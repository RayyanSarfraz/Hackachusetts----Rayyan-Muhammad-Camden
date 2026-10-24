import { describe, it, expect } from 'vitest'
import { reducer, createInitialState } from '../store'
import { parseNotes } from '../../lib/noteParser'
import { SAMPLE_NOTES } from '../../lib/__tests__/fixtures'
import { DEMO_TRIALS, TRAVEL_PREFERENCES } from '../../data/trials'
import type { QuestionAnswer } from '../../types/domain'

function answer(
  factKey: QuestionAnswer['factKey'],
  value: string | number | null,
  isUnknown: boolean,
): QuestionAnswer {
  return { factKey, optionId: 'x', value, isUnknown, answeredAt: Date.now() }
}

describe('store reducer', () => {
  it('SET_PROFILE moves to review and extracts facts honestly', () => {
    let state = createInitialState(DEMO_TRIALS)
    state = reducer(state, { type: 'SET_PROFILE', profile: parseNotes(SAMPLE_NOTES) })
    expect(state.step).toBe('review')
    expect(state.analyzed).toBe(true)
    expect(state.profile.facts.biomarkers.known).toBe(false)
  })

  it('answering EGFR positive recalculates dependent assessments (before/after)', () => {
    let state = createInitialState(DEMO_TRIALS)
    state = reducer(state, { type: 'SET_PROFILE', profile: parseNotes(SAMPLE_NOTES) })
    state = reducer(state, { type: 'ANSWER_QUESTION', answer: answer('biomarkers', 'EGFR positive', false) })
    expect(state.profile.facts.biomarkers.value).toBe('EGFR positive')
    // Changes recorded for A, B, C biomarker criteria; D unaffected.
    const changedTrials = new Set(state.lastChanges.map((c) => c.trialId))
    expect(changedTrials.has('DEMO-A')).toBe(true)
    expect(changedTrials.has('DEMO-B')).toBe(true)
    expect(changedTrials.has('DEMO-C')).toBe(true)
    expect(changedTrials.has('DEMO-D')).toBe(false)
  })

  it('Unknown answer records review and keeps the fact Unknown', () => {
    let state = createInitialState(DEMO_TRIALS)
    state = reducer(state, { type: 'SET_PROFILE', profile: parseNotes(SAMPLE_NOTES) })
    state = reducer(state, { type: 'ANSWER_QUESTION', answer: answer('biomarkers', null, true) })
    expect(state.profile.facts.biomarkers.known).toBe(false)
    expect(state.reviewedUnknown).toContain('biomarkers')
    // No status change -> no before/after rows.
    expect(state.lastChanges).toHaveLength(0)
  })

  it('revising a previous answer recalculates dependent assessments', () => {
    let state = createInitialState(DEMO_TRIALS)
    state = reducer(state, { type: 'SET_PROFILE', profile: parseNotes(SAMPLE_NOTES) })
    state = reducer(state, { type: 'ANSWER_QUESTION', answer: answer('biomarkers', 'EGFR positive', false) })
    state = reducer(state, { type: 'ANSWER_QUESTION', answer: answer('biomarkers', 'EGFR negative', false) })
    expect(state.profile.facts.biomarkers.value).toBe('EGFR negative')
    // Only one answer retained for biomarkers (replaced, not appended).
    expect(state.answers.filter((a) => a.factKey === 'biomarkers')).toHaveLength(1)
  })

  it('SET_TRAVEL does not alter the clinical profile', () => {
    let state = createInitialState(DEMO_TRIALS)
    state = reducer(state, { type: 'SET_PROFILE', profile: parseNotes(SAMPLE_NOTES) })
    const before = state.profile
    const nearby = TRAVEL_PREFERENCES.find((t) => t.id === 'nearby')!
    state = reducer(state, { type: 'SET_TRAVEL', travel: nearby })
    expect(state.profile).toBe(before)
    expect(state.travel.id).toBe('nearby')
  })
})
