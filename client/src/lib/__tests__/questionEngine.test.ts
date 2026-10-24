import { describe, it, expect } from 'vitest'
import { buildQuestions } from '../questionEngine'
import { parseNotes } from '../noteParser'
import { DEMO_PATIENT_NOTES } from '../../data/demoPatient'
import { DEMO_TRIALS } from '../../data/trials'
import { NSCLC_TRIALS } from '../../data/nsclcTrials'
import { assessTrials } from '../assessor'
import type { FactKey, PatientProfile } from '../../types/domain'

function setFact(
  profile: PatientProfile,
  key: FactKey,
  value: string | number | null,
): PatientProfile {
  return {
    ...profile,
    facts: {
      ...profile.facts,
      [key]: {
        ...profile.facts[key],
        value,
        known: value !== null,
        source: 'answered',
      },
    },
  }
}

describe('questionEngine', () => {
  it('computes affected assessments from live data, not hard-coded', () => {
    const base = parseNotes(DEMO_PATIENT_NOTES)
    const { candidates } = buildQuestions(DEMO_TRIALS, base)
    const egfr = candidates.find((c) => c.factKey === 'egfrStatus')!
    const stage = candidates.find((c) => c.factKey === 'cancerStage')!
    const ecog = candidates.find((c) => c.factKey === 'ecogStatus')!
    // EGFR appears in A, B, C -> 3 ; Stage in A, B, D -> 3 ; ECOG in A, C, D -> 3
    expect(egfr.affectedAssessments).toBe(3)
    expect(stage.affectedAssessments).toBe(3)
    expect(ecog.affectedAssessments).toBe(3)
  })

  it('selects a question via the priority algorithm (deterministic tie-break)', () => {
    const base = parseNotes(DEMO_PATIENT_NOTES)
    const { next } = buildQuestions(DEMO_TRIALS, base)
    expect(next).not.toBeNull()
    // All three tie on priority; stable tie-break puts EGFR first here.
    expect(next!.factKey).toBe('egfrStatus')
  })

  it('priority equals affectedAssessments / (1 + effort)', () => {
    const base = parseNotes(DEMO_PATIENT_NOTES)
    const { candidates } = buildQuestions(DEMO_TRIALS, base)
    const egfr = candidates.find((c) => c.factKey === 'egfrStatus')!
    const expected = egfr.affectedAssessments / (1 + egfr.estimatedEffort)
    expect(egfr.priority).toBeCloseTo(expected, 4)
  })

  it('does not re-select a fact the user reviewed as Unknown', () => {
    const base = parseNotes(DEMO_PATIENT_NOTES)
    const reviewed = new Set<FactKey>(['egfrStatus'])
    const { next } = buildQuestions(DEMO_TRIALS, base, reviewed)
    expect(next).not.toBeNull()
    expect(next!.factKey).not.toBe('egfrStatus')
  })

  it('answering a fact removes it from future candidates (no repeat)', () => {
    let profile = parseNotes(DEMO_PATIENT_NOTES)
    profile = setFact(profile, 'egfrStatus', 'positive')
    const { candidates } = buildQuestions(DEMO_TRIALS, profile)
    expect(candidates.some((c) => c.factKey === 'egfrStatus')).toBe(false)
  })

  it('Unknown responses do not create an infinite loop — eventually none remain', () => {
    const profile = parseNotes(DEMO_PATIENT_NOTES)
    const reviewed = new Set<FactKey>()
    for (let i = 0; i < 10; i++) {
      const { next } = buildQuestions(DEMO_TRIALS, profile, reviewed)
      if (!next) break
      // Simulate the user always answering "Unknown".
      reviewed.add(next.factKey)
    }
    const { next } = buildQuestions(DEMO_TRIALS, profile, reviewed)
    expect(next).toBeNull()
  })

  it('returns no question when all relevant facts are resolved', () => {
    let profile = parseNotes(DEMO_PATIENT_NOTES)
    profile = setFact(profile, 'egfrStatus', 'positive')
    profile = setFact(profile, 'cancerStage', 'IV')
    profile = setFact(profile, 'ecogStatus', 1)
    const { next } = buildQuestions(DEMO_TRIALS, profile)
    expect(next).toBeNull()
  })
})

describe('questionEngine with NSCLC_TRIALS', () => {
  it('asks EGFR status first for the demo patient', () => {
    const { next, candidates } = buildQuestions(
      NSCLC_TRIALS,
      parseNotes(DEMO_PATIENT_NOTES),
    )
    expect(next?.factKey).toBe('egfrStatus')
    const keys = candidates.map((c) => c.factKey)
    expect(keys).toContain('cancerStage')
    expect(keys).toContain('ecogStatus')
  })

  it('answering EGFR positive supports the EGFR+ trials and conflicts the EGFR- trials', () => {
    const profile = setFact(parseNotes(DEMO_PATIENT_NOTES), 'egfrStatus', 'positive')
    const egfrStatusById = new Map(
      assessTrials(NSCLC_TRIALS, profile).map((s) => [
        s.trialId,
        s.assessments.find((a) => a.criterionId === `${s.trialId}-egfr`)?.status,
      ]),
    )
    for (const id of ['NCT04410796', 'NCT04181060', 'NCT03191149']) {
      expect(egfrStatusById.get(id)).toBe('supported')
    }
    for (const id of ['NCT07291037', 'NCT06767514', 'NCT07063745']) {
      expect(egfrStatusById.get(id)).toBe('potential_conflict')
    }
  })
})
