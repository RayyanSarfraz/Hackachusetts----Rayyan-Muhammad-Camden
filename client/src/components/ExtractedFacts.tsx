import { useApp } from '../state/AppContext'
import { FACT_DEFINITIONS } from '../data/demoPatient'
import type { FactKey } from '../types/domain'

export function ExtractedFacts() {
  const { state, dispatch } = useApp()
  const { facts } = state.profile

  function edit(key: FactKey, raw: string) {
    const trimmed = raw.trim()
    let value: string | number | null = trimmed === '' ? null : trimmed
    if (key === 'age' || key === 'ecogStatus') {
      value = trimmed === '' ? null : Number(trimmed)
      if (value !== null && Number.isNaN(value)) value = null
    }
    dispatch({ type: 'CONFIRM_FACT', key, value })
  }

  return (
    <section
      aria-labelledby="facts-heading"
      className="rounded-2xl border border-slate-200 bg-white p-6 shadow-card"
    >
      <div className="mb-4 flex items-center justify-between gap-3">
        <div>
          <h2 id="facts-heading" className="text-xl font-bold text-navy">
            Review extracted facts
          </h2>
          <p className="mt-1 text-sm text-slate-600">
            Confirm or correct the facts before matching. Blank fields stay
            Unknown — missing data is never treated as a negative finding.
          </p>
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        {FACT_DEFINITIONS.map((def) => {
          const fact = facts[def.key]
          const known = fact.known
          return (
            <div
              key={def.key}
              className={`rounded-xl border p-3 ${
                known ? 'border-slate-200 bg-slate-50' : 'border-dashed border-slate-300 bg-white'
              }`}
            >
              <div className="flex items-center justify-between">
                <label
                  htmlFor={`fact-${def.key}`}
                  className="text-sm font-semibold text-navy"
                >
                  {def.label}
                </label>
                <span
                  className={`text-xs font-medium ${
                    known ? 'text-emerald-700' : 'text-slate-400'
                  }`}
                >
                  {known ? fact.source : 'Unknown'}
                </span>
              </div>
              <input
                id={`fact-${def.key}`}
                defaultValue={
                  fact.value === null ? '' : displayRaw(def.key, fact.value)
                }
                key={`${def.key}-${String(fact.value)}`}
                onBlur={(e) => edit(def.key, e.target.value)}
                placeholder="Unknown / not documented"
                className="focus-ring mt-2 w-full rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 text-sm text-navy placeholder:text-slate-400"
              />
              {fact.evidence && (
                <p className="mt-1.5 text-xs text-slate-500">
                  Evidence: <span className="italic">"{fact.evidence}"</span>
                </p>
              )}
            </div>
          )
        })}
      </div>

      <div className="mt-5 flex flex-wrap gap-3">
        <button
          type="button"
          onClick={() => dispatch({ type: 'SET_STEP', step: 'matching' })}
          className="focus-ring inline-flex items-center gap-2 rounded-lg bg-teal px-5 py-2.5 text-sm font-semibold text-white hover:bg-teal-dark"
        >
          Confirm &amp; see matching trials →
        </button>
        <button
          type="button"
          onClick={() => dispatch({ type: 'SET_STEP', step: 'intake' })}
          className="focus-ring inline-flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm font-medium text-navy hover:bg-slate-50"
        >
          ← Back to notes
        </button>
      </div>
    </section>
  )
}

/** Show the editable raw value (not the pretty EGFR label) in the input. */
function displayRaw(key: FactKey, value: unknown): string {
  if (key === 'egfrStatus') return String(value)
  return String(value)
}
