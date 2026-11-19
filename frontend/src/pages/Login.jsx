import { useState } from 'react'
import { Link, Navigate } from 'react-router-dom'
import { api } from '../api.js'
import { useAuth } from '../App.jsx'
import { ErrorBox, Field } from '../components/ui.jsx'

const DEMO = [
  ['Administrador', 'admin@helpdesk.com'],
  ['Técnica (Rede)', 'ana@helpdesk.com'],
  ['Solicitante', 'fernanda@empresa.com'],
]

export default function Login() {
  const auth = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  if (auth.user) return <Navigate to="/chamados" replace />

  async function submit(e) {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      auth.login(await api('/auth/login', { method: 'POST', body: { email, password } }))
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="auth-page">
      <form className="card auth-card" onSubmit={submit}>
        <div className="brand big"><span className="logo">HD</span> HelpDesk Inteligente</div>
        <p className="muted">Entre para abrir e acompanhar chamados de suporte.</p>
        <ErrorBox error={error} />
        <Field label="E-mail">
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required autoFocus />
        </Field>
        <Field label="Senha">
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
        </Field>
        <button className="btn primary block" disabled={busy}>{busy ? 'Entrando…' : 'Entrar'}</button>
        <p className="muted center">Não tem conta? <Link to="/cadastro">Cadastre-se</Link></p>
        <div className="demo">
          <span className="label">Contas de demonstração (senha: senha123)</span>
          {DEMO.map(([label, mail]) => (
            <button type="button" key={mail} className="btn ghost small"
              onClick={() => { setEmail(mail); setPassword('senha123') }}>
              {label}
            </button>
          ))}
        </div>
      </form>
    </div>
  )
}
