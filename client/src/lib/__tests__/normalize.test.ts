import { describe, it, expect } from 'vitest'
import { csvToText, jsonToText, xmlToText } from '../normalize'
import { parseNotes } from '../noteParser'

describe('normalize smoke', () => {
  it('CSV → text and parses lab values', () => {
    const csv = 'date,test,value,unit\n2026-01-12,eGFR,78,mL/min\n2026-01-12,EGFR mutation,positive,\n'
    const { text, meta } = csvToText(csv)
    expect(meta.rows).toBe(2)
    expect(meta.columns).toBe(4)
    expect(text).toContain('eGFR')
    // Biomarker extraction should see the EGFR positive row.
    const profile = parseNotes(text)
    expect(profile.facts.biomarkers.value).toEqual(['EGFR positive'])
  })

  it('FHIR JSON bundle → text and extracts patient facts', () => {
    const bundle = {
      resourceType: 'Bundle',
      entry: [
        { resource: { resourceType: 'Patient', gender: 'female', birthDate: '1970-05-01', address: [{ city: 'Boston', state: 'MA' }] } },
        { resource: { resourceType: 'Condition', code: { text: 'Non-small cell lung cancer' } } },
        { resource: { resourceType: 'MedicationStatement', medicationCodeableConcept: { text: 'Metformin' } } },
      ],
    }
    const { text, meta } = jsonToText(JSON.stringify(bundle))
    expect(meta.resources).toBe(3)
    expect(text).toContain('Diagnosis: Non-small cell lung cancer')
    const profile = parseNotes(text)
    expect(profile.facts.sex.value).toBe('female')
    expect(profile.facts.location.value).toBe('Boston, MA')
    expect(profile.facts.primaryCondition.value).toBe('Non-small cell lung cancer')
  })

  it('Apple Health XML → text', () => {
    const xml = `<?xml version="1.0"?>
<HealthData locale="en_US">
  <Me HKCharacteristicTypeIdentifierBiologicalSex="HKBiologicalSexFemale" HKCharacteristicTypeIdentifierDateOfBirth="1970-05-01"/>
  <Record type="HKQuantityTypeIdentifierHeartRate" unit="count/min" value="72"/>
  <Record type="HKQuantityTypeIdentifierHeartRate" unit="count/min" value="75"/>
</HealthData>`
    const { text, meta } = xmlToText(xml)
    expect(text).toContain('Apple Health export')
    expect(text).toContain('Sex: Female')
    expect(text).toContain('HeartRate: 2 records')
    expect(meta.resources).toBeGreaterThan(0)
  })

  it('invalid JSON throws a friendly error', () => {
    expect(() => jsonToText('{not json')).toThrow(/Invalid JSON/)
  })
})
