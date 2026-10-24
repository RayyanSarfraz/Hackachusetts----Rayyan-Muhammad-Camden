import type { FactKey } from '../types/domain'

export interface FactDefinition {
  key: FactKey
  /** Short label shown in the UI, e.g. "Primary condition". */
  label: string
  /** One-line hint describing what belongs here. */
  hint: string
  /** How the value is edited / displayed. */
  type: 'number' | 'text' | 'list'
  /** Where the patient usually gets this from (shown as provenance help). */
  typicalSource: 'self' | 'records' | 'either'
}

/**
 * The patient fact catalogue, in display order.
 *
 * This is a general, realistic intake model — the facts a real patient either
 * knows about themselves or can pull from documents exported from a patient
 * portal (MyChart), Apple Health, Google Health, or lab printouts.
 */
export const FACT_DEFINITIONS: FactDefinition[] = [
  { key: 'age', label: 'Age', hint: 'Your age in years', type: 'number', typicalSource: 'self' },
  { key: 'sex', label: 'Sex', hint: 'Sex assigned at birth', type: 'text', typicalSource: 'self' },
  {
    key: 'primaryCondition',
    label: 'Primary condition',
    hint: 'Main diagnosis you are seeking a trial for',
    type: 'text',
    typicalSource: 'either',
  },
  {
    key: 'location',
    label: 'Location',
    hint: 'City and state, used to find nearby sites',
    type: 'text',
    typicalSource: 'self',
  },
  {
    key: 'medications',
    label: 'Current medications',
    hint: 'Medications you take now',
    type: 'list',
    typicalSource: 'either',
  },
  {
    key: 'allergies',
    label: 'Allergies',
    hint: 'Known drug or other allergies',
    type: 'list',
    typicalSource: 'either',
  },
  {
    key: 'priorTreatments',
    label: 'Prior treatments',
    hint: 'Treatments or procedures you have already had',
    type: 'list',
    typicalSource: 'either',
  },
  {
    key: 'biomarkers',
    label: 'Biomarkers / genetic markers',
    hint: 'From pathology or molecular reports (e.g. EGFR, HER2)',
    type: 'text',
    typicalSource: 'records',
  },
  {
    key: 'diseaseStage',
    label: 'Disease stage',
    hint: 'Stage from a clinical report, if applicable',
    type: 'text',
    typicalSource: 'records',
  },
  {
    key: 'performanceStatus',
    label: 'Performance status (ECOG)',
    hint: 'Functional status score (0–4), from clinical notes',
    type: 'number',
    typicalSource: 'records',
  },
]

/** Fact keys that hold a list of strings rather than a single value. */
export const LIST_FACT_KEYS: FactKey[] = [
  'medications',
  'allergies',
  'priorTreatments',
]

/** Fact keys edited/stored as numbers. */
export const NUMBER_FACT_KEYS: FactKey[] = ['age', 'performanceStatus']
