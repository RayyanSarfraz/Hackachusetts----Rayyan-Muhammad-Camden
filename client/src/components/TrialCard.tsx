import type { RankedTrial } from '../types/domain'
import { Accordion } from './ui/Accordion'
import { StatusBadge } from './ui/StatusBadge'

function CountPill({
  label,
  count,
  tone,
}: {
  label: string
  count: number
  tone: 'green' | 'gray' | 'amber'
}) {
  const toneClass =
    tone === 'green'
      ? 'bg-emerald-50 text-emerald-700 ring-emerald-600/20'
      : tone === 'amber'
        ? 'bg-amber-50 text-amber-700 ring-amber-600/20'
        : 'bg-slate-100 text-slate-600 ring-slate-500/20'
  return (
    <div
      className={`flex flex-col items-center rounded-lg px-3 py-1.5 ring-1 ring-inset ${toneClass}`}
    >
      <span className="text-lg font-bold leading-none">{count}</span>
      <span className="mt-0.5 text-[11px] font-medium">{label}</span>
    </div>
  )
}

export function TrialCard({
  ranked,
  highlightFact,
}: {
  ranked: RankedTrial
  /** Fact key most recently changed, used to highlight affected rows. */
  highlightFact?: string | null
}) {
  const { trial, summary, rank, withinTravelPreference, clinicalScore, rankExplanation } =
    ranked

  return (
    <article className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-card">
      <div className="p-5">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <span className="inline-flex h-7 w-7 items-center justify-center rounded-full bg-navy text-xs font-bold text-white">
                {rank}
              </span>
              <h3 className="text-base font-bold text-navy">{trial.name}</h3>
            </div>
            <div className="mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-1 text-sm text-slate-600">
              <span className="inline-flex items-center gap-1 rounded-md bg-slate-100 px-2 py-0.5 text-xs font-semibold text-slate-700">
                {trial.id}
              </span>
              <span>📍 {trial.location}</span>
              <span className="text-slate-400">·</span>
              <span>
                {trial.distance.miles} mi{' '}
                <span className="text-xs text-slate-400">(mock distance)</span>
              </span>
            </div>
          </div>
          <div className="flex gap-2">
            <CountPill label="Supported" count={summary.supported} tone="green" />
            <CountPill label="Unknown" count={summary.unknown} tone="gray" />
            <CountPill
              label="Conflict"
              count={summary.potentialConflict}
              tone="amber"
            />
          </div>
        </div>

        <div className="mt-4 rounded-xl bg-slate-50 p-3 text-sm text-slate-700">
          <p className="font-semibold text-navy">Preliminary screening assessment</p>
          <p className="mt-1">
            {summary.potentialConflict > 0
              ? 'One or more criteria show a potential conflict. This is a screening signal only, not an eligibility determination.'
              : summary.unknown > 0
                ? 'Some criteria are still unknown. Answer the Next Best Question to clarify them. No eligibility determination is implied.'
                : 'All assessed criteria are currently supported by documented facts. This is a screening signal only, not an eligibility determination.'}
          </p>
          <p className="mt-2 text-xs text-slate-500">
            Clinical compatibility score: <strong>{clinicalScore}</strong> ·{' '}
            {rankExplanation}
          </p>
          {!withinTravelPreference && (
            <p className="mt-1 text-xs font-medium text-amber-700">
              Outside your current travel preference — still shown, ranked lower.
            </p>
          )}
        </div>

        <div className="mt-4">
          <Accordion title="View eligibility evidence">
            <ul className="space-y-3">
              {trial.criteria.map((criterion) => {
                const assessment = summary.assessments.find(
                  (a) => a.criterionId === criterion.id,
                )!
                const highlighted =
                  highlightFact && criterion.dependsOn.includes(highlightFact as never)
                return (
                  <li
                    key={criterion.id}
                    className={`rounded-lg border p-3 ${
                      highlighted
                        ? 'border-teal bg-teal/5 ring-1 ring-teal/30'
                        : 'border-slate-200'
                    }`}
                  >
                    <div className="flex flex-wrap items-start justify-between gap-2">
                      <p className="max-w-xl text-sm text-navy">
                        <span className="mr-1.5 inline-block rounded bg-slate-100 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-slate-500">
                          {criterion.category}
                        </span>
                        {criterion.text}
                      </p>
                      <StatusBadge status={assessment.status} />
                    </div>
                    <p className="mt-2 text-xs text-slate-600">
                      {assessment.explanation}
                    </p>
                    {assessment.patientEvidence && (
                      <p className="mt-1 text-xs text-slate-500">
                        Patient fact used:{' '}
                        <span className="font-medium">
                          {assessment.patientEvidence}
                        </span>
                      </p>
                    )}
                    <p className="mt-1 text-[11px] text-slate-400">
                      Source: {trial.sourceLabel}
                    </p>
                  </li>
                )
              })}
            </ul>
          </Accordion>
        </div>
      </div>
    </article>
  )
}
