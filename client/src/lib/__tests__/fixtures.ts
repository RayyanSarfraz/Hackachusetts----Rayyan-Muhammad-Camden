/**
 * Shared test fixtures.
 *
 * SAMPLE_NOTES is a fictional clinical note used across the parser / engine /
 * store tests. It documents age, condition, location and prior treatment, and
 * deliberately leaves biomarker status, stage and performance status
 * undocumented so tests can verify those stay Unknown (never guessed).
 */
export const SAMPLE_NOTES = `Clinical note

Patient is a 54-year-old presenting for oncology follow-up.
Diagnosis: non-small cell lung cancer.
Location: Boston, MA.
Treatment history: prior chemotherapy completed.

EGFR mutation testing: not documented in the available record.
Cancer stage: not documented in the available record.
ECOG performance status: not documented in the available record.`
