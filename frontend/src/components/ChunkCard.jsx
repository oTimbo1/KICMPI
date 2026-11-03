import { useState } from 'react'

// Retrieved chunk card (PLAN v1.1): the header row is always visible —
// expand toggle, rank, score bar, page chip and the source file. The source
// file is clickable: it opens the ORIGINAL uploaded PDF (served by
// GET /api/documents/{doc_id}/file) in a new tab. The full chunk content is
// collapsed by default and revealed with the round arrow button, so long
// chunks don't force a lot of scrolling.
export default function ChunkCard({ chunk, rank }) {
  const [expanded, setExpanded] = useState(false)
  const pct = Math.round(Math.max(0, Math.min(1, chunk.score)) * 100)
  const fileUrl = chunk.doc_id ? `/api/documents/${chunk.doc_id}/file` : null

  return (
    <article className="rounded-lg border border-kicmpi-line bg-white shadow-sm">
      <div className="flex flex-wrap items-center gap-x-4 gap-y-2 p-4">
        <button
          type="button"
          onClick={() => setExpanded((e) => !e)}
          aria-expanded={expanded}
          title={expanded ? 'Chunk inklappen' : 'Chunk uitklappen'}
          className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full border border-kicmpi-line text-kicmpi-slate transition-colors hover:border-kicmpi-blue hover:text-kicmpi-blue"
        >
          <svg
            viewBox="0 0 16 16"
            className={`h-3.5 w-3.5 transition-transform duration-200 ${expanded ? 'rotate-180' : ''}`}
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <path d="M4 6l4 4 4-4" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </button>

        <span className="text-xs font-bold text-kicmpi-muted">#{rank}</span>

        <div className="flex items-center gap-2" title={`Relevantie-score ${chunk.score.toFixed(2)} (cosine)`}>
          <div className="h-2 w-24 overflow-hidden rounded-full bg-kicmpi-line">
            <div className="h-full bg-kicmpi-blue" style={{ width: `${pct}%` }} />
          </div>
          <span className="text-sm font-semibold text-kicmpi-ink">{chunk.score.toFixed(2)}</span>
        </div>

        {chunk.page > 0 && (
          <span className="rounded-full bg-kicmpi-navy px-2.5 py-0.5 text-xs font-bold text-white">
            p. {chunk.page}
          </span>
        )}

        {fileUrl ? (
          <a
            href={fileUrl}
            target="_blank"
            rel="noreferrer"
            title="Open het originele PDF-bestand in een nieuw tabblad"
            className="max-w-[50%] truncate text-sm font-semibold text-kicmpi-magenta underline-offset-2 hover:underline"
          >
            {chunk.source}
          </a>
        ) : (
          <span className="max-w-[50%] truncate text-sm font-semibold text-kicmpi-magenta">{chunk.source}</span>
        )}
      </div>

      {expanded && (
        <div className="border-t border-kicmpi-line px-4 pb-4 pt-3">
          <p className="whitespace-pre-wrap text-sm leading-relaxed text-kicmpi-slate">{chunk.text}</p>
        </div>
      )}
    </article>
  )
}
