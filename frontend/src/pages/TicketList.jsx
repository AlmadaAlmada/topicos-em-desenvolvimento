import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api, fmtDate } from '../api.js'
import { useAuth, useMeta } from '../App.jsx'
import { Badge, Empty, ErrorBox, Loading } from '../components/ui.jsx'

export default function TicketList() {
  const { isStaff } = useAuth()
  const meta = useMeta()
  const navigate = useNavigate()
  const [filters, setFilters] = useState({ status: '', category: '', priority: '', q: '', assigned_to_me: false })
  const [tickets, setTickets] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    const t = setTimeout(() => {
      api('/tickets', { params: { ...filters, assigned_to_me: filters.assigned_to_me || undefined } })
        .then(setTickets)
        .catch((e) => setError(e.message))
    }, 250)
    return () => clearTimeout(t)
  }, [filters])

  const set = (k) => (e) => setFilters({ ...filters, [k]: e.target.type === 'checkbox' ? e.target.checked : e.target.value })

  return (
    <section>
      <div className="page-head">
        <h1>{isStaff ? 'Chamados' : 'Meus chamados'}</h1>
        <Link to="/chamados/novo" className="btn primary">+ Abrir chamado</Link>
      </div>

      <div className="filters card">
        <input placeholder="Buscar por título ou descrição…" value={filters.q} onChange={set('q')} />
        <select value={filters.status} onChange={set('status')} aria-label="Status">
          <option value="">Todos os status</option>
          {meta?.statuses.map((s) => <option key={s}>{s}</option>)}
        </select>
        <select value={filters.category} onChange={set('category')} aria-label="Categoria">
          <option value="">Todas as categorias</option>
          {meta?.categories.map((s) => <option key={s}>{s}</option>)}
        </select>
        <select value={filters.priority} onChange={set('priority')} aria-label="Prioridade">
          <option value="">Todas as prioridades</option>
          {meta?.priorities.map((s) => <option key={s}>{s}</option>)}
        </select>
        {isStaff && (
          <label className="check">
            <input type="checkbox" checked={filters.assigned_to_me} onChange={set('assigned_to_me')} /> Atribuídos a mim
          </label>
        )}
      </div>

      <ErrorBox error={error} />
      {!tickets ? <Loading /> : tickets.length === 0 ? (
        <Empty>Nenhum chamado encontrado.</Empty>
      ) : (
        <div className="card table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th>#</th><th>Título</th><th>Status</th><th>Categoria</th><th>Prioridade</th>
                {isStaff && <th>Solicitante</th>}<th>Responsável</th><th>Aberto em</th><th>SLA</th>
              </tr>
            </thead>
            <tbody>
              {tickets.map((t) => (
                <tr key={t.id} onClick={() => navigate(`/chamados/${t.id}`)} className="clickable">
                  <td className="muted">{t.id}</td>
                  <td><Link to={`/chamados/${t.id}`}>{t.title}</Link></td>
                  <td><Badge kind="status" value={t.status} /></td>
                  <td>{t.category || <span className="muted">em triagem</span>}</td>
                  <td><Badge kind="prio" value={t.priority} /></td>
                  {isStaff && <td>{t.requester.name}</td>}
                  <td>{t.assignee?.name || <span className="muted">—</span>}</td>
                  <td className="nowrap">{fmtDate(t.created_at)}</td>
                  <td>{t.sla_breached ? <span className="badge sla-late">Estourado</span> : <span className="badge sla-ok">No prazo</span>}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}
