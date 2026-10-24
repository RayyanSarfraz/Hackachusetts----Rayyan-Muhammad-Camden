import type { WorkflowStep } from '../state/store'

const STEPS: { id: WorkflowStep; label: string }[] = [
  { id: 'intake', label: '1. Patient intake' },
  { id: 'review', label: '2. Review facts' },
  { id: 'matching', label: '3. Match & refine' },
]

const ORDER: WorkflowStep[] = ['intake', 'review', 'matching']

export function WorkflowSteps({ current }: { current: WorkflowStep }) {
  const currentIndex = ORDER.indexOf(current)
  return (
    <nav aria-label="Workflow progress" className="mb-6">
      <ol className="flex flex-wrap items-center gap-2 text-sm">
        {STEPS.map((step, i) => {
          const done = i < currentIndex
          const active = i === currentIndex
          return (
            <li key={step.id} className="flex items-center gap-2">
              <span
                aria-current={active ? 'step' : undefined}
                className={`inline-flex items-center rounded-full px-3 py-1 font-medium ring-1 ring-inset ${
                  active
                    ? 'bg-teal text-white ring-teal'
                    : done
                      ? 'bg-teal/10 text-teal-dark ring-teal/30'
                      : 'bg-white text-slate-500 ring-slate-200'
                }`}
              >
                {step.label}
              </span>
              {i < STEPS.length - 1 && (
                <span className="text-slate-300" aria-hidden="true">
                  →
                </span>
              )}
            </li>
          )
        })}
      </ol>
    </nav>
  )
}
