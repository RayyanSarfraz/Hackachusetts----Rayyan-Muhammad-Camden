import { useMemo } from 'react'
import { parseCsv } from '../../lib/normalize'

/** Renders CSV content as a scrollable table, capped to a sensible row limit. */
export function CsvPreview({ raw }: { raw: string }) {
  const { header, rows } = useMemo(() => parseCsv(raw), [raw])
  const MAX_ROWS = 200

  if (header.length === 0) {
    return <p className="text-sm text-slate-400">This CSV is empty.</p>
  }

  const shown = rows.slice(0, MAX_ROWS)

  return (
    <div className="overflow-auto rounded-lg border border-slate-200">
      <table className="min-w-full border-collapse text-sm">
        <thead className="sticky top-0 bg-slate-50">
          <tr>
            {header.map((h, i) => (
              <th
                key={i}
                className="whitespace-nowrap border-b border-slate-200 px-3 py-2 text-left font-semibold text-navy"
              >
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {shown.map((row, r) => (
            <tr key={r} className={r % 2 ? 'bg-slate-50/50' : 'bg-white'}>
              {header.map((_, c) => (
                <td
                  key={c}
                  className="whitespace-nowrap border-b border-slate-100 px-3 py-1.5 text-slate-700"
                >
                  {row[c] ?? ''}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {rows.length > MAX_ROWS && (
        <p className="bg-slate-50 px-3 py-2 text-xs text-slate-500">
          Showing first {MAX_ROWS} of {rows.length} rows.
        </p>
      )}
    </div>
  )
}
