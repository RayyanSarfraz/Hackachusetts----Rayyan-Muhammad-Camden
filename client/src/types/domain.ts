/**
 * TrialBridge domain types.
 *
 * These interfaces describe the data model shared across the whole demo:
 * patient facts, trials, eligibility criteria, assessments, the Next Best
 * Question engine, travel preferences, and before/after assessment changes.
 *
 * Everything here is deliberately framework-agnostic so the pure logic modules
 * (parser, assessor, ranking, question engine) can be unit tested in isolation.
 */

/** The set of patient facts the demo understands and reasons about. */
export type FactKey =
  | 'age'
  | 'condition'
  | 'location'
  | 'previousTreatment'
  | 'egfrStatus'
  | 'cancerStage'
  | 'ecogStatus'

/** A patient fact is always present as a key; its value may be Unknown. */
export interface PatientFact<T = unknown> {
  key: FactKey
  /** Human-readable label, e.g. "EGFR status". */
  label: string
  /**
   * The resolved value, or `null` when the fact is Unknown / not documented.
   * Missing information is represented as `null`, never as a negative finding.
   */
  value: T | null
  /** True when the value is known/documented. */
  known: boolean
  /**
   * Where this value came from so the UI can be honest about provenance.
   * - 'parsed'    : extracted deterministically from the pasted notes
   * - 'answered'  : supplied by the user answering a question
   * - 'confirmed' : user explicitly confirmed/edited the fact
   * - 'default'   : seeded (e.g. the demo patient) but not yet confirmed
   */
  source: 'parsed' | 'answered' | 'confirmed' | 'default'
  /** The raw supporting text snippet from the notes, if any. */
  evidence?: string
}

export interface PatientProfile {
  id: string
  /** All known fact keys mapped to their fact record. */
  facts: Record<FactKey, PatientFact>
  /** The original notes text the facts were derived from (demo only, local). */
  rawNotes: string
}

/** EGFR mutation status values the demo supports. */
export type EgfrStatus = 'positive' | 'negative'

/** How a criterion is categorized in the trial record. */
export type CriterionCategory = 'inclusion' | 'exclusion'

/**
 * Optional structured rule for a criterion. When present, the assessor uses
 * these thresholds instead of the hardcoded demo values.
 */
export type CriterionRule =
  | { minAge?: number; maxAge?: number }
  | { egfr: 'positive' | 'negative' }
  /** Allowed stages, upper-case Roman numerals, e.g. ['III', 'IV']. */
  | { stages: string[] }
  | { ecogMax: number }

/**
 * A single eligibility criterion from a (fictional) trial record.
 * `dependsOn` lists which patient facts are needed to assess it.
 */
export interface EligibilityCriterion {
  id: string
  /** Exact, verbatim criterion text from the mock trial record. */
  text: string
  category: CriterionCategory
  /** Patient facts this criterion needs in order to be assessed. */
  dependsOn: FactKey[]
  /**
   * Estimated effort for the patient to supply the missing fact(s), used by
   * the Next Best Question engine. 1 = trivial lookup, higher = more effort.
   */
  estimatedEffort: number
  /** Short label of what the question would ask, grouped by missing fact. */
  kind:
    | 'condition'
    | 'age'
    | 'egfr'
    | 'stage'
    | 'ecog'
    | 'location'
    | 'treatment'
  /** Structured thresholds for this criterion, if any. */
  rule?: CriterionRule
}

export interface TrialDistance {
  /** Explicitly labeled mock distance in miles (not computed from geo). */
  miles: number
  /** 'mock' for demo trials, 'approximate' for real trials (rough estimate). */
  label: 'mock' | 'approximate'
}

export interface Trial {
  id: string
  name: string
  /** Fictional study location, e.g. "Boston, MA". */
  location: string
  /** Labeled mock distance from the patient's location. */
  distance: TrialDistance
  criteria: EligibilityCriterion[]
  /** Source label for evidence provenance. */
  sourceLabel: 'Demo criterion' | 'ClinicalTrials.gov'
  /** ClinicalTrials.gov identifier for real trials (equals `id`). */
  nctId?: string
  /** https://clinicaltrials.gov/study/<nctId> */
  sourceUrl?: string
  /** Recruitment status from the dataset, e.g. "RECRUITING". */
  recruitmentStatus?: string
  /** Trial phase from the dataset. */
  phase?: string
}

/** The three possible assessments for an individual criterion. */
export type AssessmentStatus = 'supported' | 'unknown' | 'potential_conflict'

export interface CriterionAssessment {
  criterionId: string
  trialId: string
  status: AssessmentStatus
  /** Plain-English explanation of why this status was assigned. */
  explanation: string
  /** Which patient fact value (if any) was used to decide. */
  factUsed?: FactKey
  /** The patient evidence string that supported the assessment, if any. */
  patientEvidence?: string
}

/** Per-trial roll-up used on the card. */
export interface TrialAssessmentSummary {
  trialId: string
  supported: number
  unknown: number
  potentialConflict: number
  assessments: CriterionAssessment[]
}

/** A candidate answer option for a missing-information question. */
export interface QuestionOption {
  /** Stable id used when recording the answer. */
  id: string
  label: string
  /**
   * The resolved value this option maps to, or `null` for the
   * "Unknown / not documented" option.
   */
  value: string | number | null
  /** True for the explicit Unknown / not documented option. */
  isUnknown: boolean
}

export interface MissingInformationQuestion {
  /** The missing fact this question resolves. */
  factKey: FactKey
  text: string
  options: QuestionOption[]
  /** Number of currently-unresolved criterion assessments this could clarify. */
  affectedAssessments: number
  /** Number of distinct trials with at least one affected criterion. */
  affectedTrials: number
  /** Summed estimated effort across the affected criteria. */
  estimatedEffort: number
  /** priority = affectedAssessments / (1 + estimatedEffort). */
  priority: number
  /** Plain-English "Why are we asking this?" explanation. */
  rationale: string
}

export interface QuestionAnswer {
  factKey: FactKey
  /** The option id that was chosen. */
  optionId: string
  value: string | number | null
  isUnknown: boolean
  /** When the user answered (epoch ms) — used for ordering history. */
  answeredAt: number
}

export type TravelPreferenceId =
  | 'nearby'
  | 'within_50'
  | 'within_100'
  | 'any'

export interface TravelPreference {
  id: TravelPreferenceId
  label: string
  /** Inclusive max distance in miles, or null for "any distance". */
  maxMiles: number | null
}

/** A single before/after change to a criterion assessment. */
export interface AssessmentChange {
  trialId: string
  trialName: string
  criterionId: string
  criterionText: string
  before: AssessmentStatus
  after: AssessmentStatus
  reason: string
}

/** A fully-ranked trial entry with its summary and travel info. */
export interface RankedTrial {
  trial: Trial
  summary: TrialAssessmentSummary
  /** Transparent clinical compatibility score (not a medical probability). */
  clinicalScore: number
  /** Whether the trial is within the current travel preference. */
  withinTravelPreference: boolean
  rank: number
  /** Short plain-English explanation of this trial's ranking position. */
  rankExplanation: string
}
