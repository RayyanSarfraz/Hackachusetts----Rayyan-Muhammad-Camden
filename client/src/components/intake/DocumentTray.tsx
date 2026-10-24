import type { IntakeDocument } from '../../types/domain'

const KIND_META: Record<
  IntakeDocument['kind'],
  { label: string; className: string }
> = {
  paste: { label: 'Text', className: 'bg-slate-100 text-slate-600' },
  txt: { label: 'TXT', className: 'bg-sky-100 text-sky-700' },
  pdf: { label: 'PDF', className: 'bg-rose-100 text-rose-700' },
  csv: { label: 'CSV', className: 'bg-emerald-100 text-emerald-700' },
  json: { label: 'JSON', className: 'bg-amber-100 text-amber-700' },
  xml: { label: 'XML', className: 'bg-violet-100 text-violet-700' },
}

/**
 * The document switcher. Lists every intake document as a selectable row so the
 * user can toggle which one is previewed, include/exclude it from analysis, and
 * remove it. Keeps clinical sources explicit and reviewable.
 */
export function DocumentTray({
  documents,
  activeId,
  onSelect,
  onToggleIncluded,
  onRemove,
}: {
  documents: IntakeDocument[]
  activeId: string | null
  onSelect: (id: string) => void
  onToggleIncluded: (id: string) => void
  onRemove: (id: string) => void
}) {
  if (documents.length === 0) {
    return (
      <p className="rounded-lg border border-dashed border-slate-300 bg-slate-50 px-3 py-6 text-center text-sm text-slate-500">
        No documents yet. Add text or upload a .pdf / .txt to get started.
      </p>
    )
  }

  return (
    <ul role="tablist" aria-label="Uploaded documents" className="space-y-2">
      {documents.map((doc) => {
        const active = doc.id === activeId
        const meta = KIND_META[doc.kind]
        return (
          <li key={doc.id}>
            <div
              className={`group flex items-center gap-2 rounded-xl border px-3 py-2 transition ${
                active
                  ? 'border-teal bg-teal/5 ring-1 ring-teal/30'
                  : 'border-slate-200 bg-white hover:border-slate-300'
              }`}
            >
              <input
                type="checkbox"
                checked={doc.included}
                onChange={() => onToggleIncluded(doc.id)}
                aria-label={`Include ${doc.name} in analysis`}
                className="focus-ring h-4 w-4 shrink-0 rounded border-slate-300 text-teal accent-teal"
              />
              <button
                type="button"
                role="tab"
                aria-selected={active}
                onClick={() => onSelect(doc.id)}
                className="focus-ring flex min-w-0 flex-1 items-center gap-2 text-left"
              >
                <span
                  className={`shrink-0 rounded px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wide ${meta.className}`}
                >
                  {meta.label}
                </span>
                <span className="min-w-0 flex-1">
                  <span className="block truncate text-sm font-medium text-navy">
                    {doc.name}
                  </span>
                  <span className="block truncate text-xs text-slate-500">
                    {doc.loading
                      ? 'Extracting text…'
                      : doc.error
                        ? doc.error
                        : documentSummary(doc)}
                  </span>
                </span>
              </button>
              <button
                type="button"
                onClick={() => onRemove(doc.id)}
                aria-label={`Remove ${doc.name}`}
                className="focus-ring shrink-0 rounded-md p-1 text-slate-400 hover:bg-red-50 hover:text-red-600"
              >
                <svg
                  viewBox="0 0 20 20"
                  className="h-4 w-4"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.8"
                  aria-hidden="true"
                >
                  <path
                    strokeLinecap="round"
                    d="M6 6l8 8M14 6l-8 8"
                  />
                </svg>
              </button>
            </div>
          </li>
        )
      })}
    </ul>
  )
}

function documentSummary(doc: IntakeDocument): string {
  const chars = doc.text.trim().length
  switch (doc.kind) {
    case 'pdf':
      return doc.pageCount
        ? `${doc.pageCount} page${doc.pageCount === 1 ? '' : 's'} · ${chars} chars`
        : `${chars} chars`
    case 'csv':
      return `${doc.rowCount ?? 0} rows · ${doc.columnCount ?? 0} cols`
    case 'json':
    case 'xml':
      return doc.resourceCount
        ? `${doc.resourceCount} record${doc.resourceCount === 1 ? '' : 's'} · ${chars} chars`
        : `${chars} chars`
    default: {
      const words = doc.text.trim().split(/\s+/).filter(Boolean).length
      return `${words} word${words === 1 ? '' : 's'} · ${chars} chars`
    }
  }
}
