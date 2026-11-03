// Always-present AI-samenvatting panel (PLAN §6 View 2).
// States: loading (search in flight) · ok (grounded text with [bron, pagina]
// citations) · unconfigured/unavailable/error (neutral box — never hides chunks).
export default function SummaryPanel({ summary, loading }) {
  const s = summary || { status: 'unconfigured' }
  const isOk = s.status === 'ok'

  return (
    <section className="mt-4 rounded-lg border border-kicmpi-line bg-white p-5">
      <h3 className="text-lg font-bold text-kicmpi-blue">AI-samenvatting</h3>

      {loading ? (
        <p className="mt-3 flex items-center gap-2 text-sm text-kicmpi-slate">
          <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-kicmpi-blue border-t-transparent" />
          Samenvatting genereren…
        </p>
      ) : isOk ? (
        <p className="mt-3 whitespace-pre-wrap text-sm leading-relaxed text-kicmpi-ink">{s.text}</p>
      ) : (
        <div className="mt-3 rounded-lg border border-kicmpi-line bg-kicmpi-stripeA px-4 py-3">
          <p className="text-sm text-kicmpi-slate">
            De samenvatting-functie is in deze conceptversie nog niet volledig beschikbaar — de
            opgehaalde chunks hierboven zijn de bron.
          </p>
          <p className="mt-1.5 text-xs text-kicmpi-muted">
            {s.status === 'unconfigured'
              ? 'Model niet verbonden: stel het IP:port in op het tab Instellingen.'
              : `Reden: ${String(s.status).replace(/^error:\s*/, '')}`}
            {s.model ? ` · model: ${s.model}` : ''}
          </p>
        </div>
      )}
    </section>
  )
}
