import { useCallback, useEffect, useRef, useState } from 'react'
import IngestProgress from './IngestProgress.jsx'
import { deleteDocument, listDocuments, uploadDocument } from '../api/client.js'

// Documents in one of these states are still processing → keep polling.
const ACTIVE_STATUSES = ['uploaded', 'parsing', 'chunking', 'embedding']

function formatDate(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return '—'
  const p = (x) => String(x).padStart(2, '0')
  return `${p(d.getDate())}-${p(d.getMonth() + 1)}-${d.getFullYear()}`
}

export default function DocumentsView() {
  const [docs, setDocs] = useState([])
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [uploadError, setUploadError] = useState(null)
  const [dragOver, setDragOver] = useState(false)
  const inputRef = useRef(null)

  const load = useCallback(async () => {
    try {
      setDocs(await listDocuments())
      setLoadError(null)
    } catch (e) {
      setLoadError(e.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  // Live progress: poll every 1.5 s while any document is being processed.
  const hasActive = docs.some((d) => ACTIVE_STATUSES.includes(d.status))
  useEffect(() => {
    if (!hasActive) return undefined
    const t = setInterval(load, 1500)
    return () => clearInterval(t)
  }, [hasActive, load])

  async function handleFiles(files) {
    const file = files && files[0]
    if (!file) return
    const isPdf = file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf')
    if (!isPdf) {
      setUploadError('Alleen PDF-bestanden worden (nog) ondersteund.')
      return
    }
    setUploadError(null)
    setUploading(true)
    try {
      await uploadDocument(file)
      await load()
    } catch (e) {
      setUploadError(e.message)
    } finally {
      setUploading(false)
      if (inputRef.current) inputRef.current.value = ''
    }
  }

  async function handleDelete(doc) {
    if (!window.confirm(`"${doc.filename}" verwijderen, inclusief alle opgeslagen chunks?`)) return
    try {
      await deleteDocument(doc.doc_id)
      await load()
    } catch (e) {
      setUploadError(e.message)
    }
  }

  return (
    <div className="space-y-8">
      <section>
        <h2 className="mb-4 text-2xl font-bold text-kicmpi-blue">Documenten</h2>
        <div
          role="button"
          tabIndex={0}
          onDragOver={(e) => {
            e.preventDefault()
            setDragOver(true)
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={(e) => {
            e.preventDefault()
            setDragOver(false)
            handleFiles(e.dataTransfer.files)
          }}
          onClick={() => inputRef.current && inputRef.current.click()}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') inputRef.current && inputRef.current.click()
          }}
          className={`cursor-pointer rounded-lg border-2 border-dashed px-6 py-10 text-center transition-colors ${
            dragOver
              ? 'border-kicmpi-blue bg-kicmpi-blue/5'
              : 'border-kicmpi-line bg-white hover:border-kicmpi-blue/60'
          }`}
        >
          <input
            ref={inputRef}
            type="file"
            accept="application/pdf,.pdf"
            className="hidden"
            onChange={(e) => handleFiles(e.target.files)}
          />
          {uploading ? (
            <p className="font-semibold text-kicmpi-slate">Uploaden…</p>
          ) : (
            <p className="text-kicmpi-slate">
              <span className="font-semibold text-kicmpi-blue">Sleep een PDF hierheen</span> of klik om
              te kiezen
              <span className="mt-1 block text-sm text-kicmpi-muted">
                PDF met tekstlaag · max. 25 MB · de RAG-pijplijn start direct
              </span>
            </p>
          )}
        </div>
        {uploadError && (
          <p className="mt-3 rounded-lg border border-red-200 bg-red-50 px-4 py-2.5 text-sm font-medium text-kicmpi-error">
            {uploadError}
          </p>
        )}
      </section>

      <section className="rounded-lg bg-kicmpi-stripes p-5 sm:p-6">
        {loading ? (
          <p className="text-kicmpi-slate">Laden…</p>
        ) : loadError ? (
          <p className="text-sm font-medium text-kicmpi-error">{loadError}</p>
        ) : docs.length === 0 ? (
          <div className="py-8 text-center">
            <p className="font-semibold text-kicmpi-slate">Nog geen documenten</p>
            <p className="mt-1 text-sm text-kicmpi-muted">
              Sleep een PDF hierboven om de RAG-pijplijn te zien draaien.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-kicmpi-line text-xs uppercase tracking-wide text-kicmpi-muted">
                  <th className="py-2 pr-4 font-semibold">Bestandsnaam</th>
                  <th className="py-2 pr-4 font-semibold">Geüpload</th>
                  <th className="py-2 pr-4 font-semibold">Chunks</th>
                  <th className="py-2 pr-4 font-semibold">Status</th>
                  <th className="py-2" />
                </tr>
              </thead>
              <tbody>
                {docs.map((doc) => (
                  <tr key={doc.doc_id} className="border-b border-kicmpi-line/70 align-top">
                    <td className="max-w-xs py-3 pr-4">
                      <a
                        href={`/api/documents/${doc.doc_id}/file`}
                        target="_blank"
                        rel="noreferrer"
                        title="Open het originele PDF-bestand in een nieuw tabblad"
                        className="line-clamp-2 font-medium text-kicmpi-ink underline-offset-2 hover:text-kicmpi-blue hover:underline"
                      >
                        {doc.filename}
                      </a>
                      <IngestProgress doc={doc} />
                    </td>
                    <td className="whitespace-nowrap py-3 pr-4 text-kicmpi-slate">
                      {formatDate(doc.uploaded_at)}
                    </td>
                    <td className="py-3 pr-4 text-kicmpi-slate">{doc.chunks || '—'}</td>
                    <td className="whitespace-nowrap py-3 pr-4">
                      <StatusPill status={doc.status} />
                    </td>
                    <td className="py-3 text-right">
                      <button
                        type="button"
                        onClick={() => handleDelete(doc)}
                        title="Document verwijderen"
                        className="text-kicmpi-muted transition-colors hover:text-kicmpi-error"
                      >
                        <TrashIcon />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  )
}

function StatusPill({ status }) {
  if (status === 'stored') return <Pill cls="bg-kicmpi-blue text-white" label="Bewerkt" />
  if (status === 'error')
    return <Pill cls="border border-red-200 bg-red-50 text-kicmpi-error" label="Fout" />
  return <Pill cls="border border-amber-300 bg-amber-100 text-amber-800" label="Werkt" />
}

function Pill({ cls, label }) {
  return <span className={`inline-block rounded-full px-3 py-1 text-xs font-semibold ${cls}`}>{label}</span>
}

function TrashIcon() {
  return (
    <svg viewBox="0 0 20 20" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="1.5">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M3 5h14M8 5V4a1 1 0 011-1h2a1 1 0 011 1v1m3 0v11a1 1 0 01-1 1H6a1 1 0 01-1-1V5m3 4v5m4-5v5"
      />
    </svg>
  )
}
