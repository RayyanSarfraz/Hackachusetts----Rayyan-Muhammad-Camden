import type { FactKey } from '../types/domain'

export interface FactDefinition {
  key: FactKey
  label: string
}

/** The fact catalogue the demo understands, in display order. */
export const FACT_DEFINITIONS: FactDefinition[] = [
  { key: 'age', label: 'Age' },
  { key: 'condition', label: 'Condition' },
  { key: 'location', label: 'Location' },
  { key: 'previousTreatment', label: 'Previous treatment' },
  { key: 'egfrStatus', label: 'EGFR status' },
  { key: 'cancerStage', label: 'Cancer stage' },
  { key: 'ecogStatus', label: 'ECOG performance status' },
]

/**
 * The fictional demo patient's medical notes. Pasting / loading these produces
 * a deterministic extraction: age, condition, location, and previous treatment
 * are documented; EGFR status, cancer stage, and ECOG status are NOT documented
 * and must remain Unknown.
 */
export const DEMO_PATIENT_NOTES = `Clinical Note (FICTIONAL — DEMO DATA ONLY)

Patient is a 54-year-old presenting for oncology follow-up.
Diagnosis: non-small cell lung cancer.
Location: Boston, MA.
Treatment history: prior chemotherapy completed.

EGFR mutation testing: not documented in the available record.
Cancer stage: not documented in the available record.
ECOG performance status: not documented in the available record.`
