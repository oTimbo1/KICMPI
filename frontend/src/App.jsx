import { useCallback, useEffect, useState } from 'react'
import Header from './components/Header.jsx'
import Hero from './components/Hero.jsx'
import DocumentsView from './components/DocumentsView.jsx'
import SearchView from './components/SearchView.jsx'
import SettingsView from './components/SettingsView.jsx'
import { getStatus } from './api/client.js'

const TABS = [
  { id: 'documenten', label: 'Documenten' },
  { id: 'zoeken', label: 'Zoeken' },
  { id: 'instellingen', label: 'Instellingen' },
]

const OFFLINE_STATUS = {
  app: 'ok',
  mock_mode: false,
  qdrant: { ok: false },
  embedding: { ok: false },
  summary: { ok: false },
}

export default function App() {
  const [tab, setTab] = useState('documenten')
  const [status, setStatus] = useState(null)

  // Dots refresh on mount, on every view switch, and after settings saves.
  const refreshStatus = useCallback(async () => {
    try {
      setStatus(await getStatus())
    } catch {
      setStatus(OFFLINE_STATUS)
    }
  }, [])

  useEffect(() => {
    refreshStatus()
  }, [tab, refreshStatus])

  return (
    <div className="flex min-h-screen flex-col bg-white">
      <Header tabs={TABS} active={tab} onSelect={setTab} status={status} />
      <Hero />
      <main className="mx-auto w-full max-w-5xl flex-1 px-4 py-8 sm:px-6">
        {tab === 'documenten' && <DocumentsView />}
        {tab === 'zoeken' && <SearchView />}
        {tab === 'instellingen' && <SettingsView onSaved={refreshStatus} />}
      </main>
      <footer className="bg-kicmpi-dark px-6 py-6 text-sm text-gray-400">
        <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-2">
          <span>KicMPi Kennisassistent — concept (RAG-prototype)</span>
          <span>Alles draait lokaal in Docker · modellen via IP:port · data verlaat de infrastructuur niet</span>
        </div>
      </footer>
    </div>
  )
}
