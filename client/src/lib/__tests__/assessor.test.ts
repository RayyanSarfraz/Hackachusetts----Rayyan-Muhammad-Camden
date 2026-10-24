import { describe, it, expect } from 'vitest'
import { assessTrials } from '../assessor'
import { parseNotes } from '../noteParser'
import { DEMO_PATIENT_NOTES } from '../../data/demoPatient'
import { DEMO_TRIALS } from '../../data/trials'
import type { PatientProfile } from '../../types/domain'

function withEgfr(
  profile: PatientProfile,
  value: 'positive' | 'negative' | null,
): PatientProfile {
  return {
    ...profile,
    facts: {
      ...profile.facts,
      egfrStatus: {
        ...profile.facts.egfrStatus,
        value,
        known: value !== null,
        source: 'answered',
      },
    },
  }
}

function statusOf(
  summaries: ReturnType<typeof assessTrials>,
  trialId: string,
  criterionId: string,
) {
  const s = summaries.find((x) => x.trialId === trialId)!
  return s.assessments.find((a) => a.criterionId === criterionId)!.status
}

describe('assessor', () => {
  it('EGFR positive updates only relevant criteria', () => {
    const base = parseNotes(DEMO_PATIENT_NOTES)
    const summaries = assessTrials(DEMO_TRIALS, withEgfr(base, 'positive'))
    expect(statusOf(summaries, 'DEMO-A', 'A-egfr')).toBe('supported')
    expect(statusOf(summaries, 'DEMO-B', 'B-egfr')).toBe('potential_conflict')
    expect(statusOf(summaries, 'DEMO-C', 'C-egfr')).toBe('supported')
    // Study D has no EGFR criterion — unaffected.
    const d = summaries.find((x) => x.trialId === 'DEMO-D')!
    expect(d.assessments.some((a) => a.factUsed === 'egfrStatus')).toBe(false)
  })

  it('EGFR negative updates correctly', () => {
    const base = parseNotes(DEMO_PATIENT_NOTES)
    const summaries = assessTrials(DEMO_TRIALS, withEgfr(base, 'negative'))
    expect(statusOf(summaries, 'DEMO-A', 'A-egfr')).toBe('potential_conflict')
    expect(statusOf(summaries, 'DEMO-B', 'B-egfr')).toBe('supported')
    expect(statusOf(summaries, 'DEMO-C', 'C-egfr')).toBe('potential_conflict')
  })

  it('EGFR unknown keeps A, B, C EGFR criteria Unknown', () => {
    const base = parseNotes(DEMO_PATIENT_NOTES)
    const summaries = assessTrials(DEMO_TRIALS, withEgfr(base, null))
    expect(statusOf(summaries, 'DEMO-A', 'A-egfr')).toBe('unknown')
    expect(statusOf(summaries, 'DEMO-B', 'B-egfr')).toBe('unknown')
    expect(statusOf(summaries, 'DEMO-C', 'C-egfr')).toBe('unknown')
  })

  it('Study D is unaffected by EGFR answers', () => {
    const base = parseNotes(DEMO_PATIENT_NOTES)
    const pos = assessTrials(DEMO_TRIALS, withEgfr(base, 'positive')).find(
      (s) => s.trialId === 'DEMO-D',
    )!
    const neg = assessTrials(DEMO_TRIALS, withEgfr(base, 'negative')).find(
      (s) => s.trialId === 'DEMO-D',
    )!
    expect(pos.assessments).toEqual(neg.assessments)
  })

  it('does not count Unknown as supported and matches demo baseline', () => {
    const base = parseNotes(DEMO_PATIENT_NOTES)
    const summaries = assessTrials(DEMO_TRIALS, base)
    const a = summaries.find((s) => s.trialId === 'DEMO-A')!
    // condition + age supported; egfr, stage, ecog unknown.
    expect(a.supported).toBe(2)
    expect(a.unknown).toBe(3)
    expect(a.potentialConflict).toBe(0)
  })
})
