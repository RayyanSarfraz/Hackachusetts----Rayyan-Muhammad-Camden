import { useMemo, useRef, useState } from 'react'
import { useApp } from '../state/AppContext'
import { api } from '../api/adapter'
import { combinedNotes } from '../state/store'
import type { IntakeDocument } from '../types/domain'
import { loadPdf, extractPdfText } from '../lib/pdf'
import {
  kindFromFilename,
  csvToText,
  jsonToText,
  xmlToText,
} from '../lib/normalize'
import { DocumentTray } from './intake/DocumentTray'
import { DocumentPreview } from './intake/DocumentPreview'

const ACCEPT = '.pdf,.txt,.csv,.json,.xml'

function newId(): string {
  return `doc_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 7)}`
}

export function PatientIntake() {
  const { state, dispatch } = useApp()
  const [busy, setBusy] = useState(false)
  const [fileError, setFileError] = useState<string | null>(null)
  const [draft, setDraft] = useState('')
  const [dragging, setDragging] = useState(false)

  const fileInputRef = useRef<HTMLInputElement>(null)
  // Track drag enter/leave depth so crossing onto child elements doesn't flicker
  // or prematurely clear the drag highlight.
  const dragDepth = useRef(0)

  const activeDoc = useMemo(
    () => state.documents.find((d) => d.id === state.activeDocId) ?? null,
    [state.documents, state.activeDocId],
  )

  const includedText = useMemo(
    () => combinedNotes(state.documents),
    [state.documents],
  )
  const includedCount = state.documents.filter((d) => d.included).length
  const canAnalyze = includedText.trim().length > 0 && !busy

  async function analyze(notes: string) {
    setBusy(true)
    try {
      const profile = await api.extractFacts(notes)
      dispatch({ type: 'SET_PROFILE', profile })
    } finally {
      setBusy(false)
    }
  }

  function addPastedText() {
    const text = draft.trim()
    if (text.length === 0) return
    const n = state.documents.filter((d) => d.kind === 'paste').length + 1
    dispatch({
      type: 'ADD_DOCUMENT',
      document: {
        id: newId(),
        name: `Pasted notes ${n}`,
        kind: 'paste',
        text,
        included: true,
        loading: false,
      },
    })
    setDraft('')
  }

  /** Process a list of dropped / selected files, one by one. */
  async function handleFiles(files: File[]) {
    setFileError(null)
    const rejected: string[] = []

    for (const file of files) {
      const kind = kindFromFilename(file.name)
      if (!kind) {
        rejected.push(file.name)
        continue
      }

      if (kind === 'pdf') {
        await addPdf(file)
        continue
      }

      // Text-based formats: read as text, then normalize per format.
      const raw = await file.text()
      let text = raw
      let patch: Partial<IntakeDocument> = {}
      try {
        if (kind === 'csv') {
          const n = csvToText(raw)
          text = n.text
          patch = { rowCount: n.meta.rows, columnCount: n.meta.columns }
        } else if (kind === 'json') {
          const n = jsonToText(raw)
          text = n.text
          patch = { resourceCount: n.meta.resources }
        } else if (kind === 'xml') {
          const n = xmlToText(raw)
          text = n.text
          patch = { resourceCount: n.meta.resources }
        }
      } catch (err) {
        dispatch({
          type: 'ADD_DOCUMENT',
          document: {
            id: newId(),
            name: file.name,
            kind,
            text: '',
            raw,
            included: false,
            loading: false,
            error: err instanceof Error ? err.message : 'Could not read this file.',
          },
        })
        continue
      }

      dispatch({
        type: 'ADD_DOCUMENT',
        document: {
          id: newId(),
          name: file.name,
          kind,
          text,
          raw,
          included: true,
          loading: false,
          ...patch,
        },
      })
    }

    if (rejected.length > 0) {
      setFileError(
        `Unsupported file${rejected.length > 1 ? 's' : ''}: ${rejected.join(', ')}. Supported: PDF, TXT, CSV, JSON, XML.`,
      )
    }
  }

  async function addPdf(file: File) {
    const id = newId()
    const bytes = await file.arrayBuffer()
    dispatch({
      type: 'ADD_DOCUMENT',
      document: {
        id,
        name: file.name,
        kind: 'pdf',
        text: '',
        included: true,
        loading: true,
        pdfBytes: bytes,
      },
    })
    try {
      const doc = await loadPdf(bytes)
      const { text, pageCount } = await extractPdfText(doc)
      void doc.destroy()
      dispatch({
        type: 'UPDATE_DOCUMENT',
        id,
        patch: { text, pageCount, loading: false },
      })
    } catch (err) {
      dispatch({
        type: 'UPDATE_DOCUMENT',
        id,
        patch: {
          loading: false,
          error: err instanceof Error ? err.message : 'Could not read this PDF.',
        },
      })
    }
  }

  function onInputChange(e: React.ChangeEvent<HTMLInputElement>) {
    const files = Array.from(e.target.files ?? [])
    if (fileInputRef.current) fileInputRef.current.value = ''
    void handleFiles(files)
  }

  function onDrop(e: React.DragEvent) {
    e.preventDefault()
    dragDepth.current = 0
    setDragging(false)
    const files = Array.from(e.dataTransfer.files ?? [])
    void handleFiles(files)
  }

  function onDragEnter(e: React.DragEvent) {
    e.preventDefault()
    dragDepth.current += 1
    setDragging(true)
  }

  function onDragLeave(e: React.DragEvent) {
    e.preventDefault()
    dragDepth.current = Math.max(0, dragDepth.current - 1)
    if (dragDepth.current === 0) setDragging(false)
  }

  return (
    <section
      aria-labelledby="intake-heading"
      className="rounded-2xl border border-slate-200 bg-white p-6 shadow-card"
    >
      <div className="mb-5">
        <h2 id="intake-heading" className="text-xl font-bold text-navy">
          Add your health records
        </h2>
        <p className="mt-1 max-w-2xl text-sm text-slate-600">
          Upload documents from your patient portal or health app, or paste
          notes. We read them privately in your browser to find matching trials
          — nothing is uploaded until you choose to run a match.
        </p>
      </div>

      {/* Unified drop zone — a real <label> so the native file picker and its
          accept/multiple semantics are announced by assistive tech, and the
          hidden input handles both click and keyboard activation natively. */}
      <label
        onDragOver={(e) => e.preventDefault()}
        onDragEnter={onDragEnter}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
        className={`focus-within:ring-2 focus-within:ring-teal focus-within:ring-offset-2 flex cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed p-8 text-center transition ${
          dragging
            ? 'border-teal bg-teal/5'
            : 'border-slate-300 bg-slate-50/60 hover:border-slate-400'
        }`}
      >
        <span className="flex h-11 w-11 items-center justify-center rounded-full bg-teal/10">
          <svg
            viewBox="0 0 24 24"
            className="h-5 w-5 text-teal-dark"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
          >
            <path d="M12 16V4M7 9l5-5 5 5" />
            <path d="M5 16v2a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-2" />
          </svg>
        </span>
        <span className="mt-3 text-sm font-semibold text-navy">
          Drag &amp; drop files here, or click to browse
        </span>
        <span className="mt-1 text-xs text-slate-500">
          You can add several files at once
        </span>
        <input
          ref={fileInputRef}
          type="file"
          accept={ACCEPT}
          multiple
          onChange={onInputChange}
          aria-label="Upload records (PDF, TXT, CSV, JSON, or XML). Multiple files allowed."
          className="sr-only"
        />
      </label>

      {/* Supported format chips */}
      <div className="mt-3 flex flex-wrap items-center justify-center gap-2">
        <span className="text-xs text-slate-400">Supported formats</span>
        <FormatChip label="PDF" className="bg-rose-100 text-rose-700" />
        <FormatChip label="TXT" className="bg-sky-100 text-sky-700" />
        <FormatChip label="CSV" className="bg-emerald-100 text-emerald-700" />
        <FormatChip label="JSON" className="bg-amber-100 text-amber-700" />
        <FormatChip label="XML" className="bg-violet-100 text-violet-700" />
      </div>
      <p className="mt-1.5 text-center text-xs text-slate-400">
        Includes Apple Health &amp; Google Health exports (XML / JSON) and FHIR
        bundles
      </p>

      {fileError && (
        <p role="alert" className="mt-3 text-center text-sm text-red-600">
          {fileError}
        </p>
      )}

      {/* Paste text */}
      <details className="mt-4 rounded-xl border border-slate-200 bg-slate-50/60">
        <summary className="focus-ring cursor-pointer select-none px-4 py-3 text-sm font-medium text-navy">
          Or paste notes as text
        </summary>
        <div className="px-4 pb-4">
          <textarea
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            rows={5}
            placeholder="Paste notes here…"
            className="focus-ring w-full resize-y rounded-xl border border-slate-300 bg-white p-3 font-mono text-sm text-navy placeholder:text-slate-400"
          />
          <button
            type="button"
            onClick={addPastedText}
            disabled={draft.trim().length === 0}
            className="focus-ring mt-2 inline-flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-navy hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
          >
            + Add text document
          </button>
        </div>
      </details>

      {/* Two-pane: document tray + preview */}
      <div className="mt-5 grid gap-5 lg:grid-cols-[minmax(0,320px)_minmax(0,1fr)]">
        <div>
          <div className="mb-2 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-navy">
              Your documents{' '}
              <span className="font-normal text-slate-400">
                ({state.documents.length})
              </span>
            </h3>
            {state.documents.length > 0 && (
              <span className="text-xs text-slate-500">
                {includedCount} included
              </span>
            )}
          </div>
          <DocumentTray
            documents={state.documents}
            activeId={state.activeDocId}
            onSelect={(id) => dispatch({ type: 'SELECT_DOCUMENT', id })}
            onToggleIncluded={(id) =>
              dispatch({ type: 'TOGGLE_DOCUMENT_INCLUDED', id })
            }
            onRemove={(id) => dispatch({ type: 'REMOVE_DOCUMENT', id })}
          />
        </div>

        <div className="min-h-[320px]">
          <h3 className="sr-only">Document preview</h3>
          <DocumentPreview doc={activeDoc} />
        </div>
      </div>

      {/* Analyze bar */}
      <div className="mt-5 flex flex-wrap items-center gap-3 border-t border-slate-100 pt-5">
        <button
          type="button"
          onClick={() => void analyze(includedText)}
          disabled={!canAnalyze}
          className="focus-ring inline-flex items-center gap-2 rounded-lg bg-navy px-5 py-2.5 text-sm font-semibold text-white hover:bg-navy-light disabled:cursor-not-allowed disabled:opacity-50"
        >
          {busy
            ? 'Analyzing…'
            : `Analyze ${includedCount > 0 ? `${includedCount} record${includedCount === 1 ? '' : 's'}` : 'records'}`}
        </button>

        {!canAnalyze && !busy && (
          <span className="text-sm text-slate-500">
            Add at least one included document to analyze.
          </span>
        )}

        {state.analyzed && (
          <span className="text-sm font-medium text-emerald-700">
            Information extracted — review it below.
          </span>
        )}
      </div>

      <p className="mt-4 rounded-lg bg-slate-50 px-3 py-2 text-xs text-slate-500 ring-1 ring-inset ring-slate-200">
        Every file is converted to plain text locally and read by a transparent,
        deterministic parser. Missing information is never treated as a negative
        finding. This is a research and decision-support tool, not a clinical
        diagnosis.
      </p>
    </section>
  )
}

function FormatChip({ label, className }: { label: string; className: string }) {
  return (
    <span
      className={`rounded-full px-2.5 py-0.5 text-[11px] font-bold uppercase tracking-wide ${className}`}
    >
      {label}
    </span>
  )
}
