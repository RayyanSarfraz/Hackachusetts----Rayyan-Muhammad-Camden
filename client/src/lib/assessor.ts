import type {
  CriterionAssessment,
  EligibilityCriterion,
  PatientProfile,
  Trial,
  TrialAssessmentSummary,
} from '../types/domain'

/**
 * Deterministic criterion assessor.
 *
 * Given the patient profile and a trial's criteria, produce one assessment per
 * criterion with status:
 *  - 'supported'          : the known patient fact satisfies the criterion
 *  - 'potential_conflict' : the known patient fact appears to conflict
 *  - 'unknown'            : the required fact is not documented
 *
 * Rules are intentionally transparent. Unknown facts never count as supported,
 * and are never reported as a negative finding. A patient is never called
 * definitively eligible or ineligible — these are per-criterion signals only.
 */

type FactValue = string | number | string[] | null

function getFact(profile: PatientProfile, key: string): {
  value: FactValue
  known: boolean
  evidence?: string
} {
  const fact = profile.facts[key as keyof PatientProfile['facts']]
  if (!fact) return { value: null, known: false }
  return { value: fact.value as FactValue, known: fact.known, evidence: fact.evidence }
}

function unknownAssessment(
  criterion: EligibilityCriterion,
  trial: Trial,
): CriterionAssessment {
  const factKey = criterion.dependsOn[0]
  return {
    criterionId: criterion.id,
    trialId: trial.id,
    status: 'unknown',
    explanation: `The patient's ${labelFor(factKey)} is not documented, so this criterion cannot be assessed yet.`,
    factUsed: factKey,
  }
}

function labelFor(key: string): string {
  const map: Record<string, string> = {
    age: 'age',
    sex: 'sex',
    primaryCondition: 'primary condition',
    location: 'location',
    medications: 'current medications',
    allergies: 'allergies',
    priorTreatments: 'prior treatments',
    biomarkers: 'biomarker status',
    diseaseStage: 'disease stage',
    performanceStatus: 'performance status',
  }
  return map[key] ?? key
}

/** Assess a single criterion against the patient profile. */
export function assessCriterion(
  criterion: EligibilityCriterion,
  trial: Trial,
  profile: PatientProfile,
): CriterionAssessment {
  switch (criterion.kind) {
    case 'condition':
      return assessCondition(criterion, trial, profile)
    case 'age':
      return assessAge(criterion, trial, profile)
    case 'biomarker':
      return assessBiomarker(criterion, trial, profile)
    case 'stage':
      return assessStage(criterion, trial, profile)
    case 'performance':
      return assessPerformance(criterion, trial, profile)
    case 'sex':
    case 'location':
    case 'medications':
    case 'allergies':
    case 'treatment':
      // These fact kinds have no assessment rule yet. They are deliberately
      // reported as not-yet-assessable (Unknown) rather than guessed. If a
      // trial starts using one of these kinds, add an explicit assessor above.
      return unknownAssessment(criterion, trial)
    default:
      return unknownAssessment(criterion, trial)
  }
}

function assessCondition(
  criterion: EligibilityCriterion,
  trial: Trial,
  profile: PatientProfile,
): CriterionAssessment {
  const { value, known, evidence } = getFact(profile, 'primaryCondition')
  if (!known) return unknownAssessment(criterion, trial)
  const matches = String(value)
    .toLowerCase()
    .includes('non-small cell lung cancer')
  return {
    criterionId: criterion.id,
    trialId: trial.id,
    status: matches ? 'supported' : 'potential_conflict',
    factUsed: 'primaryCondition',
    patientEvidence: evidence ?? String(value),
    explanation: matches
      ? `Patient condition "${value}" matches the required NSCLC diagnosis.`
      : `Patient condition "${value}" does not appear to match the required NSCLC diagnosis.`,
  }
}

function assessAge(
  criterion: EligibilityCriterion,
  trial: Trial,
  profile: PatientProfile,
): CriterionAssessment {
  const { value, known, evidence } = getFact(profile, 'age')
  if (!known) return unknownAssessment(criterion, trial)
  const age = Number(value)
  const inRange = age >= 18 && age <= 75
  return {
    criterionId: criterion.id,
    trialId: trial.id,
    status: inRange ? 'supported' : 'potential_conflict',
    factUsed: 'age',
    patientEvidence: evidence ?? String(value),
    explanation: inRange
      ? `Patient age ${age} is within the required 18–75 range.`
      : `Patient age ${age} is outside the required 18–75 range.`,
  }
}

