import type { AssessmentStatus } from '../../types/domain'

const STYLES: Record<AssessmentStatus, { label: string; className: string }> = {
  supported: {
    label: 'Supported',
    className: 'bg-emerald-50 text-emerald-700 ring-emerald-600/20',
  },
  unknown: {
    label: 'Unknown',
    className: 'bg-slate-100 text-slate-600 ring-slate-500/20',
  },
  potential_conflict: {
    label: 'Potential conflict',
    className: 'bg-amber-50 text-amber-700 ring-amber-600/20',
  },
}

export function StatusBadge({
  status,
  className = '',
}: {
  status: AssessmentStatus
  className?: string
}) {
  const s = STYLES[status]
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ring-1 ring-inset ${s.className} ${className}`}
    >
      {s.label}
    </span>
  )
}
