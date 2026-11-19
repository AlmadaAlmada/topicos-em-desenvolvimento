import { useEffect, useState } from 'react'
import { api } from '../api.js'
import { useAuth, useMeta } from '../App.jsx'
import { Empty, ErrorBox, Field, Loading } from '../components/ui.jsx'

const EMPTY = { title: '', category: '', problem: '', solution: '' }

function ArticleForm({ initial, onSaved, onCancel }) {
  const meta = useMeta()
  const [form, setForm] = useState(initial || EMPTY)
  const [error, setError] = useState('')
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value })

  async function submit(e) {
    e.preventDefault()
    try {
      const body = { title: form.title, category: form.category || null, problem: form.problem, solution: form.solution }
      const saved = initial?.id
        ? await api(`/kb/${initial.id}`, { method: 'PUT', body })
        : await api('/kb', { method: 'POST', body })
      onSaved(saved)
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <form className="card" onSubmit={submit}>
      <h2>{initial?.id ? 'Editar artigo' : 'Novo artigo'}</h2>
      <ErrorBox error={error} />
      <div className="row">
        <Field label="Título"><input value={form.title} onChange={set('title')} required minLength={5} /></Field>
        <Field label="Categoria">
          <select value={form.category || ''} onChange={set('category')}>
            <option value="">—</option>
            {meta?.categories.map((c) => <option key={c}>{c}</option>)}
          </select>
        </Field>
      </div>
      <Field label="Problema (sintomas, como o usuário descreve)" hint="Usado pela IA para encontrar este artigo">
        <textarea rows={3} value={form.problem} onChange={set('problem')} required minLength={10} />
      </Field>
      <Field label="Solução (passo a passo)">
        <textarea rows={6} value={form.solution} onChange={set('solution')} required minLength={10} />
      </Field>
      <div className="row">
        <button className="btn primary">Salvar</button>
        <button type="button" className="btn ghost" onClick={onCancel}>Cancelar</button>
      </div>
    </form>
  )
}

export default function KnowledgeBase() {
  const { user, isStaff } = useAuth()
  const meta = useMeta()
  const [q, setQ] = useState('')
  const [category, setCategory] = useState('')
  const [articles, setArticles] = useState(null)
  const [open, setOpen] = useState(null)
  const [editing, setEditing] = useState(null)
  const [error, setError] = useState('')

  const load = () => api('/kb', { params: { q, category } }).then(setArticles).catch((e) => setError(e.message))
  useEffect(() => {
    const t = setTimeout(load, 250)
    return () => clearTimeout(t)
  }, [q, category]) // eslint-disable-line react-hooks/exhaustive-deps

  async function helpful(id) {
    await api(`/kb/${id}/helpful`, { method: 'POST' })
    load()
  }

  async function remove(id) {
    if (!window.confirm('Excluir este artigo da base de conhecimento?')) return
    try {
      await api(`/kb/${id}`, { method: 'DELETE' })
      load()
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <section>
      <div className="page-head">
        <h1>Base de conhecimento</h1>
        {isStaff && !editing && <button className="btn primary" onClick={() => setEditing({})}>+ Novo artigo</button>}
      </div>
      {editing && (
        <ArticleForm initial={editing.id ? editing : null}
          onSaved={() => { setEditing(null); load() }} onCancel={() => setEditing(null)} />
      )}
      <div className="filters card">
        <input placeholder="Buscar solução…" value={q} onChange={(e) => setQ(e.target.value)} />
        <select value={category} onChange={(e) => setCategory(e.target.value)} aria-label="Categoria">
          <option value="">Todas as categorias</option>
          {meta?.categories.map((c) => <option key={c}>{c}</option>)}
        </select>
      </div>
      <ErrorBox error={error} />
      {!articles ? <Loading /> : articles.length === 0 ? <Empty>Nenhum artigo encontrado.</Empty> : (
        <div className="kb-list">
          {articles.map((a) => (
            <article key={a.id} className="card kb-item">
              <header onClick={() => setOpen(open === a.id ? null : a.id)} className="clickable">
                <h3>{a.title}</h3>
                <div className="row small muted">
                  {a.category && <span className="badge muted">{a.category}</span>}
                  <span>{a.times_helpful} acharam útil</span>
                  {a.source_ticket_id && <span>origem: chamado #{a.source_ticket_id}</span>}
                </div>
              </header>
              {open === a.id && (
                <div className="kb-body">
                  <h4>Problema</h4>
                  <p className="pre">{a.problem}</p>
                  <h4>Solução</h4>
                  <p className="pre">{a.solution}</p>
                  <div className="row">
                    <button className="btn success small" onClick={() => helpful(a.id)}>Isso me ajudou</button>
                    {isStaff && <button className="btn small" onClick={() => setEditing(a)}>Editar</button>}
                    {user.role === 'admin' && <button className="btn danger small" onClick={() => remove(a.id)}>Excluir</button>}
                  </div>
                </div>
              )}
            </article>
          ))}
        </div>
      )}
    </section>
  )
}
