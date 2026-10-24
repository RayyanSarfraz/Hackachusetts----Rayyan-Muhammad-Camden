import { describe, it, expect } from 'vitest'
import { parseNotes } from '../noteParser'
import { SAMPLE_NOTES } from './fixtures'

describe('noteParser', () => {
  it('extracts documented facts from a clinical note', () => {
    const profile = parseNotes(SAMPLE_NOTES)
    expect(profile.facts.age.value).toBe(54)
    expect(profile.facts.age.known).toBe(true)
    expect(profile.facts.primaryCondition.value).toBe('Non-small cell lung cancer')
    expect(profile.facts.location.value).toBe('Boston, MA')
    // The "Treatment history:" line is captured as a documented prior treatment.
    const treatments = profile.facts.priorTreatments.value as string[]
    expect(treatments.join(' ').toLowerCase()).toContain('chemotherapy')
  })

  it('scans for treatment keywords when there is no labeled line', () => {
    const profile = parseNotes('Patient had chemotherapy and radiation previously.')
    expect(profile.facts.priorTreatments.value).toEqual(['Chemotherapy', 'Radiation'])
  })

  it('does not invent missing facts — biomarkers, stage, performance stay Unknown', () => {
    const profile = parseNotes(SAMPLE_NOTES)
    expect(profile.facts.biomarkers.known).toBe(false)
    expect(profile.facts.biomarkers.value).toBeNull()
    expect(profile.facts.diseaseStage.known).toBe(false)
    expect(profile.facts.diseaseStage.value).toBeNull()
    expect(profile.facts.performanceStatus.known).toBe(false)
    expect(profile.facts.performanceStatus.value).toBeNull()
  })

  it('leaves everything Unknown for empty notes', () => {
    const profile = parseNotes('')
    for (const key of Object.keys(profile.facts) as (keyof typeof profile.facts)[]) {
      expect(profile.facts[key].known).toBe(false)
      expect(profile.facts[key].value).toBeNull()
    }
  })

  it('extracts an explicit EGFR positive result as a biomarker', () => {
    const profile = parseNotes('NSCLC. EGFR mutation detected (positive).')
    expect(profile.facts.biomarkers.value).toEqual(['EGFR positive'])
  })

  it('captures multiple biomarkers, not just the first', () => {
    const profile = parseNotes(
      'EGFR activating mutation detected. KRAS wild-type (negative).',
    )
    expect(profile.facts.biomarkers.value).toEqual([
      'EGFR positive',
      'KRAS negative',
    ])
  })

  it('merges medications from multiple labeled lines', () => {
    const profile = parseNotes(
      'Medication: Metformin\nMedication: Lisinopril\nMedication: Aspirin',
    )
    expect(profile.facts.medications.value).toEqual([
      'Metformin',
      'Lisinopril',
      'Aspirin',
    ])
  })

  it('treats "EGFR not documented" as Unknown, not negative', () => {
    const profile = parseNotes('NSCLC. EGFR testing not documented.')
    expect(profile.facts.biomarkers.known).toBe(false)
    expect(profile.facts.biomarkers.value).toBeNull()
  })

  it('extracts medications and allergies as lists', () => {
    const profile = parseNotes(
      'Medications: metformin, lisinopril and aspirin.\nAllergies: penicillin.',
    )
    expect(profile.facts.medications.value).toEqual([
      'Metformin',
      'Lisinopril',
      'Aspirin',
    ])
    expect(profile.facts.allergies.value).toEqual(['Penicillin'])
  })

  it('recognizes "no known drug allergies"', () => {
    const profile = parseNotes('NKDA. Diagnosis: breast cancer.')
    expect(profile.facts.allergies.value).toEqual(['No known allergies'])
    expect(profile.facts.primaryCondition.value).toBe('Breast cancer')
  })
})
