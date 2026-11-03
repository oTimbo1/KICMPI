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
  // Qdrant dashboard: explicit override (status/settings) or derived from the
  // app's own host — the dashboard is published on the same host, port 6333.
  const qdrantDashboardUrl =
    status.qdrant_dashboard_url || `http://${window.location.hostname}:6333/dashboard`
  const items = [
    { label: 'Embeddings', ok: status.embedding?.ok },
    { label: 'Samenvatting', ok: status.summary?.ok },
    {
      label: 'Qdrant',
      ok: status.qdrant?.ok,
      href: qdrantDashboardUrl,
      title: 'Open de Qdrant-dashboard in een nieuw tabblad (vectoren, payloads, chunks)',
    },
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
      {items.map((it) => {
        const dot = (
          <span
            className={`inline-block h-2.5 w-2.5 rounded-full ${
              it.ok ? 'bg-green-500' : 'bg-red-500'
            }`}
          />
        )
        const label = (
          <span className="hidden md:inline">{it.label}</span>
        )
        return it.href ? (
          <a
            key={it.label}
            href={it.href}
            target="_blank"
            rel="noopener noreferrer"
            className="flex cursor-pointer items-center gap-1.5 text-xs text-kicmpi-slate hover:text-kicmpi-blue"
            title={it.title}
          >
            {dot}
            <span className="hidden underline-offset-2 hover:underline md:inline">{it.label}</span>
          </a>
        ) : (
          <span
            key={it.label}
            className="flex items-center gap-1.5 text-xs text-kicmpi-slate"
            title={`${it.label}: ${it.ok ? 'verbonden' : 'niet bereikbaar'}`}
          >
            {dot}
            {label}
          </span>
        )
      })}
    </div>
  )
}
