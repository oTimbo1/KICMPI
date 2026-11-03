// 4-step live pipeline progress: Lezen → Chunken → Embedden → Opgeslagen (PLAN §6 View 1).
const STEPS = ['Lezen', 'Chunken', 'Embedden', 'Opgeslagen']

function stepIndex(doc) {
  switch (doc.status) {
    case 'uploaded':
    case 'parsing':
      return 0
    case 'chunking':
      return 1
    case 'embedding':
      return 2
    case 'stored':
      return 4
    default:
      return -1
  }
}

export default function IngestProgress({ doc }) {
  if (doc.status === 'error') {
    return (
      <p className="mt-2 rounded border border-red-200 bg-red-50 px-2.5 py-1.5 text-xs font-medium text-kicmpi-error">
        {doc.error}
      </p>
    )
  }
  if (doc.status === 'stored') {
    return (
      <p className="mt-1 text-xs text-kicmpi-muted">
        Opgeslagen · {doc.chunks} chunks
      </p>
    )
  }

  const active = stepIndex(doc)
  return (
    <div className="mt-2" title="RAG-pijplijn in actie">
      <div className="flex flex-wrap items-center gap-x-1 gap-y-1">
        {STEPS.map((label, i) => (
          <span key={label} className="flex items-center gap-1">
            <StepDot done={i < active} current={i === active} />
            <span
              className={`text-[11px] ${
                i < active
                  ? 'text-kicmpi-slate'
                  : i === active
                    ? 'font-semibold text-kicmpi-blue'
                    : 'text-kicmpi-muted'
              }`}
            >
              {label}
            </span>
            {i < STEPS.length - 1 && <span className="mx-0.5 text-[10px] text-kicmpi-muted">→</span>}
          </span>
        ))}
      </div>
      <div className="mt-1.5 h-1.5 w-full max-w-xs overflow-hidden rounded-full bg-kicmpi-line">
        <div
          className="h-full bg-kicmpi-blue transition-all duration-500"
          style={{ width: `${doc.progress || 0}%` }}
        />
      </div>
    </div>
  )
}

function StepDot({ done, current }) {
  if (done) {
    return (
      <span className="inline-flex h-4 w-4 items-center justify-center rounded-full bg-kicmpi-blue text-white">
        <svg viewBox="0 0 12 12" className="h-2.5 w-2.5" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M2 6l3 3 5-6" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </span>
    )
  }
  if (current) {
    return <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-kicmpi-blue border-t-transparent" />
  }
  return <span className="inline-block h-4 w-4 rounded-full border-2 border-kicmpi-line" />
}
