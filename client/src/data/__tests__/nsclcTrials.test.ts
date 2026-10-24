import { describe, it, expect } from 'vitest'
import { NSCLC_TRIALS } from '../nsclcTrials'

const EGFR_POSITIVE = ['NCT04410796', 'NCT04181060', 'NCT03191149']
const EGFR_NEGATIVE = ['NCT07291037', 'NCT06767514', 'NCT07063745']
const KRAS_G12C = ['NCT06119581', 'NCT05920356']
const SELECTED_IDS = [...EGFR_POSITIVE, ...EGFR_NEGATIVE, ...KRAS_G12C]
const ALLOWED_KINDS = ['condition', 'age', 'egfr', 'stage', 'ecog']

function egfrRule(id: string) {
  const egfr = trialById(id).criteria.filter((c) => c.kind === 'egfr')
  expect(egfr).toHaveLength(1)
  const rule = egfr[0].rule
  return rule && 'egfr' in rule ? rule.egfr : undefined
}

function trialById(id: string) {
  const trial = NSCLC_TRIALS.find((t) => t.id === id)
  if (!trial) throw new Error(`missing trial ${id}`)
  return trial
}

// Validates: Requirements 1.8, 2.1, 2.2, 2.3, 2.4, 2.5, 7.4
describe('Feature: dataset-nsclc-trials, Property 1: Real trial file invariants', () => {
  it('holds exactly the eight selected trial ids', () => {
    expect(NSCLC_TRIALS).toHaveLength(SELECTED_IDS.length)
    expect(new Set(NSCLC_TRIALS.map((t) => t.id))).toEqual(new Set(SELECTED_IDS))
  })

  for (const trial of NSCLC_TRIALS) {
    it(`${trial.id} has consistent ids, source, status, phase and distance label`, () => {
      expect(trial.nctId).toBe(trial.id)
      expect(trial.sourceUrl).toBe(`https://clinicaltrials.gov/study/${trial.nctId}`)
      expect(trial.recruitmentStatus?.trim()).toBeTruthy()
      expect(trial.phase?.trim()).toBeTruthy()
      expect(trial.distance.label).toBe('approximate')
    })

    it(`${trial.id} criteria use allowed kinds and <nctId>-<kind> ids`, () => {
      expect(trial.criteria.length).toBeGreaterThan(0)
      for (const c of trial.criteria) {
        expect(ALLOWED_KINDS).toContain(c.kind)
        expect(c.id).toBe(`${trial.nctId}-${c.kind}`)
      }
    })
  }
})

// Validates: Requirements 2.7, 2.8, 2.9, 7.4
describe('Feature: dataset-nsclc-trials, Property 2: EGFR rule grouping', () => {
  for (const id of EGFR_POSITIVE) {
    it(`${id} requires EGFR positive`, () => {
      expect(egfrRule(id)).toBe('positive')
    })
  }

  for (const id of EGFR_NEGATIVE) {
    it(`${id} requires EGFR negative`, () => {
      expect(egfrRule(id)).toBe('negative')
    })
  }

  for (const id of KRAS_G12C) {
    it(`${id} (KRAS G12C) has no EGFR criterion`, () => {
      expect(trialById(id).criteria.some((c) => c.kind === 'egfr')).toBe(false)
    })
  }
})
