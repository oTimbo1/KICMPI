import { useEffect, useState } from 'react'
import ChunkCard from './ChunkCard.jsx'
import SummaryPanel from './SummaryPanel.jsx'
import { listDocuments, search } from '../api/client.js'

export default function SearchView() {
  const [query, setQuery] = useState('')
  const [topK, setTopK] = useState(5)
  const [docFilter, setDocFilter] = useState('')
  const [docs, setDocs] = useState([])
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  // Keep the document filter current (refresh after each search so newly
  // ingested documents show up).
  useEffect(() => {
    listDocuments().then(setDocs).catch(() => {})
  }, [results])

  async function runSearch(e) {
    if (e) e.preventDefault()
    const q = query.trim()
    if (!q || loading) return
    setLoading(true)
    setError(null)
    setResults(null)
    try {
      setResults(await search({ query: q, top_k: topK, doc_id: docFilter || null }))
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-8">
      <section>
        <h2 className="mb-4 text-2xl font-bold text-kicmpi-blue">Zoeken</h2>
        <form onSubmit={runSearch} className="flex flex-col gap-3 sm:flex-row">
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Stel een vraag in het Nederlands, bijv. ‘Hoe werkt het voorbeeldproject?’"
            className="input-pill flex-1 text-base"
          />
          <button type="submit" className="btn-primary" disabled={loading || !query.trim()}>
            {loading ? 'Zoeken…' : 'Zoeken'}
          </button>
        </form>
        <div className="mt-3 flex flex-wrap items-center gap-4 text-sm">
          <label className="flex items-center gap-2 text-kicmpi-slate">
            Top-k
            <select
              value={topK}
              onChange={(e) => setTopK(Number(e.target.value))}
              className="rounded-full border border-kicmpi-line bg-white px-3 py-1.5"
            >
              <option value={3}>3</option>
              <option value={5}>5</option>
              <option value={10}>10</option>
            </select>
          </label>
          <label className="flex items-center gap-2 text-kicmpi-slate">
            Document
            <select
              value={docFilter}
              onChange={(e) => setDocFilter(e.target.value)}
              className="max-w-xs rounded-full border border-kicmpi-line bg-white px-3 py-1.5"
            >
              <option value="">Alles</option>
              {docs.map((d) => (
                <option key={d.doc_id} value={d.doc_id}>
                  {d.filename}
                </option>
              ))}
            </select>
          </label>
        </div>
      </section>

      <section className="rounded-lg bg-kicmpi-stripes p-5 sm:p-6">
        {error && (
          <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-kicmpi-error">
            Zoeken mislukt: {error}
          </div>
        )}

        {!results && !loading && !error && (
          <div className="py-10 text-center">
            <p className="font-semibold text-kicmpi-slate">Nog geen zoekopdracht uitgevoerd</p>
            <p className="mt-1 text-sm text-kicmpi-muted">Typ een vraag en klik op Zoeken.</p>
          </div>
        )}

        {loading && (
          <div className="flex items-center justify-center gap-2 py-10 text-kicmpi-slate">
            <span className="inline-block h-6 w-6 animate-spin rounded-full border-2 border-kicmpi-blue border-t-transparent" />
            Zoeken + samenvatten…
          </div>
        )}

        {results && !loading && (
          <>
            <p className="text-sm font-semibold text-kicmpi-slate">
              {results.chunks.length === 0
                ? 'Geen relevante chunks gevonden. Probeer een andere vraag of een bredere top-k.'
                : `${results.chunks.length} chunks gevonden in ${results.took_ms} ms`}
            </p>
            {/* Summary first — it is based on the chunks listed below it (PLAN v1.1) */}
            <SummaryPanel summary={results.summary} />
            <div className="mt-4 space-y-4">
              {results.chunks.map((c, i) => (
                <ChunkCard key={c.chunk_id || i} chunk={c} rank={i + 1} />
              ))}
            </div>
          </>
        )}
      </section>
    </div>
  )
}
