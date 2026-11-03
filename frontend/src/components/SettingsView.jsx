import { useEffect, useState } from 'react'
import { getSettings, probeUrl, saveSettings } from '../api/client.js'

// Four endpoint groups — the last two are stored now but reserved for the
// full pipeline (PLAN §6 View 3: "wordt in de volgende sprint gebruikt").
const GROUPS = [
  {
    key: 'embedding',
    title: 'Embedding model',
    hint: 'Zet tekst-chunks en zoekopdrachten om in vectoren (BGE-M3).',
    reserved: false,
  },
  {
    key: 'summary',
    title: 'Samenvatting model',
    hint: 'Genereert de AI-samenvatting met bronvermelding (Qwen3-8B).',
    reserved: false,
  },
  {
    key: 'vlm',
    title: 'Visie-model (PDF/video → tekst)',
    hint: 'Wordt in de volgende sprint gebruikt (volledige pijplijn).',
    reserved: true,
  },
  {
    key: 'asr',
    title: 'Audio-model (video/audio → tekst)',
    hint: 'Wordt in de volgende sprint gebruikt (volledige pijplijn).',
    reserved: true,
  },
]

export default function SettingsView({ onSaved }) {
  const [form, setForm] = useState(null)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [saveError, setSaveError] = useState(null)
  const [probing, setProbing] = useState({}) // key → true while testing
  const [probes, setProbes] = useState({}) // key → probe result | null

  useEffect(() => {
    getSettings().then(setForm).catch((e) => setSaveError(e.message))
  }, [])

  function setField(key, value) {
    setForm((f) => ({ ...f, [key]: value }))
    setSaved(false)
  }

  async function testConnection(key) {
    const url = (form && form[`${key}_url`] || '').trim()
    if (!url) {
      setProbes((p) => ({ ...p, [key]: { ok: false, reason: 'vul eerst een URL in' } }))
      return
    }
    setProbing((p) => ({ ...p, [key]: true }))
    setProbes((p) => ({ ...p, [key]: null }))
    try {
      const res = await probeUrl(url)
      setProbes((p) => ({ ...p, [key]: res }))
    } catch (e) {
      setProbes((p) => ({ ...p, [key]: { ok: false, reason: e.message } }))
    } finally {
      setProbing((p) => ({ ...p, [key]: false }))
    }
  }

  async function save() {
    setSaving(true)
    setSaveError(null)
    setSaved(false)
    try {
      await saveSettings({
        embedding_url: form.embedding_url,
        embedding_model: form.embedding_model,
        summary_url: form.summary_url,
        summary_model: form.summary_model,
        vlm_url: form.vlm_url,
        vlm_model: form.vlm_model,
        asr_url: form.asr_url,
        asr_model: form.asr_model,
        embed_mock: form.embed_mock,
      })
      setSaved(true)
      if (onSaved) onSaved()
    } catch (e) {
      setSaveError(e.message)
    } finally {
      setSaving(false)
    }
  }

  if (!form) {
    return <p className="text-kicmpi-slate">Laden…</p>
  }

  return (
    <div className="space-y-8">
      <section>
        <h2 className="mb-1 text-2xl font-bold text-kicmpi-blue">Instellingen</h2>
        <p className="mb-4 text-sm text-kicmpi-slate">
          Het adres (IP:port) van het model-systeem, per model. Wijzigingen worden opgeslagen en
          direct gebruikt — geen herstart of bestandsbewerking nodig.
        </p>
        <div className="grid gap-4 md:grid-cols-2">
          {GROUPS.map((g) => (
            <EndpointCard
              key={g.key}
              group={g}
              form={form}
              setField={setField}
              probing={!!probing[g.key]}
              probe={probes[g.key]}
              onTest={() => testConnection(g.key)}
            />
          ))}
        </div>
      </section>

      <section className="rounded-lg bg-kicmpi-stripes p-5">
        <label className="flex cursor-pointer items-center gap-3">
          <input
            type="checkbox"
            checked={!!form.embed_mock}
            onChange={(e) => setField('embed_mock', e.target.checked)}
            className="h-4 w-4 accent-kicmpi-blue"
          />
          <span className="font-semibold text-kicmpi-ink">Demo-modus (mock-embeddings)</span>
        </label>
        <p className="mt-2 inline-block rounded border border-amber-300 bg-amber-50 px-3 py-2 text-xs text-amber-800">
          Alleen voor proefdraaien — de echte modellen staan uit. Zoeken werkt dan nog (op
          sleutelwoorden), maar na wijzigen moeten documenten opnieuw worden ingevoerd (verwijderen
          en opnieuw uploaden).
        </p>
      </section>

      <div className="flex flex-wrap items-center gap-3">
        <button type="button" onClick={save} disabled={saving} className="btn-primary">
          {saving ? 'Opslaan…' : 'Bewaar instellingen'}
        </button>
        {saved && <span className="text-sm font-semibold text-green-700">✓ Instellingen opgeslagen</span>}
        {saveError && <span className="text-sm font-medium text-kicmpi-error">{saveError}</span>}
      </div>
    </div>
  )
}

function EndpointCard({ group, form, setField, probing, probe, onTest }) {
  const urlKey = `${group.key}_url`
  const modelKey = `${group.key}_model`
  return (
    <div
      className={`rounded-lg border p-4 ${
        group.reserved ? 'border-kicmpi-line bg-kicmpi-stripeA' : 'border-kicmpi-line bg-white'
      }`}
    >
      <h3 className={`font-bold ${group.reserved ? 'text-kicmpi-slate' : 'text-kicmpi-blue'}`}>
        {group.title}
      </h3>
      <p className="mb-3 mt-0.5 text-xs text-kicmpi-muted">{group.hint}</p>

      <label className="mb-1 block text-xs font-semibold text-kicmpi-slate">URL (IP:port)</label>
      <input
        className="input-pill mb-3 font-mono text-sm"
        value={form[urlKey] || ''}
        placeholder="http://192.168.69.20:8081"
        onChange={(e) => setField(urlKey, e.target.value)}
      />
      <label className="mb-1 block text-xs font-semibold text-kicmpi-slate">Modelnaam</label>
      <input
        className="input-pill mb-3 text-sm"
        value={form[modelKey] || ''}
        placeholder={group.key === 'embedding' ? 'bge-m3' : group.key === 'summary' ? 'qwen3-8b' : '…'}
        onChange={(e) => setField(modelKey, e.target.value)}
      />

      <div className="flex flex-wrap items-center gap-2">
        <button type="button" onClick={onTest} disabled={probing} className="btn-outline px-4 py-1.5 text-sm">
          {probing ? 'Testen…' : 'Test verbinding'}
        </button>
        {probe && (
          <span className={`text-sm font-semibold ${probe.ok ? 'text-green-700' : 'text-kicmpi-error'}`}>
            {probe.ok ? `✓ verbonden (${probe.latency_ms} ms)` : `✗ ${probe.reason || 'niet bereikbaar'}`}
          </span>
        )}
      </div>
    </div>
  )
}