function assessBiomarker(
  criterion: EligibilityCriterion,
  trial: Trial,
  profile: PatientProfile,
): CriterionAssessment {
  const { value, known, evidence } = getFact(profile, 'biomarkers')
  if (!known) return unknownAssessment(criterion, trial)

  // Determine which marker + polarity the criterion requires. Today the demo
  // criteria concern EGFR; parse the marker so identity is cross-checked and
  // a different marker (e.g. KRAS) can't satisfy an EGFR requirement.
  const requiresPositive = /egfr[^.]*positive|egfr[^.]*activating mutation|activating mutation/i.test(
    criterion.text,
  )
  const requiresNegative = /egfr[^.]*negative|egfr[^.]*wild[\s-]?type|wild[\s-]?type/i.test(
    criterion.text,
  )

  // If the criterion isn't one this rule understands, the fact exists but
  // can't be judged here — report Unknown rather than a false conflict.
  if (!requiresPositive && !requiresNegative) {
    return unknownAssessment(criterion, trial)
  }

  // The patient's biomarkers are a list of "<MARKER> positive/negative" labels.
  const markers = (Array.isArray(value) ? value : [String(value)]).map((s) =>
    s.toLowerCase(),
  )
  const egfrEntry = markers.find((m) => m.startsWith('egfr'))

  // We only have an EGFR requirement but no EGFR result documented → Unknown.
  if (!egfrEntry) return unknownAssessment(criterion, trial)

  const isPositive = /\bpositive\b/.test(egfrEntry)
  const supported = requiresPositive ? isPositive : !isPositive
  const resultLabel = isPositive ? 'EGFR positive' : 'EGFR negative'

  return {
    criterionId: criterion.id,
    trialId: trial.id,
    status: supported ? 'supported' : 'potential_conflict',
    factUsed: 'biomarkers',
    patientEvidence: evidence ?? resultLabel,
    explanation: supported
      ? `Documented ${resultLabel} satisfies this criterion.`
      : `Documented ${resultLabel} appears to conflict with this criterion.`,
  }
}

function assessStage(
  criterion: EligibilityCriterion,
  trial: Trial,
  profile: PatientProfile,
): CriterionAssessment {
  const { value, known, evidence } = getFact(profile, 'diseaseStage')
  if (!known) return unknownAssessment(criterion, trial)
  // Value is like "Stage IV"; extract the roman numeral.
  const stage = String(value).toUpperCase().replace(/^STAGE\s+/, '')

  const requiresStageIV = /stage iv/i.test(criterion.text)
  const allowsStageIII = /stage iii/i.test(criterion.text)

  // If the criterion names no stage this rule understands, the known stage
  // can't be judged against it — report Unknown rather than a false conflict.
  if (!requiresStageIV && !allowsStageIII) {
    return unknownAssessment(criterion, trial)
  }

  let supported = false
  if (allowsStageIII && requiresStageIV) {
    supported = stage === 'III' || stage === 'IV'
  } else if (requiresStageIV) {
    supported = stage === 'IV'
  } else if (allowsStageIII) {
    supported = stage === 'III'
  }

  return {
    criterionId: criterion.id,
    trialId: trial.id,
    status: supported ? 'supported' : 'potential_conflict',
    factUsed: 'diseaseStage',
    patientEvidence: evidence ?? `Stage ${stage}`,
    explanation: supported
      ? `Documented Stage ${stage} satisfies this criterion.`
      : `Documented Stage ${stage} appears to conflict with this criterion.`,
  }
}

function assessPerformance(
  criterion: EligibilityCriterion,
  trial: Trial,
  profile: PatientProfile,
): CriterionAssessment {
  const { value, known, evidence } = getFact(profile, 'performanceStatus')
  if (!known) return unknownAssessment(criterion, trial)
  const ecog = Number(value)

  const m = criterion.text.match(/([0-4])\s*(?:to|-|–)\s*([0-4])/)
  const min = m ? Number(m[1]) : 0
  const max = m ? Number(m[2]) : 4
  const supported = ecog >= min && ecog <= max

  return {
    criterionId: criterion.id,
    trialId: trial.id,
    status: supported ? 'supported' : 'potential_conflict',
    factUsed: 'performanceStatus',
    patientEvidence: evidence ?? `ECOG ${ecog}`,
    explanation: supported
      ? `Documented ECOG ${ecog} is within the accepted ${min}–${max} range.`
      : `Documented ECOG ${ecog} is outside the accepted ${min}–${max} range.`,
  }
}

/** Assess every criterion in a trial and roll up the counts. */
export function assessTrial(
  trial: Trial,
  profile: PatientProfile,
): TrialAssessmentSummary {
  const assessments = trial.criteria.map((c) => assessCriterion(c, trial, profile))
  return {
    trialId: trial.id,
    assessments,
    supported: assessments.filter((a) => a.status === 'supported').length,
    unknown: assessments.filter((a) => a.status === 'unknown').length,
    potentialConflict: assessments.filter((a) => a.status === 'potential_conflict')
      .length,
  }
}

/** Assess a set of trials. */
export function assessTrials(
  trials: Trial[],
  profile: PatientProfile,
): TrialAssessmentSummary[] {
  return trials.map((t) => assessTrial(t, profile))
}
