import { pct } from '../api.js'

export function Badge({ kind, value }) {
  if (!value) return <span className="badge muted">—</span>
  const slug = value.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().replace(/\s+/g, '-')
  return <span className={`badge ${kind}-${slug}`}>{value}</span>
}

export function Confidence({ value }) {
  if (value === null || value === undefined) return null
  const level = value >= 0.7 ? 'high' : value >= 0.45 ? 'mid' : 'low'
  return (
    <span className={`confidence ${level}`} title="Confiança do modelo de IA">
      <span className="bar"><span style={{ width: pct(value) }} /></span>
      {pct(value)}
    </span>
  )
}

export function ErrorBox({ error }) {
  if (!error) return null
  return <div className="alert error" role="alert">{error}</div>
}

export function Loading({ text = 'Carregando…' }) {
  return <div className="loading">{text}</div>
}

export function Empty({ children }) {
  return <div className="empty">{children}</div>
}

export function Field({ label, children, hint }) {
  return (
    <label className="field">
      <span className="label">{label}</span>
      {children}
      {hint && <span className="hint">{hint}</span>}
    </label>
  )
}

export function BarList({ data, kind }) {
  const entries = Object.entries(data || {})
  const max = Math.max(1, ...entries.map(([, v]) => v))
  return (
    <ul className="barlist">
      {entries.map(([label, value]) => (
        <li key={label}>
          <span className="bl-label">{label}</span>
          <span className="bl-track">
            <span className={`bl-fill ${kind ? `${kind}-fill` : ''}`} style={{ width: `${(100 * value) / max}%` }} />
          </span>
          <span className="bl-value">{value}</span>
        </li>
      ))}
    </ul>
  )
}
