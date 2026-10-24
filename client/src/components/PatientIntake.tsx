import { useRef, useState } from 'react'
import { useApp } from '../state/AppContext'
import { api } from '../api/adapter'
import { DEMO_PATIENT_NOTES } from '../data/demoPatient'

export function PatientIntake() {
  const { state, dispatch } = useApp()
  const [busy, setBusy] = useState(false)
  const [fileError, setFileError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  async function analyze(notes: string) {
    setBusy(true)
    try {
      // extractFacts is the local, deterministic parser via the API adapter.
      const profile = await api.extractFacts(notes)
      dispatch({ type: 'SET_PROFILE', profile })
    } finally {
      setBusy(false)
    }
  }

  function loadDemo() {
    dispatch({ type: 'SET_DRAFT_NOTES', notes: DEMO_PATIENT_NOTES })
    void analyze(DEMO_PATIENT_NOTES)
  }

  async function onFile(e: React.ChangeEvent<HTMLInputElement>) {
    setFileError(null)
    const file = e.target.files?.[0]
    if (!file) return
    if (!file.name.toLowerCase().endsWith('.txt')) {
      setFileError('Please upload a .txt file with fictional notes.')
      return
    }
    // Read locally in the browser — notes are never transmitted anywhere.
    const text = await file.text()
    dispatch({ type: 'SET_DRAFT_NOTES', notes: text })
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  return (
    <section
      aria-labelledby="intake-heading"
      className="rounded-2xl border border-slate-200 bg-white p-6 shadow-card"
    >
      <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 id="intake-heading" className="text-xl font-bold text-navy">
            Patient intake
          </h2>
          <p className="mt-1 text-sm text-slate-600">
            Paste or upload <strong>fictional</strong> medical notes, then analyze.
            Notes are parsed locally in your browser and never uploaded.
          </p>
        </div>
        <button
          type="button"
          onClick={loadDemo}
          disabled={busy}
          className="focus-ring inline-flex items-center gap-2 rounded-lg border border-teal bg-teal/5 px-4 py-2 text-sm font-semibold text-teal-dark hover:bg-teal/10 disabled:opacity-50"
        >
          Load Demo Patient
        </button>
      </div>

      <label htmlFor="notes" className="mb-1.5 block text-sm font-medium text-navy">
        Medical notes (fictional only)
      </label>
      <textarea
        id="notes"
        value={state.draftNotes}
        onChange={(e) => dispatch({ type: 'SET_DRAFT_NOTES', notes: e.target.value })}
        rows={10}
        placeholder="Paste fictional patient notes here, or load the demo patient…"
        className="focus-ring w-full resize-y rounded-xl border border-slate-300 bg-slate-50 p-3 font-mono text-sm text-navy placeholder:text-slate-400"
      />

      <div className="mt-4 flex flex-wrap items-center gap-3">
        <button
          type="button"
          onClick={() => void analyze(state.draftNotes)}
          disabled={busy || state.draftNotes.trim().length === 0}
          className="focus-ring inline-flex items-center gap-2 rounded-lg bg-navy px-5 py-2.5 text-sm font-semibold text-white hover:bg-navy-light disabled:cursor-not-allowed disabled:opacity-50"
        >
          {busy ? 'Analyzing…' : 'Analyze Notes'}
        </button>

        <label className="focus-ring inline-flex cursor-pointer items-center gap-2 rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm font-medium text-navy hover:bg-slate-50">
          Upload .txt file
          <input
            ref={fileInputRef}
            type="file"
            accept=".txt,text/plain"
            onChange={onFile}
            className="sr-only"
          />
        </label>

        {state.analyzed && (
          <span className="text-sm font-medium text-emerald-700">
            Facts extracted — review them below.
          </span>
        )}
      </div>

      {fileError && (
        <p role="alert" className="mt-2 text-sm text-red-600">
          {fileError}
        </p>
      )}

      <p className="mt-4 rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-800 ring-1 ring-inset ring-amber-200">
        Honest extraction: this demo uses a small deterministic local parser. It
        does not call an LLM or backend, and it never marks missing information
        as a negative finding.
      </p>
    </section>
  )
}
