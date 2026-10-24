import { useState } from 'react'
import { useApp } from '../state/AppContext'
import { Accordion } from './ui/Accordion'
import { FACT_DEFINITIONS } from '../data/facts'

export function NextBestQuestion() {
  const { state, dispatch, nextQuestion, candidateQuestions } = useApp()
  const [selected, setSelected] = useState<string | null>(null)

  // Completion state: no more useful questions remain.
  if (!nextQuestion) {
    const unresolved = FACT_DEFINITIONS.filter(
      (d) => !state.profile.facts[d.key].known,
    )
    return (
      <section
        aria-labelledby="nbq-heading"
        className="rounded-2xl border border-slate-200 bg-white p-6 shadow-card"
      >
        <h2 id="nbq-heading" className="text-xl font-bold text-navy">
          Next Best Question
        </h2>
        <div className="mt-3 rounded-xl bg-emerald-50 p-4 text-sm text-emerald-800 ring-1 ring-inset ring-emerald-200">
          <p className="font-semibold">No further useful questions remain.</p>
          <p className="mt-1">
            Every question that could clarify a trial criterion has been
            reviewed.
          </p>
          {unresolved.length > 0 && (
            <div className="mt-3">
              <p className="font-semibold">Unresolved information for clinician review:</p>
              <ul className="mt-1 list-inside list-disc">
                {unresolved.map((d) => (
                  <li key={d.key}>{d.label}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </section>
    )
  }

  const q = nextQuestion

  function submit() {
    if (!selected) return
    const option = q.options.find((o) => o.id === selected)
    if (!option) return
    dispatch({
      type: 'ANSWER_QUESTION',
      answer: {
        factKey: q.factKey,
        optionId: option.id,
        value: option.value,
        isUnknown: option.isUnknown,
        answeredAt: Date.now(),
      },
    })
    setSelected(null)
  }

  return (
    <section
      aria-labelledby="nbq-heading"
      className="rounded-2xl border border-teal/30 bg-white p-6 shadow-card ring-1 ring-teal/10"
    >
      <div className="mb-3 flex items-center justify-between gap-3">
        <h2 id="nbq-heading" className="text-xl font-bold text-navy">
          Next Best Question
        </h2>
        <span className="inline-flex items-center gap-1.5 rounded-full bg-teal/10 px-3 py-1 text-xs font-bold text-teal-dark ring-1 ring-inset ring-teal/30">
          Affects {q.affectedAssessments} trial assessment
          {q.affectedAssessments === 1 ? '' : 's'} · {q.affectedTrials} trial
          {q.affectedTrials === 1 ? '' : 's'}
        </span>
      </div>

      <p className="text-base font-semibold text-navy">{q.text}</p>

      <fieldset className="mt-3 space-y-2">
        <legend className="sr-only">Answer options</legend>
        {q.options.map((opt) => (
          <label
            key={opt.id}
            className={`flex cursor-pointer items-center gap-3 rounded-lg border px-3 py-2.5 text-sm ${
              selected === opt.id
                ? 'border-teal bg-teal/5 ring-1 ring-teal/30'
                : 'border-slate-200 hover:bg-slate-50'
            } ${opt.isUnknown ? 'text-slate-500' : 'text-navy'}`}
          >
            <input
              type="radio"
              name={`nbq-${q.factKey}`}
              value={opt.id}
              checked={selected === opt.id}
              onChange={() => setSelected(opt.id)}
              className="h-4 w-4 accent-teal"
            />
            <span className="font-medium">{opt.label}</span>
          </label>
        ))}
      </fieldset>

      <div className="mt-4 flex flex-wrap items-center gap-3">
        <button
          type="button"
          onClick={submit}
          disabled={!selected}
          className="focus-ring inline-flex items-center gap-2 rounded-lg bg-teal px-5 py-2.5 text-sm font-semibold text-white hover:bg-teal-dark disabled:cursor-not-allowed disabled:opacity-50"
        >
          Submit Answer
        </button>
      </div>

      <div className="mt-4">
        <Accordion title="Why are we asking this?">
          <p className="text-sm text-slate-700">{q.rationale}</p>
          <div className="mt-3 rounded-lg bg-slate-50 p-3 text-xs text-slate-600">
            <p className="font-semibold text-navy">How this was prioritized</p>
            <p className="mt-1">
              priority = affected assessments ÷ (1 + estimated effort) ={' '}
              {q.affectedAssessments} ÷ (1 + {q.estimatedEffort}) ={' '}
              <strong>{q.priority}</strong>
            </p>
            <table className="mt-2 w-full text-left">
              <thead>
                <tr className="text-slate-500">
                  <th className="py-1 pr-2 font-medium">Candidate</th>
                  <th className="py-1 pr-2 font-medium">Affects</th>
                  <th className="py-1 pr-2 font-medium">Effort</th>
                  <th className="py-1 font-medium">Priority</th>
                </tr>
              </thead>
              <tbody>
                {candidateQuestions.map((c) => (
                  <tr
                    key={c.factKey}
                    className={c.factKey === q.factKey ? 'font-semibold text-teal-dark' : ''}
                  >
                    <td className="py-1 pr-2">{labelFor(c.factKey)}</td>
                    <td className="py-1 pr-2">{c.affectedAssessments}</td>
                    <td className="py-1 pr-2">{c.estimatedEffort}</td>
                    <td className="py-1">{c.priority}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <p className="mt-2 text-[11px] text-slate-400">
              Counts are computed from the current mock data, not hard-coded.
              This question requests existing record information only — it does
              not recommend any new medical test.
            </p>
          </div>
        </Accordion>
      </div>
    </section>
  )
}

function labelFor(key: string): string {
  return FACT_DEFINITIONS.find((d) => d.key === key)?.label ?? key
}
