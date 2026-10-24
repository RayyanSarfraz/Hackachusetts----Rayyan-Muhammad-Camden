import { describe, it, expect } from 'vitest'
import { assessTrials } from '../assessor'
import { parseNotes } from '../noteParser'
import { SAMPLE_NOTES } from './fixtures'
import { DEMO_TRIALS } from '../../data/trials'
import type { PatientProfile, Trial } from '../../types/domain'

function withBiomarkers(
  profile: PatientProfile,
  value: string[] | null,
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
    const summaries = assessTrials(DEMO_TRIALS, withBiomarkers(base, ['EGFR positive']))
    expect(statusOf(summaries, 'DEMO-A', 'A-biomarker')).toBe('supported')
    expect(statusOf(summaries, 'DEMO-B', 'B-biomarker')).toBe('potential_conflict')
    expect(statusOf(summaries, 'DEMO-C', 'C-biomarker')).toBe('supported')
    // Study D has no biomarker criterion — unaffected.
    const d = summaries.find((x) => x.trialId === 'DEMO-D')!
    expect(d.assessments.some((a) => a.factUsed === 'biomarkers')).toBe(false)
  })

  it('EGFR negative updates correctly', () => {
    const base = parseNotes(SAMPLE_NOTES)
    const summaries = assessTrials(DEMO_TRIALS, withBiomarkers(base, ['EGFR negative']))
    expect(statusOf(summaries, 'DEMO-A', 'A-biomarker')).toBe('potential_conflict')
    expect(statusOf(summaries, 'DEMO-B', 'B-biomarker')).toBe('supported')
    expect(statusOf(summaries, 'DEMO-C', 'C-biomarker')).toBe('potential_conflict')
  })

  it('biomarker unknown keeps A, B, C biomarker criteria Unknown', () => {
    const base = parseNotes(SAMPLE_NOTES)
    const summaries = assessTrials(DEMO_TRIALS, withBiomarkers(base, null))
    expect(statusOf(summaries, 'DEMO-A', 'A-biomarker')).toBe('unknown')
    expect(statusOf(summaries, 'DEMO-B', 'B-biomarker')).toBe('unknown')
    expect(statusOf(summaries, 'DEMO-C', 'C-biomarker')).toBe('unknown')
  })

  it('Study D is unaffected by biomarker answers', () => {
    const base = parseNotes(SAMPLE_NOTES)
    const pos = assessTrials(DEMO_TRIALS, withBiomarkers(base, ['EGFR positive'])).find(
      (s) => s.trialId === 'DEMO-D',
    )!
    const neg = assessTrials(DEMO_TRIALS, withBiomarkers(base, ['EGFR negative'])).find(
      (s) => s.trialId === 'DEMO-D',
    )!
    expect(pos.assessments).toEqual(neg.assessments)
  })

  it('a non-EGFR marker does not satisfy an EGFR requirement (stays Unknown)', () => {
    const base = parseNotes(SAMPLE_NOTES)
    // Patient has only KRAS documented; EGFR-positive criteria can't be judged.
    const summaries = assessTrials(DEMO_TRIALS, withBiomarkers(base, ['KRAS positive']))
    expect(statusOf(summaries, 'DEMO-A', 'A-biomarker')).toBe('unknown')
    expect(statusOf(summaries, 'DEMO-C', 'C-biomarker')).toBe('unknown')
  })

  it('EGFR match is picked out of a multi-marker list', () => {
    const base = parseNotes(SAMPLE_NOTES)
    const summaries = assessTrials(
      DEMO_TRIALS,
      withBiomarkers(base, ['KRAS positive', 'EGFR positive']),
    )
    expect(statusOf(summaries, 'DEMO-A', 'A-biomarker')).toBe('supported')
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

  it('a known fact the criterion rule cannot judge stays Unknown, not a conflict', () => {
    const base = parseNotes(SAMPLE_NOTES)
    const profile = withBiomarkers(base, ['EGFR positive'])
    // A biomarker criterion that names a marker the rule has no branch for.
    const trial: Trial = {
      id: 'T-UNJUDGED',
      name: 'Unjudged marker trial',
      location: 'Boston, MA',
      distance: { miles: 1, label: 'mock' },
      sourceLabel: 'Study criterion',
      criteria: [
        {
          id: 'u-biomarker',
          text: 'Requires BRAF V600E mutation.',
          category: 'inclusion',
          dependsOn: ['biomarkers'],
          estimatedEffort: 2,
          kind: 'biomarker',
        },
        {
          id: 'u-stage',
          text: 'Requires Stage II disease.',
          category: 'inclusion',
          dependsOn: ['diseaseStage'],
          estimatedEffort: 2,
          kind: 'stage',
        },
      ],
    }
    const stageKnown: PatientProfile = {
      ...profile,
      facts: {
        ...profile.facts,
        diseaseStage: {
          ...profile.facts.diseaseStage,
          value: 'Stage IV',
          known: true,
          source: 'answered',
        },
      },
    }
    const [summary] = assessTrials([trial], stageKnown)
    // Biomarker rule only understands EGFR; BRAF criterion is unjudgeable.
    expect(summary.assessments.find((a) => a.criterionId === 'u-biomarker')!.status).toBe(
      'unknown',
    )
    // Stage rule only understands III/IV; a "Stage II" criterion is unjudgeable.
    expect(summary.assessments.find((a) => a.criterionId === 'u-stage')!.status).toBe(
      'unknown',
    )
  })
})
