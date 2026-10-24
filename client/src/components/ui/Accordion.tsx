import { useId, useState, type ReactNode } from 'react'

export function Accordion({
  title,
  children,
  defaultOpen = false,
}: {
  title: ReactNode
  children: ReactNode
  defaultOpen?: boolean
}) {
  const [open, setOpen] = useState(defaultOpen)
  const panelId = useId()
  const buttonId = useId()

  return (
    <div className="rounded-lg border border-slate-200 bg-white">
      <button
        id={buttonId}
        type="button"
        aria-expanded={open}
        aria-controls={panelId}
        onClick={() => setOpen((o) => !o)}
        className="focus-ring flex w-full items-center justify-between gap-3 rounded-lg px-4 py-3 text-left text-sm font-semibold text-navy hover:bg-slate-50"
      >
        <span>{title}</span>
        <svg
          className={`h-4 w-4 shrink-0 text-teal transition-transform ${
            open ? 'rotate-180' : ''
          }`}
          viewBox="0 0 20 20"
          fill="currentColor"
          aria-hidden="true"
        >
          <path
            fillRule="evenodd"
            d="M5.23 7.21a.75.75 0 011.06.02L10 11.168l3.71-3.938a.75.75 0 111.08 1.04l-4.25 4.5a.75.75 0 01-1.08 0l-4.25-4.5a.75.75 0 01.02-1.06z"
            clipRule="evenodd"
          />
        </svg>
      </button>
      {open && (
        <div
          id={panelId}
          role="region"
          aria-labelledby={buttonId}
          className="border-t border-slate-100 px-4 py-3"
        >
          {children}
        </div>
      )}
    </div>
  )
}
