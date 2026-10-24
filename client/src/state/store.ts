import type {
  AssessmentChange,
  FactKey,
  PatientFact,
  PatientProfile,
  QuestionAnswer,
  TravelPreference,
  Trial,
} from '../types/domain'
import { emptyProfile } from '../lib/noteParser'
import { DEFAULT_TRAVEL_PREFERENCE } from '../data/trials'
import { diffAssessments } from '../lib/assessmentDiff'

/**
 * Centralized, immutable application state and reducer.
 *
 * All business-logic-affecting state lives here so patient profile, trials,
 * question history, travel preference and the last before/after diff stay
 * synchronized. State is never mutated directly — the reducer always returns
 * new objects.
 */

export type WorkflowStep = 'intake' | 'review' | 'matching'

export interface AppState {
  step: WorkflowStep
  trials: Trial[]
  profile: PatientProfile
  /** Draft notes in the textarea before analysis. */
  draftNotes: string
  /** True once notes have been analyzed and facts extracted. */
  analyzed: boolean
  travel: TravelPreference
  /** History of answered questions, newest last. */
  answers: QuestionAnswer[]
  /** Fact keys the user reviewed and left Unknown (so we don't re-ask). */
  reviewedUnknown: FactKey[]
  /** The most recent set of before/after assessment changes. */
  lastChanges: AssessmentChange[]
  /** Fact key of the most recent change, for highlighting. */
  lastChangedFact: FactKey | null
}

export function createInitialState(trials: Trial[]): AppState {
  return {
    step: 'intake',
    trials,
    profile: emptyProfile(),
    draftNotes: '',
    analyzed: false,
    travel: DEFAULT_TRAVEL_PREFERENCE,
    answers: [],
    reviewedUnknown: [],
    lastChanges: [],
    lastChangedFact: null,
  }
}

export type Action =
  | { type: 'SET_DRAFT_NOTES'; notes: string }
  | { type: 'SET_PROFILE'; profile: PatientProfile }
  | { type: 'CONFIRM_FACT'; key: FactKey; value: string | number | null }
  | { type: 'SET_STEP'; step: WorkflowStep }
  | { type: 'SET_TRAVEL'; travel: TravelPreference }
  | { type: 'ANSWER_QUESTION'; answer: QuestionAnswer }
  | { type: 'REVISE_FACT'; factKey: FactKey }
  | { type: 'RESET' }

function applyAnswerToProfile(
  profile: PatientProfile,
  answer: QuestionAnswer,
): PatientProfile {
  const existing = profile.facts[answer.factKey]
  const updated: PatientFact = {
    ...existing,
    value: answer.isUnknown ? null : answer.value,
    known: !answer.isUnknown,
    source: 'answered',
    evidence: answer.isUnknown
      ? undefined
      : `Answered via Next Best Question: ${String(answer.value)}`,
  }
  return {
    ...profile,
    facts: { ...profile.facts, [answer.factKey]: updated },
  }
}

export function reducer(state: AppState, action: Action): AppState {
  switch (action.type) {
    case 'SET_DRAFT_NOTES':
      return { ...state, draftNotes: action.notes }

    case 'SET_PROFILE':
      return {
        ...state,
        profile: action.profile,
        draftNotes: action.profile.rawNotes,
        analyzed: true,
        step: 'review',
        answers: [],
        reviewedUnknown: [],
        lastChanges: [],
        lastChangedFact: null,
      }

    case 'CONFIRM_FACT': {
      const existing = state.profile.facts[action.key]
      const updated: PatientFact = {
        ...existing,
        value: action.value,
        known: action.value !== null && action.value !== '',
        source: 'confirmed',
      }
      return {
        ...state,
        profile: {
          ...state.profile,
          facts: { ...state.profile.facts, [action.key]: updated },
        },
      }
    }

    case 'SET_STEP':
      return { ...state, step: action.step }

    case 'SET_TRAVEL':
      // Travel preference never touches clinical assessments or the profile.
      return { ...state, travel: action.travel }

    case 'ANSWER_QUESTION': {
      const before = state.profile
      const after = applyAnswerToProfile(before, action.answer)
      const changes = diffAssessments(state.trials, before, after)

      // Track reviewed-as-Unknown facts so the engine stops re-asking them,
      // and clear the flag if the user later provides a real answer.
      let reviewedUnknown = state.reviewedUnknown
      if (action.answer.isUnknown) {
        reviewedUnknown = reviewedUnknown.includes(action.answer.factKey)
          ? reviewedUnknown
          : [...reviewedUnknown, action.answer.factKey]
      } else {
        reviewedUnknown = reviewedUnknown.filter((k) => k !== action.answer.factKey)
      }

      // Replace any prior answer for the same fact (supports revision).
      const answers = [
        ...state.answers.filter((a) => a.factKey !== action.answer.factKey),
        action.answer,
      ]

      return {
        ...state,
        profile: after,
        answers,
        reviewedUnknown,
        lastChanges: changes,
        lastChangedFact: action.answer.factKey,
      }
    }

    case 'REVISE_FACT': {
      // Clear a previously answered fact back to Unknown so the engine can
      // surface the question again for a fresh answer. Dependent assessments
      // recalculate via the derived selectors.
      const before = state.profile
      const existing = before.facts[action.factKey]
      const cleared: PatientFact = {
        ...existing,
        value: null,
        known: false,
        source: 'answered',
        evidence: undefined,
      }
      const after: PatientProfile = {
        ...before,
        facts: { ...before.facts, [action.factKey]: cleared },
      }
      const changes = diffAssessments(state.trials, before, after)
      return {
        ...state,
        profile: after,
        answers: state.answers.filter((a) => a.factKey !== action.factKey),
        reviewedUnknown: state.reviewedUnknown.filter((k) => k !== action.factKey),
        lastChanges: changes,
        lastChangedFact: action.factKey,
      }
    }

    case 'RESET':
      return createInitialState(state.trials)

    default:
      return state
  }
}
