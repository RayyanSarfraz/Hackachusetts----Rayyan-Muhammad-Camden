import type { Trial, TravelPreference } from '../types/domain'

/**
 * Candidate studies used by the matching engine.
 *
 * This is a small, self-contained study catalogue the local engine matches
 * against. Study codes (A–D) are internal identifiers. Distances are labeled
 * estimates relative to a Boston, MA patient, not computed from a live
 * geocoding service.
 */
export const DEMO_TRIALS: Trial[] = [
  {
    id: 'DEMO-A',
    name: 'Study A — Targeted Therapy in EGFR+ Advanced NSCLC',
    location: 'Boston, MA',
    distance: { miles: 3, label: 'mock' },
    sourceLabel: 'Study criterion',
    criteria: [
      {
        id: 'A-condition',
        text: 'Histologically confirmed non-small cell lung cancer (NSCLC).',
        category: 'inclusion',
        dependsOn: ['primaryCondition'],
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
        id: 'A-biomarker',
        text: 'Documented EGFR activating mutation (EGFR positive) required.',
        category: 'inclusion',
        dependsOn: ['biomarkers'],
        estimatedEffort: 2,
        kind: 'biomarker',
      },
      {
        id: 'A-stage',
        text: 'Stage IV disease required.',
        category: 'inclusion',
        dependsOn: ['diseaseStage'],
        estimatedEffort: 2,
        kind: 'stage',
      },
      {
        id: 'A-performance',
        text: 'ECOG performance status 0 to 1.',
        category: 'inclusion',
        dependsOn: ['performanceStatus'],
        estimatedEffort: 2,
        kind: 'performance',
      },
    ],
  },
  {
    id: 'DEMO-B',
    name: 'Study B — Chemo-Immunotherapy in EGFR-wildtype NSCLC',
    location: 'Cambridge, MA',
    distance: { miles: 6, label: 'mock' },
    sourceLabel: 'Study criterion',
    criteria: [
      {
        id: 'B-condition',
        text: 'Histologically confirmed non-small cell lung cancer (NSCLC).',
        category: 'inclusion',
        dependsOn: ['primaryCondition'],
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
        id: 'B-biomarker',
        text: 'EGFR wild-type (EGFR negative) required.',
        category: 'inclusion',
        dependsOn: ['biomarkers'],
        estimatedEffort: 2,
        kind: 'biomarker',
      },
      {
        id: 'B-stage',
        text: 'Stage III or Stage IV disease.',
        category: 'inclusion',
        dependsOn: ['diseaseStage'],
        estimatedEffort: 2,
        kind: 'stage',
      },
    ],
  },
  {
    id: 'DEMO-C',
    name: 'Study C — Next-Generation TKI in EGFR+ NSCLC',
    location: 'Worcester, MA',
    distance: { miles: 48, label: 'mock' },
    sourceLabel: 'Study criterion',
    criteria: [
      {
        id: 'C-condition',
        text: 'Histologically confirmed non-small cell lung cancer (NSCLC).',
        category: 'inclusion',
        dependsOn: ['primaryCondition'],
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
        id: 'C-biomarker',
        text: 'Documented EGFR activating mutation (EGFR positive) required.',
        category: 'inclusion',
        dependsOn: ['biomarkers'],
        estimatedEffort: 2,
        kind: 'biomarker',
      },
      {
        id: 'C-performance',
        text: 'ECOG performance status 0 to 2.',
        category: 'inclusion',
        dependsOn: ['performanceStatus'],
        estimatedEffort: 2,
        kind: 'performance',
      },
    ],
  },
  {
    id: 'DEMO-D',
    name: 'Study D — Broad-Eligibility NSCLC Platform Study',
    location: 'Springfield, MA',
    distance: { miles: 90, label: 'mock' },
    sourceLabel: 'Study criterion',
    criteria: [
      {
        id: 'D-condition',
        text: 'Histologically confirmed non-small cell lung cancer (NSCLC).',
        category: 'inclusion',
        dependsOn: ['primaryCondition'],
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
        dependsOn: ['diseaseStage'],
        estimatedEffort: 2,
        kind: 'stage',
      },
      {
        id: 'D-performance',
        text: 'ECOG performance status 0 to 1.',
        category: 'inclusion',
        dependsOn: ['performanceStatus'],
        estimatedEffort: 2,
        kind: 'performance',
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
