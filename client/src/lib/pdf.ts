import type { PDFDocumentProxy } from 'pdfjs-dist'

/**
 * Client-side PDF utilities.
 *
 * Everything here runs in the browser via pdf.js. PDFs are read with a local
 * FileReader and parsed in a web worker — nothing is uploaded, which keeps the
 * demo's privacy promise (no patient data leaves the browser) intact.
 *
 * pdf.js is heavy (~1.3 MB), so the library is imported dynamically the first
 * time it's needed. This keeps it out of the initial app bundle; it only loads
 * once a user actually works with a PDF.
 */

type PdfJsModule = typeof import('pdfjs-dist')

let pdfjsPromise: Promise<PdfJsModule> | null = null

/** Load (once) and configure the pdf.js module with its bundled worker. */
async function getPdfjs(): Promise<PdfJsModule> {
  if (!pdfjsPromise) {
    pdfjsPromise = (async () => {
      const pdfjs = await import('pdfjs-dist')
      const workerSrc = (await import('pdfjs-dist/build/pdf.worker.min.mjs?url'))
        .default
      pdfjs.GlobalWorkerOptions.workerSrc = workerSrc
      return pdfjs
    })()
  }
  return pdfjsPromise
}

export interface PdfTextResult {
  /** Plain text extracted from every page, joined with blank lines. */
  text: string
  /** Number of pages in the document. */
  pageCount: number
}

/** Load a PDF document from raw bytes. Caller owns the ArrayBuffer. */
export async function loadPdf(data: ArrayBuffer): Promise<PDFDocumentProxy> {
  const pdfjs = await getPdfjs()
  // pdf.js transfers (detaches) the buffer, so hand it a copy to keep the
  // caller's original bytes usable for later re-reads.
  const task = pdfjs.getDocument({ data: data.slice(0) })
  return task.promise
}

/** Extract the full text of an already-loaded PDF. */
export async function extractPdfText(
  doc: PDFDocumentProxy,
): Promise<PdfTextResult> {
  const pages: string[] = []
  for (let n = 1; n <= doc.numPages; n++) {
    const page = await doc.getPage(n)
    const content = await page.getTextContent()
    const pageText = content.items
      .map((item) => ('str' in item ? item.str : ''))
      .join(' ')
      // Collapse the runs of spaces pdf.js emits between text fragments.
      .replace(/[ \t]+/g, ' ')
      .trim()
    pages.push(pageText)
    page.cleanup()
  }
  return { text: pages.join('\n\n'), pageCount: doc.numPages }
}

/** A render in progress, with a handle to cancel it. */
export interface PdfRenderHandle {
  /** Resolves when the page finishes rendering (or rejects on error/cancel). */
  promise: Promise<void>
  /** Abort the in-flight render (safe to call after it has finished). */
  cancel(): void
}

/**
 * Render a single page of a PDF onto a canvas, scaled to fit `targetWidth`.
 *
 * Returns a handle so callers can cancel an in-flight render before starting a
 * new one on the same canvas — pdf.js throws if two renders overlap on one
 * canvas, which happens on rapid page switches.
 */
export function renderPdfPage(
  doc: PDFDocumentProxy,
  pageNumber: number,
  canvas: HTMLCanvasElement,
  targetWidth: number,
): PdfRenderHandle {
  let renderTask: { cancel: () => void } | null = null
  let cancelled = false

  const promise = (async () => {
    const page = await doc.getPage(pageNumber)
    if (cancelled) {
      page.cleanup()
      return
    }
    const unscaled = page.getViewport({ scale: 1 })
    const scale = targetWidth / unscaled.width
    const viewport = page.getViewport({ scale })

    const ctx = canvas.getContext('2d')
    if (!ctx) throw new Error('Could not get 2D canvas context')

    // Account for high-DPI screens for a crisp render.
    const dpr = Math.min(window.devicePixelRatio || 1, 2)
    canvas.width = Math.floor(viewport.width * dpr)
    canvas.height = Math.floor(viewport.height * dpr)
    canvas.style.width = `${Math.floor(viewport.width)}px`
    canvas.style.height = `${Math.floor(viewport.height)}px`
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0)

    const task = page.render({ canvasContext: ctx, viewport })
    renderTask = task
    try {
      await task.promise
    } finally {
      page.cleanup()
    }
  })()

  return {
    promise,
    cancel() {
      cancelled = true
      renderTask?.cancel()
    },
  }
}
