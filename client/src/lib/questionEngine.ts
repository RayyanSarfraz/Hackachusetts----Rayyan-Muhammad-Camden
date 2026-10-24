import type {
  FactKey,
  MissingInformationQuestion,
  PatientProfile,
  QuestionOption,
  Trial,
} from '../types/domain'
import { assessTrials } from './assessor'

/**
 * Next Best Question engine.
 *
 * A separate, reusable, testable module that decides which single
 * missing-information question is most useful to ask next.
 *
 * Algorithm (deterministic):
 *  1. Assess every candidate trial with the current profile.
 *  2. Find every criterion currently assessed 'unknown'.
 *  3. Group those criteria by the patient fact they depend on.
 *  4. For each missing fact, build one candidate question and count how many
 *     unresolved criterion assessments it could clarify (across all trials).
 *  5. Score each candidate:  priority = affectedAssessments / (1 + effort)
 *  6. Rank, skip facts the user has already reviewed-as-Unknown, and pick the
 *     highest-priority remaining candidate.
 *
 * None of the counts are hard-coded — they are computed from the live data.
 */

/** Static question text + options per fact. Questions request EXISTING info. */
const QUESTION_TEMPLATES: Partial<
  Record<FactKey, { text: string; options: QuestionOption[] }>
> = {
  biomarkers: {
    text: 'Do your pathology or molecular reports document an EGFR result?',
    options: [
      { id: 'egfr-pos', label: 'EGFR positive', value: 'EGFR positive', isUnknown: false },
      { id: 'egfr-neg', label: 'EGFR negative', value: 'EGFR negative', isUnknown: false },
      { id: 'egfr-unk', label: 'Unknown / not documented', value: null, isUnknown: true },
    ],
  },
  diseaseStage: {
    text: 'Do your records document a disease stage?',
    options: [
      { id: 'stage-1', label: 'Stage I', value: 'Stage I', isUnknown: false },
      { id: 'stage-2', label: 'Stage II', value: 'Stage II', isUnknown: false },
      { id: 'stage-3', label: 'Stage III', value: 'Stage III', isUnknown: false },
      { id: 'stage-4', label: 'Stage IV', value: 'Stage IV', isUnknown: false },
      { id: 'stage-unk', label: 'Unknown / not documented', value: null, isUnknown: true },
    ],
  },
  performanceStatus: {
    text: 'Do your clinical notes document an ECOG performance status?',
    options: [
      { id: 'ecog-0', label: 'ECOG 0', value: 0, isUnknown: false },
      { id: 'ecog-1', label: 'ECOG 1', value: 1, isUnknown: false },
      { id: 'ecog-2', label: 'ECOG 2', value: 2, isUnknown: false },
      { id: 'ecog-3', label: 'ECOG 3', value: 3, isUnknown: false },
      { id: 'ecog-4', label: 'ECOG 4', value: 4, isUnknown: false },
      { id: 'ecog-unk', label: 'Unknown / not documented', value: null, isUnknown: true },
    ],
  },
  age: {
    text: 'Do your records document your age?',
    options: [{ id: 'age-unk', label: 'Unknown / not documented', value: null, isUnknown: true }],
  },
  sex: {
    text: 'Do your records document your sex?',
    options: [
      { id: 'sex-m', label: 'Male', value: 'male', isUnknown: false },
      { id: 'sex-f', label: 'Female', value: 'female', isUnknown: false },
      { id: 'sex-unk', label: 'Unknown / not documented', value: null, isUnknown: true },
    ],
  },
  primaryCondition: {
    text: 'Do your records document your primary diagnosis?',
    options: [{ id: 'cond-unk', label: 'Unknown / not documented', value: null, isUnknown: true }],
  },
  location: {
    text: 'Do your records document your location?',
    options: [{ id: 'loc-unk', label: 'Unknown / not documented', value: null, isUnknown: true }],
  },
  medications: {
    text: 'Do your records document your current medications?',
    options: [{ id: 'med-unk', label: 'Unknown / not documented', value: null, isUnknown: true }],
  },
  allergies: {
    text: 'Do your records document any allergies?',
    options: [{ id: 'alg-unk', label: 'Unknown / not documented', value: null, isUnknown: true }],
  },
  priorTreatments: {
    text: 'Do your records document prior treatments?',
    options: [{ id: 'trt-unk', label: 'Unknown / not documented', value: null, isUnknown: true }],
  },
}

function factLabel(key: FactKey): string {
  const map: Record<FactKey, string> = {
    age: 'age',
    sex: 'sex',
    primaryCondition: 'diagnosis',
    location: 'location',
    medications: 'current medications',
    allergies: 'allergies',
    priorTreatments: 'prior treatments',
    biomarkers: 'biomarker status',
    diseaseStage: 'disease stage',
    performanceStatus: 'ECOG performance status',
  }
  return map[key]
}

