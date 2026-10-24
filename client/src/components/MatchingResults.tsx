import { useApp } from '../state/AppContext'
import { TrialCard } from './TrialCard'

export function MatchingResults() {
  const { ranked, state } = useApp()
  const withinCount = ranked.filter((r) => r.withinTravelPreference).length

  return (
    <section aria-labelledby="results-heading">
      <div className="mb-3 flex flex-wrap items-baseline justify-between gap-2">
        <h2 id="results-heading" className="text-xl font-bold text-navy">
          Ranked trial matches
        </h2>
        <p className="text-sm text-slate-500">
          {ranked.length} trials · {withinCount} within “{state.travel.label}”
        </p>
      </div>
      <p className="mb-4 rounded-lg bg-slate-50 px-3 py-2 text-xs text-slate-600">
        Ranking is deterministic: trials within your travel preference first,
        then by clinical compatibility (supported criteria add, potential
        conflicts subtract, unknown counts as zero). The score is a transparent
        screening signal, not a validated medical probability.
      </p>
      <div className="grid gap-4">
        {ranked.map((r) => (
          <TrialCard key={r.trial.id} ranked={r} highlightFact={state.lastChangedFact} />
        ))}
      </div>
    </section>
  )
}
