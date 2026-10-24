import type { Trial, TravelPreference } from '../types/domain'

/**
 * Four clearly fictional demo studies. These are NOT real trials.
 * No NCT identifiers, no real contact information — everything is mock.
 *
 * Distances are explicitly labeled mock values, not computed from a geographic
 * service. They are rough stand-ins relative to a Boston, MA patient.
 */
export const DEMO_TRIALS: Trial[] = [
  {
    id: 'DEMO-A',
    name: 'Study A — Targeted Therapy in EGFR+ Advanced NSCLC (Fictional)',
    location: 'Boston, MA',
    distance: { miles: 3, label: 'mock' },
    sourceLabel: 'Demo criterion',
    criteria: [
      {
        id: 'A-condition',
        text: 'Histologically confirmed non-small cell lung cancer (NSCLC).',
        category: 'inclusion',
        dependsOn: ['condition'],
        estimatedEffort: 1,
        kind: 'condition',
      },
      {
        id: 'A-age',
        text: 'Age between 18 and 75 years, inclusive.',
        category: 'inclusion',
        dependsOn: ['age'],
        estimatedEffort: 1,
        kind: 'age',
      },
      {
        id: 'A-egfr',
        text: 'Documented EGFR activating mutation (EGFR positive) required.',
        category: 'inclusion',
        dependsOn: ['egfrStatus'],
        estimatedEffort: 2,
        kind: 'egfr',
      },
      {
        id: 'A-stage',
        text: 'Stage IV disease required.',
        category: 'inclusion',
        dependsOn: ['cancerStage'],
        estimatedEffort: 2,
        kind: 'stage',
      },
      {
        id: 'A-ecog',
        text: 'ECOG performance status 0 to 1.',
        category: 'inclusion',
        dependsOn: ['ecogStatus'],
        estimatedEffort: 2,
        kind: 'ecog',
      },
    ],
  },
  {
    id: 'DEMO-B',
    name: 'Study B — Chemo-Immunotherapy in EGFR-wildtype NSCLC (Fictional)',
    location: 'Cambridge, MA',
    distance: { miles: 6, label: 'mock' },
    sourceLabel: 'Demo criterion',
    criteria: [
      {
        id: 'B-condition',
        text: 'Histologically confirmed non-small cell lung cancer (NSCLC).',
        category: 'inclusion',
        dependsOn: ['condition'],
        estimatedEffort: 1,
        kind: 'condition',
      },
      {
        id: 'B-age',
        text: 'Age between 18 and 75 years, inclusive.',
        category: 'inclusion',
        dependsOn: ['age'],
        estimatedEffort: 1,
        kind: 'age',
      },
      {
        id: 'B-egfr',
        text: 'EGFR wild-type (EGFR negative) required.',
        category: 'inclusion',
        dependsOn: ['egfrStatus'],
        estimatedEffort: 2,
        kind: 'egfr',
      },
      {
        id: 'B-stage',
        text: 'Stage III or Stage IV disease.',
        category: 'inclusion',
        dependsOn: ['cancerStage'],
        estimatedEffort: 2,
        kind: 'stage',
      },
    ],
  },
  {
    id: 'DEMO-C',
    name: 'Study C — Next-Generation TKI in EGFR+ NSCLC (Fictional)',
    location: 'Worcester, MA',
    distance: { miles: 48, label: 'mock' },
    sourceLabel: 'Demo criterion',
    criteria: [
      {
        id: 'C-condition',
        text: 'Histologically confirmed non-small cell lung cancer (NSCLC).',
        category: 'inclusion',
        dependsOn: ['condition'],
        estimatedEffort: 1,
        kind: 'condition',
      },
      {
        id: 'C-age',
        text: 'Age between 18 and 75 years, inclusive.',
        category: 'inclusion',
        dependsOn: ['age'],
        estimatedEffort: 1,
        kind: 'age',
      },
      {
        id: 'C-egfr',
        text: 'Documented EGFR activating mutation (EGFR positive) required.',
        category: 'inclusion',
        dependsOn: ['egfrStatus'],
        estimatedEffort: 2,
        kind: 'egfr',
      },
      {
        id: 'C-ecog',
        text: 'ECOG performance status 0 to 2.',
        category: 'inclusion',
        dependsOn: ['ecogStatus'],
        estimatedEffort: 2,
        kind: 'ecog',
      },
    ],
  },
  {
    id: 'DEMO-D',
    name: 'Study D — Broad-Eligibility NSCLC Platform Study (Fictional)',
    location: 'Springfield, MA',
    distance: { miles: 90, label: 'mock' },
    sourceLabel: 'Demo criterion',
    criteria: [
      {
        id: 'D-condition',
        text: 'Histologically confirmed non-small cell lung cancer (NSCLC).',
        category: 'inclusion',
        dependsOn: ['condition'],
        estimatedEffort: 1,
        kind: 'condition',
      },
      {
        id: 'D-age',
        text: 'Age between 18 and 75 years, inclusive.',
        category: 'inclusion',
        dependsOn: ['age'],
        estimatedEffort: 1,
        kind: 'age',
      },
      {
        id: 'D-stage',
        text: 'Stage IV disease required. No EGFR restriction.',
        category: 'inclusion',
        dependsOn: ['cancerStage'],
        estimatedEffort: 2,
        kind: 'stage',
      },
      {
        id: 'D-ecog',
        text: 'ECOG performance status 0 to 1.',
        category: 'inclusion',
        dependsOn: ['ecogStatus'],
        estimatedEffort: 2,
        kind: 'ecog',
      },
    ],
  },
]

export const TRAVEL_PREFERENCES: TravelPreference[] = [
  { id: 'nearby', label: 'Nearby only (≤ 10 mi)', maxMiles: 10 },
  { id: 'within_50', label: 'Within 50 miles', maxMiles: 50 },
  { id: 'within_100', label: 'Within 100 miles', maxMiles: 100 },
  { id: 'any', label: 'Any distance', maxMiles: null },
]

export const DEFAULT_TRAVEL_PREFERENCE = TRAVEL_PREFERENCES[2] // Within 100 miles
