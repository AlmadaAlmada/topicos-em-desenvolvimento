import { useState } from 'react'
import { Link, Navigate } from 'react-router-dom'
import { api } from '../api.js'
import { useAuth } from '../App.jsx'
import { ErrorBox, Field } from '../components/ui.jsx'

export default function Register() {
  const auth = useAuth()
  const [form, setForm] = useState({ name: '', email: '', password: '', confirm: '', department: '' })
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  if (auth.user) return <Navigate to="/chamados" replace />
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value })

  async function submit(e) {
    e.preventDefault()
    if (form.password !== form.confirm) return setError('As senhas não conferem')
    setBusy(true)
    setError('')
    try {
      const { confirm, ...body } = form
      auth.login(await api('/auth/register', { method: 'POST', body }))
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="auth-page">
      <form className="card auth-card" onSubmit={submit}>
        <div className="brand big"><span className="logo">HD</span> Criar conta</div>
        <ErrorBox error={error} />
        <Field label="Nome completo"><input value={form.name} onChange={set('name')} required minLength={2} /></Field>
        <Field label="E-mail corporativo"><input type="email" value={form.email} onChange={set('email')} required /></Field>
        <Field label="Departamento"><input value={form.department} onChange={set('department')} /></Field>
        <div className="row">
          <Field label="Senha" hint="Mínimo de 6 caracteres">
            <input type="password" value={form.password} onChange={set('password')} required minLength={6} />
          </Field>
          <Field label="Confirmar senha">
            <input type="password" value={form.confirm} onChange={set('confirm')} required />
          </Field>
        </div>
        <button className="btn primary block" disabled={busy}>{busy ? 'Criando…' : 'Criar conta'}</button>
        <p className="muted center">Já tem conta? <Link to="/login">Entrar</Link></p>
      </form>
    </div>
  )
}
