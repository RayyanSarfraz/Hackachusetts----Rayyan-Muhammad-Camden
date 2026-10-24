import { describe, it, expect } from 'vitest'
import { assessTrials } from '../assessor'
import { parseNotes } from '../noteParser'
import { SAMPLE_NOTES } from './fixtures'
import { DEMO_TRIALS } from '../../data/trials'
import type { PatientProfile } from '../../types/domain'

function withBiomarker(
  profile: PatientProfile,
  value: 'EGFR positive' | 'EGFR negative' | null,
): PatientProfile {
  return {
    ...profile,
    facts: {
      ...profile.facts,
      biomarkers: {
        ...profile.facts.biomarkers,
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
    const base = parseNotes(SAMPLE_NOTES)
    const summaries = assessTrials(DEMO_TRIALS, withBiomarker(base, 'EGFR positive'))
    expect(statusOf(summaries, 'DEMO-A', 'A-biomarker')).toBe('supported')
    expect(statusOf(summaries, 'DEMO-B', 'B-biomarker')).toBe('potential_conflict')
    expect(statusOf(summaries, 'DEMO-C', 'C-biomarker')).toBe('supported')
    // Study D has no biomarker criterion — unaffected.
    const d = summaries.find((x) => x.trialId === 'DEMO-D')!
    expect(d.assessments.some((a) => a.factUsed === 'biomarkers')).toBe(false)
  })

  it('EGFR negative updates correctly', () => {
    const base = parseNotes(SAMPLE_NOTES)
    const summaries = assessTrials(DEMO_TRIALS, withBiomarker(base, 'EGFR negative'))
    expect(statusOf(summaries, 'DEMO-A', 'A-biomarker')).toBe('potential_conflict')
    expect(statusOf(summaries, 'DEMO-B', 'B-biomarker')).toBe('supported')
    expect(statusOf(summaries, 'DEMO-C', 'C-biomarker')).toBe('potential_conflict')
  })

  it('biomarker unknown keeps A, B, C biomarker criteria Unknown', () => {
    const base = parseNotes(SAMPLE_NOTES)
    const summaries = assessTrials(DEMO_TRIALS, withBiomarker(base, null))
    expect(statusOf(summaries, 'DEMO-A', 'A-biomarker')).toBe('unknown')
    expect(statusOf(summaries, 'DEMO-B', 'B-biomarker')).toBe('unknown')
    expect(statusOf(summaries, 'DEMO-C', 'C-biomarker')).toBe('unknown')
  })

  it('Study D is unaffected by biomarker answers', () => {
    const base = parseNotes(SAMPLE_NOTES)
    const pos = assessTrials(DEMO_TRIALS, withBiomarker(base, 'EGFR positive')).find(
      (s) => s.trialId === 'DEMO-D',
    )!
    const neg = assessTrials(DEMO_TRIALS, withBiomarker(base, 'EGFR negative')).find(
      (s) => s.trialId === 'DEMO-D',
    )!
    expect(pos.assessments).toEqual(neg.assessments)
  })

  it('does not count Unknown as supported and matches baseline', () => {
    const base = parseNotes(SAMPLE_NOTES)
    const summaries = assessTrials(DEMO_TRIALS, base)
    const a = summaries.find((s) => s.trialId === 'DEMO-A')!
    // condition + age supported; biomarker, stage, performance unknown.
    expect(a.supported).toBe(2)
    expect(a.unknown).toBe(3)
    expect(a.potentialConflict).toBe(0)
  })
})
