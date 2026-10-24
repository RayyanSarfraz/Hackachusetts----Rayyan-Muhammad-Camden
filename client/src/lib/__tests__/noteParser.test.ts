import { describe, it, expect } from 'vitest'
import { parseNotes } from '../noteParser'
import { DEMO_PATIENT_NOTES } from '../../data/demoPatient'

describe('noteParser', () => {
  it('loads the demo patient correctly: documented facts are extracted', () => {
    const profile = parseNotes(DEMO_PATIENT_NOTES)
    expect(profile.facts.age.value).toBe(54)
    expect(profile.facts.age.known).toBe(true)
    expect(profile.facts.condition.value).toBe('Non-small cell lung cancer')
    expect(profile.facts.location.value).toBe('Boston, MA')
    expect(profile.facts.previousTreatment.value).toBe('Chemotherapy')
  })

  it('does not invent missing facts — EGFR, stage, ECOG stay Unknown', () => {
    const profile = parseNotes(DEMO_PATIENT_NOTES)
    expect(profile.facts.egfrStatus.known).toBe(false)
    expect(profile.facts.egfrStatus.value).toBeNull()
    expect(profile.facts.cancerStage.known).toBe(false)
    expect(profile.facts.cancerStage.value).toBeNull()
    expect(profile.facts.ecogStatus.known).toBe(false)
    expect(profile.facts.ecogStatus.value).toBeNull()
  })

  it('leaves everything Unknown for empty notes', () => {
    const profile = parseNotes('')
    for (const key of Object.keys(profile.facts) as (keyof typeof profile.facts)[]) {
      expect(profile.facts[key].known).toBe(false)
      expect(profile.facts[key].value).toBeNull()
    }
  })

  it('extracts an explicit EGFR positive result when stated', () => {
    const profile = parseNotes('NSCLC. EGFR mutation detected (positive).')
    expect(profile.facts.egfrStatus.value).toBe('positive')
  })

  it('treats "EGFR not documented" as Unknown, not negative', () => {
    const profile = parseNotes('NSCLC. EGFR testing not documented.')
    expect(profile.facts.egfrStatus.known).toBe(false)
    expect(profile.facts.egfrStatus.value).toBeNull()
  })
})
