import { useApp } from '../state/AppContext'
import { StatusBadge } from './ui/StatusBadge'
import { FACT_DEFINITIONS } from '../data/facts'
import type { QuestionAnswer } from '../types/domain'

export function AssessmentChanges() {
  const { state, dispatch } = useApp()
  const { lastChanges, lastChangedFact, answers } = state

  if (answers.length === 0) {
    return null
  }

  const changedLabel = lastChangedFact
    ? (FACT_DEFINITIONS.find((d) => d.key === lastChangedFact)?.label ?? lastChangedFact)
    : null

  return (
    <section
      aria-labelledby="changes-heading"
      className="rounded-2xl border border-slate-200 bg-white p-6 shadow-card"
    >
      <h2 id="changes-heading" className="text-xl font-bold text-navy">
        Before vs After
      </h2>

      {changedLabel && (
        <p className="mt-1 text-sm text-slate-600">
          Most recent update: <strong>{changedLabel}</strong>.
        </p>
      )}

      {lastChanges.length === 0 ? (
        <p className="mt-3 rounded-lg bg-slate-50 p-3 text-sm text-slate-600">
          That answer did not change any criterion status. Unknown criteria stay
          Unknown until a documented value is provided.
        </p>
      ) : (
        <ul className="mt-3 space-y-2">
          {lastChanges.map((c) => (
            <li
              key={`${c.trialId}-${c.criterionId}`}
              className="rounded-lg border border-teal/30 bg-teal/5 p-3"
            >
              <div className="flex flex-wrap items-center justify-between gap-2">
                <p className="text-sm font-semibold text-navy">
                  {c.trialId} — {c.criterionText}
                </p>
                <div className="flex items-center gap-2">
                  <StatusBadge status={c.before} />
                  <span aria-hidden="true" className="text-slate-400">
                    →
                  </span>
                  <StatusBadge status={c.after} />
                </div>
              </div>
              <p className="mt-1.5 text-xs text-slate-600">{c.reason}</p>
            </li>
          ))}
        </ul>
      )}

      {answers.length > 0 && (
        <div className="mt-5">
          <h3 className="text-sm font-semibold text-navy">
            Your answers (revisable)
          </h3>
          <ul className="mt-2 space-y-2">
            {[...answers]
              .sort((a, b) => a.answeredAt - b.answeredAt)
              .map((a) => (
                <AnswerRow
                  key={a.factKey}
                  answer={a}
                  onRevise={() => dispatch({ type: 'REVISE_FACT', factKey: a.factKey })}
                />
              ))}
          </ul>
          <p className="mt-2 text-[11px] text-slate-400">
            Revise clears the stored value so you can answer again; dependent
            assessments recalculate automatically.
          </p>
        </div>
      )}
    </section>
  )
}

function AnswerRow({
  answer,
  onRevise,
}: {
  answer: QuestionAnswer
  onRevise: () => void
}) {
  const label = FACT_DEFINITIONS.find((d) => d.key === answer.factKey)?.label
  const valueText = answer.isUnknown
    ? 'Unknown / not documented'
    : String(answer.value)
  return (
    <li className="flex items-center justify-between gap-3 rounded-lg border border-slate-200 px-3 py-2 text-sm">
      <span className="text-navy">
        <strong>{label}:</strong> {valueText}
      </span>
      <button
        type="button"
        onClick={onRevise}
        className="focus-ring rounded-md border border-slate-300 px-2.5 py-1 text-xs font-medium text-navy hover:bg-slate-50"
      >
        Revise
      </button>
    </li>
  )
}
