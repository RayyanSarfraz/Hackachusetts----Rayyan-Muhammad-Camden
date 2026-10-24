import { describe, it, expect } from 'vitest'
import { rankTrials } from '../ranking'
import { assessTrials } from '../assessor'
import { parseNotes } from '../noteParser'
import { SAMPLE_NOTES } from './fixtures'
import { DEMO_TRIALS, TRAVEL_PREFERENCES } from '../../data/trials'
import type { PatientProfile } from '../../types/domain'

const nearby = TRAVEL_PREFERENCES.find((t) => t.id === 'nearby')!
const any = TRAVEL_PREFERENCES.find((t) => t.id === 'any')!

describe('ranking', () => {
  it('changing travel preference changes ordering', () => {
    // EGFR negative makes near Study B (6mi) supported while far Study C (48mi,
    // EGFR+) becomes a conflict, so travel preference reshuffles the order.
    const base = parseNotes(SAMPLE_NOTES)
    const profile: PatientProfile = {
      ...base,
      facts: {
        ...base.facts,
        biomarkers: { ...base.facts.biomarkers, value: ['EGFR positive'], known: true, source: 'answered' },
      },
    }
    const rankedAny = rankTrials(DEMO_TRIALS, profile, { travel: any })
    const rankedNearby = rankTrials(DEMO_TRIALS, profile, { travel: nearby })
    const anyOrder = rankedAny.map((r) => r.trial.id).join(',')
    const nearbyOrder = rankedNearby.map((r) => r.trial.id).join(',')
    // Under "any", far high-scoring Study C can outrank near trials; under
    // "nearby" the within-preference trials are pulled to the front.
    expect(anyOrder).not.toBe(nearbyOrder)
    // Clinically relevant far trials are never dropped.
    expect(rankedNearby).toHaveLength(4)
    // The top trial under "nearby" must be within the preference.
    expect(rankedNearby[0].withinTravelPreference).toBe(true)
  })

  it('does not change clinical assessments when travel changes', () => {
    const profile = parseNotes(SAMPLE_NOTES)
    const clinicalAny = assessTrials(DEMO_TRIALS, profile)
    const rankedNearby = rankTrials(DEMO_TRIALS, profile, { travel: nearby })
    for (const r of rankedNearby) {
      const baseline = clinicalAny.find((s) => s.trialId === r.trial.id)!
      expect(r.summary.supported).toBe(baseline.supported)
      expect(r.summary.potentialConflict).toBe(baseline.potentialConflict)
      expect(r.summary.unknown).toBe(baseline.unknown)
    }
  })

  it('keeps clinically relevant trials even when outside travel preference', () => {
    const profile = parseNotes(SAMPLE_NOTES)
    const ranked = rankTrials(DEMO_TRIALS, profile, { travel: nearby })
    // All four trials are still present, none silently removed.
    expect(ranked).toHaveLength(4)
    const outside = ranked.filter((r) => !r.withinTravelPreference)
    expect(outside.length).toBeGreaterThan(0)
  })

  it('Unknown criteria never count as supported in the score', () => {
    const profile = parseNotes(SAMPLE_NOTES)
    const ranked = rankTrials(DEMO_TRIALS, profile, { travel: any })
    const a = ranked.find((r) => r.trial.id === 'DEMO-A')!
    // 2 supported * 2 - 0 conflicts * 3 = 4 ; unknowns contribute nothing.
    expect(a.clinicalScore).toBe(4)
  })
})
