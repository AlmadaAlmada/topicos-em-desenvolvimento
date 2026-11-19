import { useCallback, useEffect, useState } from 'react'
import { Link, useLocation, useParams } from 'react-router-dom'
import { api, fmtDate } from '../api.js'
import { useAuth, useMeta } from '../App.jsx'
import { Badge, Confidence, ErrorBox, Field, Loading } from '../components/ui.jsx'

function StaffPanel({ ticket, onChange, setError }) {
  const meta = useMeta()
  const [techs, setTechs] = useState([])
  const [cls, setCls] = useState({ category: ticket.category || ticket.ai_category || '', priority: ticket.priority || '' })
  const [resolution, setResolution] = useState(ticket.resolution || '')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    api('/users', { params: { role: 'tecnico' } }).then(setTechs).catch(() => {})
  }, [])
  useEffect(() => {
    setCls({ category: ticket.category || ticket.ai_category || '', priority: ticket.priority || '' })
    setResolution(ticket.resolution || '')
  }, [ticket])

  async function patch(body) {
    setBusy(true)
    setError('')
    try {
      await api(`/tickets/${ticket.id}`, { method: 'PATCH', body })
      await onChange()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  async function autoAssign() {
    setBusy(true)
    try {
      await api(`/tickets/${ticket.id}/auto-assign`, { method: 'POST' })
      await onChange()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  const changedCls = cls.category !== (ticket.category || '') || cls.priority !== (ticket.priority || '')

  return (
    <div className="card">
      <h2>Ações do técnico</h2>

      <h3>Classificação</h3>
      <div className="row">
        <Field label="Categoria">
          <select value={cls.category} onChange={(e) => setCls({ ...cls, category: e.target.value })}>
            <option value="">—</option>
            {meta?.categories.map((c) => <option key={c}>{c}</option>)}
          </select>
        </Field>
        <Field label="Prioridade">
          <select value={cls.priority} onChange={(e) => setCls({ ...cls, priority: e.target.value })}>
            {meta?.priorities.map((c) => <option key={c}>{c}</option>)}
          </select>
        </Field>
      </div>
      <button className="btn small" disabled={busy || !cls.category} onClick={() => patch(cls)}>
        {changedCls ? 'Corrigir classificação' : ticket.classification_reviewed ? 'Classificação confirmada ✓' : 'Confirmar classificação da IA'}
      </button>
      <p className="hint">Confirmações e correções viram dados de treino para a próxima versão do modelo.</p>

      <h3>Responsável</h3>
      <div className="row">
        <select value={ticket.assignee?.id || ''} disabled={busy}
          onChange={(e) => patch({ assignee_id: e.target.value ? Number(e.target.value) : null })}>
          <option value="">Sem responsável</option>
          {techs.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
        </select>
        <button className="btn small" disabled={busy || !ticket.category} onClick={autoAssign}
          title="Regra: especialista da categoria com menos chamados abertos">
          Atribuir automaticamente
        </button>
      </div>

      <h3>Status e solução</h3>
      <Field label="Solução aplicada" hint="Obrigatória para marcar como resolvido">
        <textarea rows={4} value={resolution} onChange={(e) => setResolution(e.target.value)} />
      </Field>
      <div className="row wrap">
        {meta?.statuses.filter((s) => s !== ticket.status && s !== 'Triagem').map((s) => (
          <button key={s} className={`btn small ${s === 'Resolvido' ? 'success' : ''}`} disabled={busy}
            onClick={() => patch(resolution !== (ticket.resolution || '') ? { resolution, status: s } : { status: s })}>
            {s}
          </button>
        ))}
        {resolution !== (ticket.resolution || '') && (
          <button className="btn small ghost" disabled={busy} onClick={() => patch({ resolution })}>Salvar solução</button>
        )}
      </div>
    </div>
  )
}

function SaveAsArticle({ ticket, setError }) {
  const [saved, setSaved] = useState(null)
  async function save() {
    try {
      const art = await api('/kb', {
        method: 'POST',
        body: { title: ticket.title, problem: ticket.description, solution: ticket.resolution,
                category: ticket.category, source_ticket_id: ticket.id },
      })
      setSaved(art)
    } catch (err) {
      setError(err.message)
    }
  }
  if (saved) return <p className="alert success">Artigo #{saved.id} criado na base de conhecimento.</p>
  return (
    <button className="btn small ghost" onClick={save} title="Transforma esta solução em artigo para sugestões futuras">
      Salvar solução na base de conhecimento
    </button>
  )
}

export default function TicketDetail() {
  const { id } = useParams()
  const location = useLocation()
  const { user, isStaff } = useAuth()
  const [ticket, setTicket] = useState(null)
  const [error, setError] = useState('')
  const [comment, setComment] = useState('')
  const [openSugg, setOpenSugg] = useState(null)

  const load = useCallback(() => api(`/tickets/${id}`).then(setTicket).catch((e) => setError(e.message)), [id])
  useEffect(() => { load() }, [load])

  async function sendComment(e) {
    e.preventDefault()
    try {
      await api(`/tickets/${id}/comments`, { method: 'POST', body: { body: comment } })
      setComment('')
      load()
    } catch (err) {
      setError(err.message)
    }
  }

  async function requesterAction(status) {
    try {
      await api(`/tickets/${id}`, { method: 'PATCH', body: { status } })
      load()
    } catch (err) {
      setError(err.message)
    }
  }

  async function useArticle(articleId) {
    try {
      await api(`/tickets/${id}`, { method: 'PATCH', body: { kb_article_used_id: articleId } })
      load()
    } catch (err) {
      setError(err.message)
    }
  }

  if (!ticket) return error ? <ErrorBox error={error} /> : <Loading />

  const aiChanged = ticket.ai_category && ticket.category && ticket.ai_category !== ticket.category

  return (
    <section>
      <div className="page-head">
        <div>
          <Link to="/chamados" className="muted small">← Voltar</Link>
          <h1>#{ticket.id} · {ticket.title}</h1>
        </div>
        <div className="row">
          <Badge kind="status" value={ticket.status} />
          <Badge kind="prio" value={ticket.priority} />
        </div>
      </div>
      {location.state?.created && <div className="alert success">Chamado aberto com sucesso.</div>}
      <ErrorBox error={error} />

      <div className="grid-2">
        <div className="stack">
          <div className="card">
            <p className="pre">{ticket.description}</p>
            <dl className="kv cols">
              <dt>Solicitante</dt><dd>{ticket.requester.name}</dd>
              <dt>Responsável</dt><dd>{ticket.assignee?.name || '—'}</dd>
              <dt>Categoria</dt><dd>{ticket.category || <em className="muted">em triagem</em>}</dd>
              <dt>Aberto em</dt><dd>{fmtDate(ticket.created_at)}</dd>
              <dt>Prazo (SLA)</dt>
              <dd>{fmtDate(ticket.sla_due_at)} {ticket.sla_breached && <span className="badge sla-late">Estourado</span>}</dd>
              <dt>Resolvido em</dt><dd>{fmtDate(ticket.resolved_at)}</dd>
            </dl>
            {ticket.resolution && (
              <div className="resolution">
                <h3>Solução</h3>
                <p className="pre">{ticket.resolution}</p>
                {isStaff && ['Resolvido', 'Fechado'].includes(ticket.status) && <SaveAsArticle ticket={ticket} setError={setError} />}
              </div>
            )}
            {!isStaff && ticket.requester.id === user.id && ticket.status === 'Resolvido' && (
              <div className="alert info">
                O técnico marcou este chamado como resolvido.
                <div className="row">
                  <button className="btn success small" onClick={() => requesterAction('Fechado')}>Confirmar solução</button>
                  <button className="btn ghost small" onClick={() => requesterAction('Aberto')}>Reabrir</button>
                </div>
              </div>
            )}
          </div>

          <div className="card">
            <h2>Histórico</h2>
            <ul className="timeline">
              {ticket.comments.map((c) => (
                <li key={c.id} className={c.is_system ? 'system' : ''}>
                  <div className="meta"><strong>{c.is_system ? 'Sistema' : c.author.name}</strong> · {fmtDate(c.created_at)}</div>
                  <div className="pre">{c.body}</div>
                </li>
              ))}
            </ul>
            {ticket.status !== 'Fechado' && (
              <form onSubmit={sendComment} className="comment-form">
                <textarea rows={3} placeholder="Escreva um comentário…" value={comment} onChange={(e) => setComment(e.target.value)} required />
                <button className="btn primary small">Comentar</button>
              </form>
            )}
          </div>
        </div>

        <aside className="stack">
          <div className="card ai-card">
            <h2><span className="ai-tag">IA</span> Classificação automática</h2>
            {ticket.ai_category ? (
              <>
                <dl className="kv">
                  <dt>Categoria sugerida</dt>
                  <dd>{ticket.ai_category} <Confidence value={ticket.ai_category_confidence} /></dd>
                  <dt>Prioridade sugerida</dt>
                  <dd>{ticket.ai_priority} <Confidence value={ticket.ai_priority_confidence} /></dd>
                  <dt>Modelo</dt><dd className="muted small">{ticket.ai_model_version}</dd>
                </dl>
                {ticket.priority_rule && <p className="hint">Regra aplicada: {ticket.priority_rule} → {ticket.priority}</p>}
                {ticket.status === 'Triagem' && <p className="alert warn">Confiança baixa: aguardando triagem humana.</p>}
                {ticket.classification_reviewed && (
                  <p className={`hint ${aiChanged ? 'warn-text' : 'ok-text'}`}>
                    {aiChanged ? `Corrigida por técnico para "${ticket.category}".` : 'Confirmada por técnico.'}
                  </p>
                )}
              </>
            ) : <p className="muted">Chamado registrado sem classificação automática.</p>}
          </div>

          {isStaff && <StaffPanel ticket={ticket} onChange={load} setError={setError} />}

          <div className="card">
            <h2><span className="ai-tag">IA</span> Soluções sugeridas</h2>
            {ticket.suggestions.length === 0 ? <p className="muted">Nenhum artigo similar.</p> : (
              <ul className="suggestions">
                {ticket.suggestions.map((s) => (
                  <li key={s.id}>
                    <button type="button" className="link" onClick={() => setOpenSugg(openSugg === s.id ? null : s.id)}>{s.title}</button>
                    <span className="muted small"> · {Math.round(s.score * 100)}%</span>
                    {ticket.kb_article_used_id === s.id && <span className="badge sla-ok">usado</span>}
                    {openSugg === s.id && (
                      <div className="solution">
                        <pre>{s.solution}</pre>
                        {isStaff && ticket.kb_article_used_id !== s.id && (
                          <button className="btn small" onClick={() => useArticle(s.id)}>Marcar como solução utilizada</button>
                        )}
                      </div>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </div>
        </aside>
      </div>
    </section>
  )
}
