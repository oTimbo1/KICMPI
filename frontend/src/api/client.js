// Thin fetch wrapper for /api/* — all requests in the app go through here.
const BASE = '/api'

async function request(path, { method = 'GET', body, isForm = false } = {}) {
  const headers = {}
  let payload
  if (isForm) {
    payload = body // FormData — the browser sets the multipart content type
  } else if (body !== undefined) {
    headers['Content-Type'] = 'application/json'
    payload = JSON.stringify(body)
  }

  let res
  try {
    res = await fetch(BASE + path, { method, headers, body: payload })
  } catch {
    throw new Error('Backend niet bereikbaar (is de app gestart?)')
  }

  let data = null
  try {
    data = await res.json()
  } catch {
    /* non-JSON response */
  }

  if (!res.ok) {
    const detail = data && (data.detail || data.error)
    throw new Error(typeof detail === 'string' ? detail : `Fout ${res.status}`)
  }
  return data
}

export const getHealth = () => request('/health')

export const listDocuments = () => request('/documents')
export const getDocument = (id) => request(`/documents/${id}`)
export const uploadDocument = (file) => {
  const form = new FormData()
  form.append('file', file)
  return request('/documents', { method: 'POST', body: form, isForm: true })
}
export const deleteDocument = (id) => request(`/documents/${id}`, { method: 'DELETE' })

export const search = ({ query, top_k = 5, doc_id = null }) =>
  request('/search', { method: 'POST', body: { query, top_k, doc_id } })

export const getStatus = () => request('/status')

export const getSettings = () => request('/settings')
export const saveSettings = (body) => request('/settings', { method: 'PUT', body })

export const probeUrl = (url) => request('/probe', { method: 'POST', body: { url } })