interface FactGroup {
  factKey: FactKey
  affectedAssessments: number
  affectedTrials: Set<string>
  totalEffort: number
}

/** Stable ordering used only to break exact ties deterministically. */
const TIE_BREAK_ORDER: FactKey[] = [
  'biomarkers',
  'diseaseStage',
  'performanceStatus',
  'age',
  'sex',
  'primaryCondition',
  'location',
  'medications',
  'allergies',
  'priorTreatments',
]

export interface BuildQuestionsResult {
  /** All candidate questions, ranked highest priority first. */
  candidates: MissingInformationQuestion[]
  /** The single best question to ask next, or null when none remain. */
  next: MissingInformationQuestion | null
}

/**
 * Build the ranked list of candidate questions and select the next best one.
 *
 * @param trials       candidate trials to consider
 * @param profile      current patient profile
 * @param reviewedKeys fact keys the user already reviewed-as-Unknown; these are
 *                     excluded from `next` so the same question is not asked
 *                     repeatedly, but their criteria stay Unknown.
 */
export function buildQuestions(
  trials: Trial[],
  profile: PatientProfile,
  reviewedKeys: Set<FactKey> = new Set(),
): BuildQuestionsResult {
  const summaries = assessTrials(trials, profile)

  // Group unknown criteria by the fact they depend on.
  const groups = new Map<FactKey, FactGroup>()

  for (const trial of trials) {
    const summary = summaries.find((s) => s.trialId === trial.id)
    if (!summary) continue
    for (const criterion of trial.criteria) {
      const assessment = summary.assessments.find((a) => a.criterionId === criterion.id)
      if (!assessment || assessment.status !== 'unknown') continue
      const factKey = criterion.dependsOn[0]
      if (!factKey) continue
      const existing = groups.get(factKey)
      if (existing) {
        existing.affectedAssessments += 1
        existing.affectedTrials.add(trial.id)
        existing.totalEffort += criterion.estimatedEffort
      } else {
        groups.set(factKey, {
          factKey,
          affectedAssessments: 1,
          affectedTrials: new Set([trial.id]),
          totalEffort: criterion.estimatedEffort,
        })
      }
    }
  }

  const candidates: MissingInformationQuestion[] = []

  for (const group of groups.values()) {
    const template = QUESTION_TEMPLATES[group.factKey]
    if (!template) continue

    // Average the effort across affected criteria to keep the heuristic stable.
    const avgEffort = group.totalEffort / group.affectedAssessments
    const priority = group.affectedAssessments / (1 + avgEffort)
    const affectedTrials = group.affectedTrials.size

    candidates.push({
      factKey: group.factKey,
      text: template.text,
      options: template.options,
      affectedAssessments: group.affectedAssessments,
      affectedTrials,
      estimatedEffort: Number(avgEffort.toFixed(2)),
      priority: Number(priority.toFixed(4)),
      rationale: buildRationale(group.factKey, group.affectedAssessments, affectedTrials),
    })
  }

  // Rank: priority desc, then more affected assessments, then lower effort,
  // then the stable tie-break order.
  candidates.sort((a, b) => {
    if (b.priority !== a.priority) return b.priority - a.priority
    if (b.affectedAssessments !== a.affectedAssessments)
      return b.affectedAssessments - a.affectedAssessments
    if (a.estimatedEffort !== b.estimatedEffort)
      return a.estimatedEffort - b.estimatedEffort
    return TIE_BREAK_ORDER.indexOf(a.factKey) - TIE_BREAK_ORDER.indexOf(b.factKey)
  })

  // The next best question is the highest-ranked one the user has not already
  // reviewed-as-Unknown.
  const next = candidates.find((c) => !reviewedKeys.has(c.factKey)) ?? null

  return { candidates, next }
}

function buildRationale(
  factKey: FactKey,
  affectedAssessments: number,
  affectedTrials: number,
): string {
  const label = factLabel(factKey)
  const trialWord = affectedTrials === 1 ? 'trial' : 'trials'
  const assessmentWord =
    affectedAssessments === 1 ? 'criterion assessment' : 'criterion assessments'
  return (
    `${affectedTrials} candidate ${trialWord} contain requirements that depend on ${label}. ` +
    `Clarifying an existing ${label} result could help resolve ${affectedAssessments} currently ` +
    `unknown ${assessmentWord}. This question requests information that may already be in the record; ` +
    `it does not recommend any new test.`
  )
}
