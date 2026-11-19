import { useEffect, useState } from 'react'
import { api, fmtDate } from '../api.js'
import { useAuth, useMeta } from '../App.jsx'
import { ErrorBox, Loading } from '../components/ui.jsx'

function Users({ setError }) {
  const meta = useMeta()
  const { user: me } = useAuth()
  const [users, setUsers] = useState(null)
  const load = () => api('/users').then(setUsers).catch((e) => setError(e.message))
  useEffect(() => { load() }, []) // eslint-disable-line react-hooks/exhaustive-deps

  async function update(id, body) {
    setError('')
    try {
      await api(`/users/${id}`, { method: 'PATCH', body })
      load()
    } catch (err) {
      setError(err.message)
    }
  }

  if (!users) return <Loading />
  return (
    <div className="card table-wrap">
      <h2>Usuários e perfis</h2>
      <table className="table">
        <thead><tr><th>Nome</th><th>E-mail</th><th>Perfil</th><th>Especialidade</th><th>Ativo</th></tr></thead>
        <tbody>
          {users.map((u) => (
            <tr key={u.id}>
              <td>{u.name}</td>
              <td className="muted">{u.email}</td>
              <td>
                <select value={u.role} disabled={u.id === me.id} onChange={(e) => update(u.id, { role: e.target.value })}>
                  {meta?.roles.map((r) => <option key={r}>{r}</option>)}
                </select>
              </td>
              <td>
                <select value={u.specialty || ''} disabled={u.role === 'solicitante'}
                  onChange={(e) => update(u.id, { specialty: e.target.value })}>
                  <option value="">—</option>
                  {meta?.categories.map((c) => <option key={c}>{c}</option>)}
                </select>
              </td>
              <td>
                <input type="checkbox" checked={u.active} disabled={u.id === me.id}
                  onChange={(e) => update(u.id, { active: e.target.checked })} aria-label="Ativo" />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function Models({ setError }) {
  const [models, setModels] = useState(null)
  const [busy, setBusy] = useState(false)
  const load = () => api('/ai/models').then(setModels).catch((e) => setError(e.message))
  useEffect(() => { load() }, []) // eslint-disable-line react-hooks/exhaustive-deps

  async function run(path) {
    setBusy(true)
    setError('')
    try {
      await api(path, { method: 'POST' })
      await load()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  if (!models) return <Loading />
  return (
    <div className="card table-wrap ai-card">
      <div className="row space">
        <h2><span className="ai-tag">IA</span> Versões do modelo de classificação</h2>
        <button className="btn primary small" disabled={busy} onClick={() => run('/ai/retrain')}>
          {busy ? 'Treinando…' : 'Retreinar com chamados revisados'}
        </button>
      </div>
      <p className="hint">
        O retreino usa o conjunto inicial + chamados cuja classificação foi confirmada ou corrigida por técnicos.
        A acurácia é estimada por validação cruzada (5 partições). Se uma versão nova piorar, reative a anterior.
      </p>
      <table className="table">
        <thead><tr><th>Versão</th><th>Treinado em</th><th>Amostras</th><th>Vindas de chamados</th><th>Acurácia categoria</th><th>Acurácia prioridade</th><th></th></tr></thead>
        <tbody>
          {models.map((m) => (
            <tr key={m.version}>
              <td><code>{m.version}</code></td>
              <td>{fmtDate(m.trained_at)}</td>
              <td>{m.samples}</td>
              <td>{m.samples_from_tickets}</td>
              <td>{(m.category_accuracy * 100).toFixed(1)}%</td>
              <td>{(m.priority_accuracy * 100).toFixed(1)}%</td>
              <td>{m.active ? <span className="badge sla-ok">ativa</span> : (
                <button className="btn ghost small" disabled={busy} onClick={() => run(`/ai/models/${m.version}/activate`)}>Reativar</button>
              )}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default function Admin() {
  const [error, setError] = useState('')
  return (
    <section className="stack">
      <div className="page-head"><h1>Administração</h1></div>
      <ErrorBox error={error} />
      <Models setError={setError} />
      <Users setError={setError} />
    </section>
  )
}
