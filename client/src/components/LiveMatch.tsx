import { useMemo, useState } from 'react'
import { useApp } from '../state/AppContext'
import { combinedNotes } from '../state/store'
import { matchTrials, type MatchResponse, type MatchQuestion } from '../api/engineMatch'
import { PatientIntake } from './PatientIntake'

/**
 * Live match flow — the REAL experience.
 *
 * Reuses the rich intake tray (upload PDF/CSV/JSON/XML or paste) to collect
 * documents, then sends the combined text to the engine (/api/engine/match/),
 * which runs MedGemma extraction + ChromaDB retrieval over the real trial
 * dataset. Shows what was extracted, the matched trials, and a clarifying-
 * question form that refines the match. No login; nothing fabricated.
 */
export function LiveMatch() {
  const { state } = useApp()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<MatchResponse | null>(null)
  const [answers, setAnswers] = useState<Record<string, string>>({})

  const notes = useMemo(() => combinedNotes(state.documents), [state.documents])
  const canSearch = notes.trim().length > 0 && !loading

  async function run(withAnswers: Record<string, string> = {}) {
    setLoading(true)
    setError(null)
    try {
      const data = await matchTrials({ medical_note: notes }, withAnswers)
      setResult(data)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Search failed.')
    } finally {
      setLoading(false)
    }
  }

  function submitAnswers(e: React.FormEvent) {
    e.preventDefault()
    void run(answers)
  }

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      {/* Reuse the full intake tray for document upload / paste. */}
      <PatientIntake />

      <div className="flex flex-wrap items-center gap-3">
        <button
          type="button"
          onClick={() => void run(answers)}
          disabled={!canSearch}
          className="focus-ring inline-flex items-center gap-2 rounded-lg bg-teal px-5 py-2.5 text-sm font-semibold text-white hover:bg-teal-dark disabled:cursor-not-allowed disabled:opacity-50"
        >
          {loading ? 'Searching real trials…' : 'Find matching trials'}
        </button>
        {!canSearch && !loading && (
          <span className="text-sm text-slate-500">
            Add at least one document above, then search.
          </span>
        )}
      </div>

      {error && (
        <p role="alert" className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </p>
      )}

      {result && (
        <>
          <ExtractedSummary result={result} />

          {result.questions.length > 0 && (
            <QuestionForm
              questions={result.questions}
              answers={answers}
              setAnswers={setAnswers}
              onSubmit={submitAnswers}
              loading={loading}
            />
          )}

          <MatchedTrials result={result} />
        </>
      )}
    </div>
  )
}

function ExtractedSummary({ result }: { result: MatchResponse }) {
  const profile = result.profile as Record<string, unknown>
  const facts: { label: string; value: string }[] = []
  const push = (label: string, v: unknown) => {
    if (v !== null && v !== undefined && v !== '') facts.push({ label, value: String(v) })
  }
  push('Age', profile.age)
  push('Primary condition', profile.primary_condition)
  const loc = (profile.location ?? {}) as Record<string, unknown>
  push('Location', [loc.city, loc.state].filter(Boolean).join(', '))

  const listCount = (key: string) =>
    Array.isArray(profile[key]) ? (profile[key] as unknown[]).length : 0

  return (
    <section className="rounded-xl border border-slate-200 bg-white p-6">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-navy">What we extracted</h3>
        <span
          className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${result.model_available ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-500'}`}
        >
          {result.model_available ? 'AI extraction on' : 'AI extraction unavailable'}
        </span>
      </div>
      {facts.length === 0 ? (
        <p className="mt-2 text-sm text-slate-500">
          No structured facts were extracted. Matching uses your note text
          directly.
        </p>
      ) : (
        <dl className="mt-3 grid grid-cols-2 gap-x-6 gap-y-2 text-sm sm:grid-cols-3">
          {facts.map((f) => (
            <div key={f.label}>
              <dt className="text-slate-400">{f.label}</dt>
              <dd className="font-medium text-navy">{f.value}</dd>
            </div>
          ))}
        </dl>
      )}
      <p className="mt-3 text-xs text-slate-400">
        {listCount('medications')} medication(s), {listCount('conditions')}{' '}
        condition(s), {listCount('symptoms')} symptom(s) detected. We never
        invent facts that are not in your records.
      </p>
    </section>
  )
}

function MatchedTrials({ result }: { result: MatchResponse }) {
  return (
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
                  {[r.trial?.phase, r.trial?.status].filter(Boolean).join(' · ')}
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
        determination. Trials are real recruiting studies; verify with the study
        team.
      </p>
    </section>
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
