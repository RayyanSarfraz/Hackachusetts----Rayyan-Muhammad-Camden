import type { IntakeDocument } from '../../types/domain'
import { PdfPreview } from './PdfPreview'
import { CsvPreview } from './CsvPreview'

/**
 * Preview pane for the active intake document.
 *
 * - PDF  : rendered page-by-page on a canvas.
 * - CSV  : rendered as a table.
 * - JSON : pretty-printed.
 * - XML  : shown as formatted source.
 * - TXT / pasted text : shown as formatted, scrollable monospace text.
 *
 * For every non-text format, the normalized plain text we actually feed the
 * parser / model is available in a collapsible "Normalized text" section, so
 * what the system reads is always transparent.
 */
export function DocumentPreview({ doc }: { doc: IntakeDocument | null }) {
  if (!doc) {
    return (
      <div className="flex h-full min-h-[320px] items-center justify-center rounded-xl border border-dashed border-slate-300 bg-slate-50 p-6 text-center">
        <p className="max-w-xs text-sm text-slate-500">
          Select a document to preview it here, or add one from the panel on the
          left.
        </p>
      </div>
    )
  }

  if (doc.loading) {
    return (
      <div className="flex h-full min-h-[320px] items-center justify-center rounded-xl border border-slate-200 bg-white p-6">
        <p className="text-sm text-slate-500">Reading {doc.name}…</p>
      </div>
    )
  }

  if (doc.error) {
    return (
      <div className="rounded-xl border border-red-200 bg-red-50 p-6">
        <p className="text-sm font-medium text-red-700">
          Couldn’t read {doc.name}
        </p>
        <p className="mt-1 text-sm text-red-600">{doc.error}</p>
      </div>
    )
  }

  return (
    <div className="flex h-full flex-col rounded-xl border border-slate-200 bg-white">
      <div className="flex items-center justify-between gap-2 border-b border-slate-100 px-4 py-3">
        <h3 className="truncate text-sm font-semibold text-navy" title={doc.name}>
          {doc.name}
        </h3>
        {!doc.included && (
          <span className="shrink-0 rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-500">
            Excluded from analysis
          </span>
        )}
      </div>

      <div className="min-h-0 flex-1 overflow-auto p-4">
        {renderBody(doc)}
      </div>
    </div>
  )
}

function renderBody(doc: IntakeDocument) {
  switch (doc.kind) {
    case 'pdf':
      return (
        <>
          {doc.pdfBytes && (
            <PdfPreview bytes={doc.pdfBytes} pageCount={doc.pageCount} />
          )}
          <NormalizedText label="Extracted text" text={doc.text} />
        </>
      )

    case 'csv':
      return (
        <>
          <CsvPreview raw={doc.raw ?? ''} />
          <NormalizedText label="Normalized text (fed to the model)" text={doc.text} />
        </>
      )

    case 'json':
      return (
        <>
          <CodeBlock text={prettyJson(doc.raw ?? doc.text)} />
          <NormalizedText label="Normalized text (fed to the model)" text={doc.text} />
        </>
      )

    case 'xml':
      return (
        <>
          <CodeBlock text={doc.raw ?? doc.text} />
          <NormalizedText label="Normalized text (fed to the model)" text={doc.text} />
        </>
      )

    default:
      // txt / pasted text
      return (
        <pre className="whitespace-pre-wrap break-words font-mono text-sm leading-relaxed text-navy">
          {doc.text.trim().length > 0 ? (
            doc.text
          ) : (
            <span className="text-slate-400">This document is empty.</span>
          )}
        </pre>
      )
  }
}

function CodeBlock({ text }: { text: string }) {
  return (
    <pre className="max-h-[420px] overflow-auto rounded-lg border border-slate-200 bg-slate-50 p-3 font-mono text-xs leading-relaxed text-slate-700">
      {text}
    </pre>
  )
}

function NormalizedText({ label, text }: { label: string; text: string }) {
  if (text.trim().length === 0) return null
  return (
    <details className="mt-4 rounded-lg border border-slate-200 bg-slate-50">
      <summary className="focus-ring cursor-pointer select-none px-3 py-2 text-sm font-medium text-navy">
        {label} ({text.trim().length} chars)
      </summary>
      <pre className="max-h-64 overflow-auto whitespace-pre-wrap px-3 pb-3 font-mono text-xs leading-relaxed text-slate-700">
        {text}
      </pre>
    </details>
  )
}

function prettyJson(raw: string): string {
  try {
    return JSON.stringify(JSON.parse(raw), null, 2)
  } catch {
    return raw
  }
}
