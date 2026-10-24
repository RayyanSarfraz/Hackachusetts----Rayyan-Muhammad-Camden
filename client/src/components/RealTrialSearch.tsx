import { useState } from 'react'
import {
  matchTrials,
  type MatchResponse,
  type MatchQuestion,
} from '../api/engineMatch'

/**
 * Real trial search — calls the live engine (/api/engine/match/) over the
 * actual trial dataset, then renders matched trials plus a clarifying-question
 * form that refines the match when submitted.
 *
 * Additive: this view is independent of the offline demo flow.
 */
export function RealTrialSearch() {
  const [note, setNote] = useState('')
  const [condition, setCondition] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<MatchResponse | null>(null)
  const [answers, setAnswers] = useState<Record<string, string>>({})

  async function run(withAnswers: Record<string, string> = {}) {
    setLoading(true)
    setError(null)
    try {
      const data = await matchTrials(
        { medical_note: note, primary_condition: condition || undefined },
        withAnswers,
      )
      setResult(data)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Search failed.')
    } finally {
      setLoading(false)
    }
  }

  function submitAnswers(e: React.FormEvent) {
    e.preventDefault()
    run(answers)
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <section className="rounded-xl border border-slate-200 bg-white p-6">
        <h2 className="text-lg font-semibold text-navy">Find clinical trials</h2>
        <p className="mt-1 text-sm text-slate-500">
          Searches real recruiting trials. Medical details are extracted from
          your note; we never invent facts.
        </p>

        <label className="mt-4 block text-sm font-medium text-slate-600">
          Primary condition (optional)
          <input
            type="text"
            value={condition}
            onChange={(e) => setCondition(e.target.value)}
            placeholder="e.g. Alcohol Use Disorder"
            className="focus-ring mt-1 w-full rounded-lg border border-slate-300 px-3 py-2"
          />
        </label>

        <label className="mt-4 block text-sm font-medium text-slate-600">
          Medical history / notes
          <textarea
            rows={5}
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder="Describe the patient's history in plain text."
            className="focus-ring mt-1 w-full rounded-lg border border-slate-300 px-3 py-2"
          />
        </label>

        {error && (
          <p className="mt-3 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
            {error}
          </p>
        )}

        <button
          type="button"
          onClick={() => run(answers)}
          disabled={loading || (!note.trim() && !condition.trim())}
          className="focus-ring mt-4 rounded-lg bg-navy px-4 py-2 font-medium text-white disabled:opacity-50"
        >
          {loading ? 'Searching…' : 'Find trials'}
        </button>
      </section>

      {result && (
        <>
          {result.questions.length > 0 && (
            <QuestionForm
              questions={result.questions}
              answers={answers}
              setAnswers={setAnswers}
              onSubmit={submitAnswers}
              loading={loading}
            />
          )}

          <section className="rounded-xl border border-slate-200 bg-white p-6">
            <h3 className="font-semibold text-navy">
              Matched trials{' '}
              <span className="text-sm font-normal text-slate-400">
                ({result.results.length})
              </span>
            </h3>

            {!result.retrieval_available ? (
              <p className="mt-2 rounded-lg bg-amber-50 px-3 py-2 text-sm text-amber-800">
                {result.detail ||
                  'Trial retrieval is unavailable right now. No results to show.'}
              </p>
            ) : result.results.length === 0 ? (
              <p className="mt-2 text-sm text-slate-500">No matching trials found.</p>
            ) : (
              <ol className="mt-3 space-y-3">
                {result.results.map((r, i) => (
                  <li
                    key={r.trial_id ?? i}
                    className="rounded-lg border border-slate-200 p-4"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <span className="font-medium text-navy">
                        {r.trial?.title || r.trial_id}
                      </span>
                      <span className="shrink-0 text-xs text-slate-400">
                        {r.trial?.phase} · {r.trial?.status}
                      </span>
                    </div>
                    <p className="mt-1 text-xs text-slate-500">
                      {r.trial?.nct_id}
                      {r.trial?.conditions?.length
                        ? ` · ${r.trial.conditions.join(', ')}`
                        : ''}
                    </p>
                  </li>
                ))}
              </ol>
            )}

            <p className="mt-4 text-xs text-slate-400">
              Preliminary matches for screening only — not an eligibility
              determination. Trials are real recruiting studies; verify with the
              study team.
            </p>
          </section>
        </>
      )}
    </div>
  )
}

function QuestionForm({
  questions,
  answers,
  setAnswers,
  onSubmit,
  loading,
}: {
  questions: MatchQuestion[]
  answers: Record<string, string>
  setAnswers: (a: Record<string, string>) => void
  onSubmit: (e: React.FormEvent) => void
  loading: boolean
}) {
  return (
    <section className="rounded-xl border border-sky-200 bg-sky-50/50 p-6">
      <h3 className="font-semibold text-navy">A few details improve matching</h3>
      <p className="mt-1 text-sm text-slate-500">
        Optional. Answer what you can; leave blank to keep it unknown.
      </p>
      <form onSubmit={onSubmit} className="mt-4 space-y-3">
        {questions.map((q) => (
          <label
            key={q.question_id}
            className="block text-sm font-medium text-slate-600"
          >
            {q.display_question}
            <input
              type={q.answer_type === 'number' ? 'number' : 'text'}
              value={answers[q.required_fact_key] ?? ''}
              onChange={(e) =>
                setAnswers({ ...answers, [q.required_fact_key]: e.target.value })
              }
              className="focus-ring mt-1 w-full rounded-lg border border-slate-300 px-3 py-2"
            />
          </label>
        ))}
        <button
          type="submit"
          disabled={loading}
          className="focus-ring rounded-lg bg-navy px-4 py-2 font-medium text-white disabled:opacity-50"
        >
          {loading ? 'Refining…' : 'Refine matches'}
        </button>
      </form>
    </section>
  )
}
