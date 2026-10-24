import type {
  CriterionAssessment,
  EligibilityCriterion,
  FactKey,
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

type FactValue = string | number | null

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

/** Build an assessment from a structured rule check (met -> supported). */
function ruleResult(
  criterion: EligibilityCriterion,
  trial: Trial,
  factUsed: FactKey,
  met: boolean,
  evidence: string,
  what: string,
): CriterionAssessment {
  return {
    criterionId: criterion.id,
    trialId: trial.id,
    factUsed,
    status: met ? 'supported' : 'potential_conflict',
    patientEvidence: evidence,
    explanation: met
      ? `${what} satisfies this criterion.`
      : `${what} appears to conflict with this criterion.`,
  }
}

function labelFor(key: string): string {
  const map: Record<string, string> = {
    age: 'age',
    condition: 'condition',
    location: 'location',
    previousTreatment: 'previous treatment',
    egfrStatus: 'EGFR status',
    cancerStage: 'cancer stage',
    ecogStatus: 'ECOG performance status',
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
    case 'egfr':
      return assessEgfr(criterion, trial, profile)
    case 'stage':
      return assessStage(criterion, trial, profile)
    case 'ecog':
      return assessEcog(criterion, trial, profile)
    default:
      return unknownAssessment(criterion, trial)
  }
}

function assessCondition(
  criterion: EligibilityCriterion,
  trial: Trial,
  profile: PatientProfile,
): CriterionAssessment {
  const { value, known, evidence } = getFact(profile, 'condition')
  if (!known) return unknownAssessment(criterion, trial)
  const matches = String(value).toLowerCase().includes('non-small cell lung cancer')
  return {
    criterionId: criterion.id,
    trialId: trial.id,
    status: matches ? 'supported' : 'potential_conflict',
    factUsed: 'condition',
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
  const rule = criterion.rule
  if (rule && ('minAge' in rule || 'maxAge' in rule)) {
    const { minAge = -Infinity, maxAge = Infinity } = rule
    const ruleAge = Number(value)
    return ruleResult(
      criterion,
      trial,
      'age',
      ruleAge >= minAge && ruleAge <= maxAge,
      evidence ?? String(value),
      `Patient age ${ruleAge}`,
    )
  }
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

function assessEgfr(
  criterion: EligibilityCriterion,
  trial: Trial,
  profile: PatientProfile,
): CriterionAssessment {
  const { value, known, evidence } = getFact(profile, 'egfrStatus')
  if (!known) return unknownAssessment(criterion, trial)
  const rule = criterion.rule
  if (rule && 'egfr' in rule) {
    return ruleResult(
      criterion,
      trial,
      'egfrStatus',
      String(value) === rule.egfr,
      evidence ?? `EGFR ${String(value)}`,
      `Documented EGFR ${String(value)} result`,
    )
  }

  const requiresPositive = /egfr positive|activating mutation/i.test(criterion.text)
  const requiresNegative = /egfr negative|wild[\s-]?type/i.test(criterion.text)
  const status = String(value) // 'positive' | 'negative'

  let supported = false
  if (requiresPositive) supported = status === 'positive'
  else if (requiresNegative) supported = status === 'negative'

  return {
    criterionId: criterion.id,
    trialId: trial.id,
    status: supported ? 'supported' : 'potential_conflict',
    factUsed: 'egfrStatus',
    patientEvidence: evidence ?? `EGFR ${status}`,
    explanation: supported
      ? `Documented EGFR ${status} result satisfies this criterion.`
      : `Documented EGFR ${status} result appears to conflict with this criterion.`,
  }
}

function assessStage(
  criterion: EligibilityCriterion,
  trial: Trial,
  profile: PatientProfile,
): CriterionAssessment {
  const { value, known, evidence } = getFact(profile, 'cancerStage')
  if (!known) return unknownAssessment(criterion, trial)
  const rule = criterion.rule
  if (rule && 'stages' in rule) {
    const ruleStage = String(value).toUpperCase()
    return ruleResult(
      criterion,
      trial,
      'cancerStage',
      rule.stages.includes(ruleStage),
      evidence ?? `Stage ${ruleStage}`,
      `Documented Stage ${ruleStage}`,
    )
  }
  const stage = String(value).toUpperCase()

  // Extract accepted stages from the criterion text.
  const requiresStageIV = /stage iv/i.test(criterion.text)
  const allowsStageIII = /stage iii/i.test(criterion.text)

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
    factUsed: 'cancerStage',
    patientEvidence: evidence ?? `Stage ${stage}`,
    explanation: supported
      ? `Documented Stage ${stage} satisfies this criterion.`
      : `Documented Stage ${stage} appears to conflict with this criterion.`,
  }
}

function assessEcog(
  criterion: EligibilityCriterion,
  trial: Trial,
  profile: PatientProfile,
): CriterionAssessment {
  const { value, known, evidence } = getFact(profile, 'ecogStatus')
  if (!known) return unknownAssessment(criterion, trial)
  const rule = criterion.rule
  if (rule && 'ecogMax' in rule) {
    const ruleEcog = Number(value)
    return ruleResult(
      criterion,
      trial,
      'ecogStatus',
      ruleEcog <= rule.ecogMax,
      evidence ?? `ECOG ${ruleEcog}`,
      `Documented ECOG ${ruleEcog}`,
    )
  }
  const ecog = Number(value)

  // Parse the accepted ECOG range, e.g. "0 to 1" or "0 to 2".
  const m = criterion.text.match(/([0-4])\s*(?:to|-|–)\s*([0-4])/)
  const min = m ? Number(m[1]) : 0
  const max = m ? Number(m[2]) : 4
  const supported = ecog >= min && ecog <= max

  return {
    criterionId: criterion.id,
    trialId: trial.id,
    status: supported ? 'supported' : 'potential_conflict',
    factUsed: 'ecogStatus',
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
