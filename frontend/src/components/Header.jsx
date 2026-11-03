// Sticky white header: logo left, tabs + status dots right (PLAN §6).
export default function Header({ tabs, active, onSelect, status }) {
  return (
    <header className="sticky top-0 z-20 border-b border-kicmpi-line bg-white shadow-sm">
      <div className="mx-auto flex h-20 max-w-5xl flex-wrap items-center justify-between gap-x-6 gap-y-2 px-4 sm:px-6">
        <img src="/kicmpi-logo.svg" alt="KicMPi" className="h-12 w-auto shrink-0" />
        <div className="flex flex-wrap items-center justify-end gap-x-5 gap-y-2">
          <nav className="flex items-center gap-4 sm:gap-6" aria-label="Hoofdmenu">
            {tabs.map((t) => (
              <button
                key={t.id}
                type="button"
                onClick={() => onSelect(t.id)}
                className={`font-semibold transition-colors duration-500 ${
                  active === t.id
                    ? 'text-kicmpi-magenta'
                    : 'text-kicmpi-ink hover:text-kicmpi-magenta'
                }`}
              >
                {t.label}
              </button>
            ))}
          </nav>
          <StatusDots status={status} />
        </div>
      </div>
    </header>
  )
}

function StatusDots({ status }) {
  if (!status) {
    return <span className="text-xs text-kicmpi-muted">Status laden…</span>
  }
  const items = [
    { label: 'Embeddings', ok: status.embedding?.ok },
    { label: 'Samenvatting', ok: status.summary?.ok },
    { label: 'Qdrant', ok: status.qdrant?.ok },
  ]
  return (
    <div className="flex items-center gap-3">
      {status.mock_mode && (
        <span
          className="rounded-full border border-amber-300 bg-amber-100 px-2.5 py-0.5 text-[11px] font-semibold uppercase tracking-wide text-amber-800"
          title="Demo-modus: deterministische mock-embeddings (alleen voor proefdraaien)"
        >
          demo-modus
        </span>
      )}
      {items.map((it) => (
        <span
          key={it.label}
          className="flex items-center gap-1.5 text-xs text-kicmpi-slate"
          title={`${it.label}: ${it.ok ? 'verbonden' : 'niet bereikbaar'}`}
        >
          <span
            className={`inline-block h-2.5 w-2.5 rounded-full ${
              it.ok ? 'bg-green-500' : 'bg-red-500'
            }`}
          />
          <span className="hidden md:inline">{it.label}</span>
        </span>
      ))}
    </div>
  )
}
