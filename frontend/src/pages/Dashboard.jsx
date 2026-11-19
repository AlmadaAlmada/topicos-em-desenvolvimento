import { useEffect, useState } from 'react'
import { api } from '../api.js'
import { BarList, ErrorBox, Loading } from '../components/ui.jsx'

const num = (v, suffix = '') => (v === null || v === undefined ? '—' : `${v}${suffix}`)

function Kpi({ label, value, hint, tone }) {
  return (
    <div className={`kpi ${tone || ''}`}>
      <span className="kpi-label">{label}</span>
      <span className="kpi-value">{value}</span>
      {hint && <span className="kpi-hint">{hint}</span>}
    </div>
  )
}

export default function Dashboard() {
  const [days, setDays] = useState(30)
  const [data, setData] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    setData(null)
    api('/dashboard', { params: { days } }).then(setData).catch((e) => setError(e.message))
  }, [days])

  if (error) return <ErrorBox error={error} />
  if (!data) return <Loading />

  const maxDaily = Math.max(1, ...data.daily.map((d) => d.count))

  return (
    <section>
      <div className="page-head">
        <h1>Painel de indicadores</h1>
        <select value={days} onChange={(e) => setDays(Number(e.target.value))} aria-label="Período">
          <option value={7}>Últimos 7 dias</option>
          <option value={30}>Últimos 30 dias</option>
          <option value={90}>Últimos 90 dias</option>
        </select>
      </div>

      <div className="kpis">
        <Kpi label="Chamados no período" value={data.totals.tickets} />
        <Kpi label="Em aberto" value={data.totals.open} hint={`${data.totals.in_triage} em triagem · ${data.totals.unassigned} sem responsável`} />
        <Kpi label="Tempo médio de resolução" value={num(data.times.avg_resolution_hours, ' h')} />
        <Kpi label="Tempo médio até atribuição" value={num(data.times.avg_first_assignment_hours, ' h')} />
        <Kpi label="Resolvidos dentro do SLA" value={num(data.sla.resolved_within_sla_pct, '%')}
          hint={`${data.sla.open_breached} abertos com SLA estourado`} tone={data.sla.open_breached ? 'warn' : ''} />
        <Kpi label="Resolvidos pela base (sem chamado)" value={data.totals.deflected_by_kb} tone="ok" />
      </div>

      <div className="card">
        <h2>Volume diário de chamados</h2>
        <div className="daily" role="img" aria-label="Gráfico de chamados por dia">
          {data.daily.map((d) => (
            <div key={d.date} className="daily-col" title={`${d.date}: ${d.count}`}>
              <span style={{ height: `${(100 * d.count) / maxDaily}%` }} />
            </div>
          ))}
        </div>
        <div className="row space small muted"><span>{data.daily[0]?.date}</span><span>{data.daily.at(-1)?.date}</span></div>
      </div>

      <div className="grid-3">
        <div className="card"><h2>Por status</h2><BarList data={data.by_status} /></div>
        <div className="card"><h2>Por categoria</h2><BarList data={data.by_category} kind="cat" /></div>
        <div className="card"><h2>Por prioridade</h2><BarList data={data.by_priority} kind="prio" /></div>
      </div>

      <div className="grid-2">
        <div className="card table-wrap">
          <h2>Desempenho por técnico</h2>
          <table className="table">
            <thead><tr><th>Técnico</th><th>Especialidade</th><th>Abertos</th><th>Resolvidos</th><th>Média (h)</th></tr></thead>
            <tbody>
              {data.technicians.map((t) => (
                <tr key={t.id}><td>{t.name}</td><td>{t.specialty || '—'}</td><td>{t.open}</td><td>{t.resolved}</td><td>{num(t.avg_resolution_hours)}</td></tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="card ai-card">
          <h2><span className="ai-tag">IA</span> Qualidade da classificação em produção</h2>
          <div className="kpis small">
            <Kpi label="Acurácia categoria" value={num(data.ai.category_accuracy_pct, '%')} />
            <Kpi label="Acurácia prioridade" value={num(data.ai.priority_accuracy_pct, '%')} />
            <Kpi label="Baixa confiança" value={num(data.ai.low_confidence_pct, '%')} />
          </div>
          <p className="hint">Medido sobre {data.ai.reviewed} chamados confirmados ou corrigidos por técnicos.</p>
          {data.ai.top_confusions.length > 0 && (
            <>
              <h3>Erros mais comuns</h3>
              <ul className="plain">
                {data.ai.top_confusions.map((c, i) => (
                  <li key={i}>IA disse <strong>{c.ai}</strong>, técnico corrigiu para <strong>{c.human}</strong> ({c.count}x)</li>
                ))}
              </ul>
            </>
          )}
          <h3>Artigos mais úteis</h3>
          <ul className="plain">
            {data.kb_top.map((a) => <li key={a.id}>{a.title} <span className="muted small">· {a.helpful} úteis / {a.suggested} sugestões</span></li>)}
          </ul>
        </div>
      </div>
    </section>
  )
}
