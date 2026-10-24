import { useApp } from './state/AppContext'
import { Header } from './components/Header'
import { WorkflowSteps } from './components/WorkflowSteps'
import { PatientIntake } from './components/PatientIntake'
import { ExtractedFacts } from './components/ExtractedFacts'
import { MatchingResults } from './components/MatchingResults'
import { NextBestQuestion } from './components/NextBestQuestion'
import { AssessmentChanges } from './components/AssessmentChanges'
import { TravelPreferences } from './components/TravelPreferences'

function App() {
  const { state, dispatch } = useApp()

  return (
    <div className="min-h-screen bg-slate-50 text-navy">
      <Header />

      <main className="mx-auto max-w-6xl px-4 py-8 sm:px-6">
        <WorkflowSteps current={state.step} />

        {state.step === 'intake' && (
          <div className="mx-auto max-w-3xl">
            <PatientIntake />
          </div>
        )}

        {state.step === 'review' && (
          <div className="mx-auto max-w-3xl space-y-6">
            <ExtractedFacts />
          </div>
        )}

        {state.step === 'matching' && (
          <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_360px]">
            {/* Main column: ranked trial cards */}
            <div className="order-2 lg:order-1">
              <div className="mb-4 flex items-center justify-between">
                <button
                  type="button"
                  onClick={() => dispatch({ type: 'SET_STEP', step: 'review' })}
                  className="focus-ring rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-navy hover:bg-slate-50"
                >
                  ← Edit patient facts
                </button>
                <button
                  type="button"
                  onClick={() => dispatch({ type: 'RESET' })}
                  className="focus-ring rounded-lg px-3 py-1.5 text-sm font-medium text-slate-500 hover:text-navy"
                >
                  Start over
                </button>
              </div>
              <MatchingResults />
            </div>

            {/* Side column: question engine, before/after, travel */}
            <div className="order-1 space-y-6 lg:order-2">
              <NextBestQuestion />
              <AssessmentChanges />
              <TravelPreferences />
            </div>
          </div>
        )}
      </main>

      <footer className="border-t border-slate-200 bg-white py-6">
        <div className="mx-auto max-w-6xl px-4 text-center text-xs text-slate-400 sm:px-6">
          TrialBridge demo · All patient data and trials are fictional. No data
          leaves your browser. Not for clinical use.
        </div>
      </footer>
    </div>
  )
}

export default App
