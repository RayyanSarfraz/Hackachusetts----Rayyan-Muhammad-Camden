import { useEffect, useRef, useState } from 'react'
import type { PDFDocumentProxy } from 'pdfjs-dist'
import { loadPdf, renderPdfPage } from '../../lib/pdf'

/**
 * Renders a PDF (from in-memory bytes) onto a canvas with simple page
 * navigation. Loading and rendering happen entirely in the browser via pdf.js.
 */
export function PdfPreview({
  bytes,
  pageCount,
}: {
  bytes: ArrayBuffer
  pageCount?: number
}) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const wrapRef = useRef<HTMLDivElement>(null)
  // The loaded document is kept in STATE (not a ref) so the render effect
  // re-runs the moment the document becomes available. Keeping it in a ref was
  // the cause of the "stuck on Rendering…" bug: the render effect ran before
  // the async load finished, saw no doc, and bailed without ever re-running.
  const [doc, setDoc] = useState<PDFDocumentProxy | null>(null)
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(pageCount ?? 1)
  const [rendering, setRendering] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Load the document whenever the source bytes change.
  useEffect(() => {
    let cancelled = false
    let loaded: PDFDocumentProxy | null = null
    setError(null)
    setPage(1)
    setRendering(true)
    setDoc(null)

    loadPdf(bytes)
      .then((d) => {
        if (cancelled) {
          void d.destroy()
          return
        }
        loaded = d
        setTotal(d.numPages)
        setDoc(d)
      })
      .catch((e: unknown) => {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : 'Failed to load PDF')
          setRendering(false)
        }
      })

    return () => {
      cancelled = true
      void loaded?.destroy()
    }
  }, [bytes])

  // Render the current page whenever the loaded doc or the page changes.
  useEffect(() => {
    if (!doc || !canvasRef.current) return
    let cancelled = false
    setRendering(true)
    const width = Math.min(wrapRef.current?.clientWidth ?? 640, 900)

    const handle = renderPdfPage(doc, page, canvasRef.current, width)
    handle.promise
      .catch((e: unknown) => {
        // Ignore cancellations from rapid page switches / unmounts.
        if (cancelled || isRenderCancelled(e)) return
        setError(e instanceof Error ? e.message : 'Failed to render page')
      })
      .finally(() => {
        if (!cancelled) setRendering(false)
      })

    return () => {
      cancelled = true
      handle.cancel()
    }
  }, [doc, page])

  if (error) {
    return (
      <p role="alert" className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
        Could not preview this PDF: {error}
      </p>
    )
  }

  return (
    <div ref={wrapRef} className="flex flex-col items-center">
      {total > 1 && (
        <div className="mb-3 flex items-center gap-3 text-sm text-slate-600">
          <button
            type="button"
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page <= 1}
            className="focus-ring rounded-md border border-slate-300 bg-white px-2.5 py-1 font-medium text-navy hover:bg-slate-50 disabled:opacity-40"
          >
            ← Prev
          </button>
          <span className="tabular-nums">
            Page {page} of {total}
          </span>
          <button
            type="button"
            onClick={() => setPage((p) => Math.min(total, p + 1))}
            disabled={page >= total}
            className="focus-ring rounded-md border border-slate-300 bg-white px-2.5 py-1 font-medium text-navy hover:bg-slate-50 disabled:opacity-40"
          >
            Next →
          </button>
        </div>
      )}
      <div className="relative w-full overflow-auto rounded-lg border border-slate-200 bg-slate-100 p-3">
        {rendering && (
          <div className="absolute inset-0 z-10 flex items-center justify-center bg-slate-100/60 text-sm text-slate-500">
            Rendering…
          </div>
        )}
        <canvas ref={canvasRef} className="mx-auto block rounded shadow-sm" />
      </div>
    </div>
  )
}

/** pdf.js throws a RenderingCancelledException when a render is aborted. */
function isRenderCancelled(e: unknown): boolean {
  return (
    typeof e === 'object' &&
    e !== null &&
    'name' in e &&
    (e as { name?: string }).name === 'RenderingCancelledException'
  )
}
