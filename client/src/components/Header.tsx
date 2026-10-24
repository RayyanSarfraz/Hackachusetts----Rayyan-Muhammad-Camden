export function Header({ mode = 'live' }: { mode?: 'live' | 'demo' }) {
  const isDemo = mode === 'demo'
  return (
    <header className="border-b border-slate-200 bg-navy text-white">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-4 sm:px-6">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-teal shadow-card">
            <svg
              className="h-6 w-6 text-white"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M4 12h4l2 5 4-10 2 5h4"
              />
            </svg>
          </div>
          <div>
            <h1 className="text-lg font-bold leading-tight tracking-tight">
              TrialBridge
            </h1>
            <p className="text-xs text-slate-300">
              Clinical trial matching &amp; enrollment navigation
            </p>
          </div>
        </div>
        {isDemo ? (
          <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-400/20 px-3 py-1 text-xs font-semibold text-amber-200 ring-1 ring-inset ring-amber-300/40">
            <span className="h-2 w-2 rounded-full bg-amber-300" aria-hidden="true" />
            Demo Mode — fictional local data
          </span>
        ) : (
          <span className="inline-flex items-center gap-1.5 rounded-full bg-teal/20 px-3 py-1 text-xs font-semibold text-teal-100 ring-1 ring-inset ring-teal-300/40">
            <span className="h-2 w-2 rounded-full bg-teal-300" aria-hidden="true" />
            Live — real recruiting trials
          </span>
        )}
      </div>
    </header>
  )
}
