import { describe, it, expect } from 'vitest'
import { assessCriterion, assessTrial } from '../assessor'
import { emptyProfile } from '../noteParser'
import type {
  CriterionRule,
  EligibilityCriterion,
  FactKey,
  PatientProfile,
  Trial,
} from '../../types/domain'

type Kind = 'age' | 'egfr' | 'stage' | 'ecog'

const FACT_FOR: Record<Kind, FactKey> = {
  age: 'age',
  egfr: 'egfrStatus',
  stage: 'cancerStage',
  ecog: 'ecogStatus',
}

/** A one-criterion trial whose criterion carries the given rule. */
function ruleTrial(kind: Kind, rule: CriterionRule): Trial {
  const criterion: EligibilityCriterion = {
    id: `T-${kind}`,
    text: 'Verbatim criterion text with no demo keywords.',
    category: 'inclusion',
    dependsOn: [FACT_FOR[kind]],
    estimatedEffort: 1,
    kind,
    rule,
  }
  return {
    id: 'NCT00000000',
    name: 'Rule test trial',
    location: 'Boston, MA',
    distance: { miles: 10, label: 'approximate' },
    criteria: [criterion],
    sourceLabel: 'ClinicalTrials.gov',
  }
}

function withFact(key: FactKey, value: string | number): PatientProfile {
  const p = emptyProfile()
  return {
    ...p,
    facts: { ...p.facts, [key]: { ...p.facts[key], value, known: true } },
  }
}

function statusFor(kind: Kind, rule: CriterionRule, profile: PatientProfile) {
  const trial = ruleTrial(kind, rule)
  return assessCriterion(trial.criteria[0], trial, profile).status
}

const expected = (met: boolean) => (met ? 'supported' : 'potential_conflict')

describe('Feature: dataset-nsclc-trials, Property 3: Rule assessment matches the rule predicate', () => {
  // **Validates: Requirements 4.1, 4.3, 4.4, 4.5, 4.6, 4.8, 7.5**
  const ages = Array.from({ length: 101 }, (_, i) => i) // 0..100

  it('age with minAge only: supported iff age >= minAge', () => {
    for (const minAge of [18, 21, 50]) {
      for (const age of ages) {
        expect(statusFor('age', { minAge }, withFact('age', age))).toBe(
          expected(age >= minAge),
        )
      }
    }
  })

  it('age with maxAge only: supported iff age <= maxAge', () => {
    for (const maxAge of [17, 65, 75]) {
      for (const age of ages) {
        expect(statusFor('age', { maxAge }, withFact('age', age))).toBe(
          expected(age <= maxAge),
        )
      }
    }
  })

  it('age with both bounds: supported iff minAge <= age <= maxAge', () => {
    for (const [minAge, maxAge] of [
      [18, 75],
      [40, 40],
      [12, 99],
    ]) {
      for (const age of ages) {
        expect(statusFor('age', { minAge, maxAge }, withFact('age', age))).toBe(
          expected(age >= minAge && age <= maxAge),
        )
      }
    }
  })

  it('age bounds are inclusive at the exact boundary', () => {
    const rule = { minAge: 18, maxAge: 75 }
    expect(statusFor('age', rule, withFact('age', 17))).toBe('potential_conflict')
    expect(statusFor('age', rule, withFact('age', 18))).toBe('supported')
    expect(statusFor('age', rule, withFact('age', 75))).toBe('supported')
    expect(statusFor('age', rule, withFact('age', 76))).toBe('potential_conflict')
  })

  it('egfr: supported iff the documented status equals rule.egfr', () => {
    const values = ['positive', 'negative'] as const
    for (const required of values) {
      for (const actual of values) {
        expect(
          statusFor('egfr', { egfr: required }, withFact('egfrStatus', actual)),
        ).toBe(expected(actual === required))
      }
    }
  })

  it('stages: supported iff the documented stage is in rule.stages', () => {
    const all = ['I', 'II', 'III', 'IV']
    const ruleSets = [['IV'], ['III', 'IV'], ['I', 'II'], all]
    for (const stages of ruleSets) {
      for (const stage of all) {
        expect(statusFor('stage', { stages }, withFact('cancerStage', stage))).toBe(
          expected(stages.includes(stage)),
        )
      }
    }
  })

  it('ecogMax: supported iff ecog <= ecogMax (inclusive)', () => {
    for (let ecogMax = 0; ecogMax <= 4; ecogMax++) {
      for (let ecog = 0; ecog <= 4; ecog++) {
        expect(statusFor('ecog', { ecogMax }, withFact('ecogStatus', ecog))).toBe(
          expected(ecog <= ecogMax),
        )
      }
    }
  })

  it('assessTrial rolls rule results into the summary counts', () => {
    const met = assessTrial(ruleTrial('ecog', { ecogMax: 1 }), withFact('ecogStatus', 1))
    expect(met.supported).toBe(1)
    expect(met.potentialConflict).toBe(0)
    const notMet = assessTrial(
      ruleTrial('ecog', { ecogMax: 1 }),
      withFact('ecogStatus', 2),
    )
    expect(notMet.supported).toBe(0)
    expect(notMet.potentialConflict).toBe(1)
  })
})

describe('Feature: dataset-nsclc-trials, Property 4: Unknown facts stay unknown', () => {
  // **Validates: Requirements 4.7, 7.5**
  const cases: [Kind, CriterionRule][] = [
    ['age', { minAge: 18 }],
    ['age', { maxAge: 75 }],
    ['age', { minAge: 18, maxAge: 75 }],
    ['egfr', { egfr: 'positive' }],
    ['egfr', { egfr: 'negative' }],
    ['stage', { stages: ['III', 'IV'] }],
    ['ecog', { ecogMax: 1 }],
  ]

  it.each(cases)('%s rule %j with the fact unknown returns unknown', (kind, rule) => {
    const trial = ruleTrial(kind, rule)
    const profile = emptyProfile()
    expect(profile.facts[FACT_FOR[kind]].known).toBe(false)
    expect(assessCriterion(trial.criteria[0], trial, profile).status).toBe('unknown')
    const summary = assessTrial(trial, profile)
    expect(summary.unknown).toBe(1)
    expect(summary.supported).toBe(0)
    expect(summary.potentialConflict).toBe(0)
  })
})
