import { useApp } from '../state/AppContext'
import { TRAVEL_PREFERENCES } from '../data/trials'

export function TravelPreferences() {
  const { state, dispatch } = useApp()

  return (
    <section
      aria-labelledby="travel-heading"
      className="rounded-2xl border border-slate-200 bg-white p-6 shadow-card"
    >
      <h2 id="travel-heading" className="text-xl font-bold text-navy">
        Travel preferences
      </h2>
      <p className="mt-1 text-sm text-slate-600">
        Affects trial <strong>ordering only</strong>. Clinical assessments never
        change, and clinically relevant trials outside your preference are still
        shown (ranked lower).
      </p>

      <div
        role="radiogroup"
        aria-labelledby="travel-heading"
        className="mt-3 grid gap-2 sm:grid-cols-2"
      >
        {TRAVEL_PREFERENCES.map((pref) => {
          const active = state.travel.id === pref.id
          return (
            <button
              key={pref.id}
              type="button"
              role="radio"
              aria-checked={active}
              onClick={() => dispatch({ type: 'SET_TRAVEL', travel: pref })}
              className={`focus-ring rounded-lg border px-4 py-2.5 text-left text-sm font-medium ${
                active
                  ? 'border-teal bg-teal/5 text-teal-dark ring-1 ring-teal/30'
                  : 'border-slate-200 text-navy hover:bg-slate-50'
              }`}
            >
              {pref.label}
            </button>
          )
        })}
      </div>
      <p className="mt-2 text-[11px] text-slate-400">
        Distances shown on trial cards are explicitly labeled mock values, not
        computed driving times.
      </p>
    </section>
  )
}
