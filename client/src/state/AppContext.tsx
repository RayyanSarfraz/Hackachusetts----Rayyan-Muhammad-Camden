import {
  createContext,
  useContext,
  useMemo,
  useReducer,
  type ReactNode,
} from 'react'
import type { FactKey, MissingInformationQuestion, RankedTrial } from '../types/domain'
import { DEMO_TRIALS } from '../data/trials'
import { rankTrials } from '../lib/ranking'
import { buildQuestions } from '../lib/questionEngine'
import {
  createInitialState,
  reducer,
  type Action,
  type AppState,
} from './store'

interface AppContextValue {
  state: AppState
  dispatch: React.Dispatch<Action>
  /** Trials ranked with the current profile + travel preference. */
  ranked: RankedTrial[]
  /** The next best question, or null when none remain. */
  nextQuestion: MissingInformationQuestion | null
  /** All ranked candidate questions (for transparency). */
  candidateQuestions: MissingInformationQuestion[]
}

const AppContext = createContext<AppContextValue | null>(null)

export function AppProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(
    reducer,
    DEMO_TRIALS,
    createInitialState,
  )

  const ranked = useMemo(
    () => rankTrials(state.trials, state.profile, { travel: state.travel }),
    [state.trials, state.profile, state.travel],
  )

  const { candidates, next } = useMemo(
    () =>
      buildQuestions(
        state.trials,
        state.profile,
        new Set<FactKey>(state.reviewedUnknown),
      ),
    [state.trials, state.profile, state.reviewedUnknown],
  )

  const value: AppContextValue = {
    state,
    dispatch,
    ranked,
    nextQuestion: next,
    candidateQuestions: candidates,
  }

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>
}

// eslint-disable-next-line react-refresh/only-export-components
export function useApp(): AppContextValue {
  const ctx = useContext(AppContext)
  if (!ctx) throw new Error('useApp must be used within an AppProvider')
  return ctx
}
