import type {
  AssessmentChange,
  PatientProfile,
  Trial,
} from '../types/domain'
import { assessTrials } from './assessor'

/**
 * Compute the before/after criterion assessment changes between two patient
 * profiles over the same set of trials. Used to show the "Before vs After"
 * section after the user answers a question or revises an answer.
 *
 * Only criteria whose status actually changed are returned.
 */
export function diffAssessments(
  trials: Trial[],
  before: PatientProfile,
  after: PatientProfile,
): AssessmentChange[] {
  const beforeSummaries = assessTrials(trials, before)
  const afterSummaries = assessTrials(trials, after)
  const changes: AssessmentChange[] = []

  for (const trial of trials) {
    const b = beforeSummaries.find((s) => s.trialId === trial.id)
    const a = afterSummaries.find((s) => s.trialId === trial.id)
    if (!b || !a) continue
    for (const criterion of trial.criteria) {
      const ba = b.assessments.find((x) => x.criterionId === criterion.id)
      const aa = a.assessments.find((x) => x.criterionId === criterion.id)
      if (!ba || !aa) continue
      if (ba.status !== aa.status) {
        changes.push({
          trialId: trial.id,
          trialName: trial.name,
          criterionId: criterion.id,
          criterionText: criterion.text,
          before: ba.status,
          after: aa.status,
          reason: aa.explanation,
        })
      }
    }
  }

  return changes
}
