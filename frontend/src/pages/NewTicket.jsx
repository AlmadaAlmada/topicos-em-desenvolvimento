import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api.js'
import { Badge, Confidence, ErrorBox, Field } from '../components/ui.jsx'

export default function NewTicket() {
  const navigate = useNavigate()
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [preview, setPreview] = useState(null)
  const [suggestions, setSuggestions] = useState([])
  const [open, setOpen] = useState(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [solved, setSolved] = useState(false)

  // Pré-visualização da IA enquanto o usuário digita (debounce de 600 ms).
  useEffect(() => {
    const text = `${title} ${description}`.trim()
    if (text.length < 8) {
      setPreview(null)
      setSuggestions([])
      return
    }
    const t = setTimeout(() => {
      api('/ai/classify', { method: 'POST', body: { title, description } }).then(setPreview).catch(() => {})
      api('/ai/suggestions', { params: { q: text } }).then(setSuggestions).catch(() => {})
    }, 600)
    return () => clearTimeout(t)
  }, [title, description])

  async function submit(e) {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      const ticket = await api('/tickets', { method: 'POST', body: { title, description } })
      navigate(`/chamados/${ticket.id}`, { state: { created: true } })
    } catch (err) {
      setError(err.message)
      setBusy(false)
    }
  }

  async function resolvedByArticle(article) {
    try {
      await api('/tickets/self-resolved', {
        method: 'POST',
        body: { title: title || article.title, description, kb_article_id: article.id },
      })
      setSolved(true)
    } catch (err) {
      setError(err.message)
    }
  }

  if (solved) {
    return (
      <section className="narrow">
        <div className="card success-card">
          <h1>Que bom que resolveu!</h1>
          <p>Registramos que a solução da base de conhecimento ajudou. Nenhum chamado foi aberto.</p>
          <div className="actions">
            <button className="btn primary" onClick={() => navigate('/chamados')}>Voltar aos chamados</button>
            <button className="btn ghost" onClick={() => { setSolved(false); setTitle(''); setDescription('') }}>Abrir outro</button>
          </div>
        </div>
      </section>
    )
  }

  return (
    <section>
      <div className="page-head"><h1>Abrir chamado</h1></div>
      <div className="grid-2">
        <form className="card" onSubmit={submit}>
          <ErrorBox error={error} />
          <Field label="Título" hint="Resuma o problema em poucas palavras">
            <input value={title} onChange={(e) => setTitle(e.target.value)} required minLength={5} maxLength={200}
              placeholder="Ex.: Impressora do 2º andar não imprime" />
          </Field>
          <Field label="Descrição" hint="Conte o que aconteceu, desde quando e quem é afetado">
            <textarea rows={8} value={description} onChange={(e) => setDescription(e.target.value)} required minLength={10} />
          </Field>
          <p className="hint">
            A categoria e a prioridade são sugeridas automaticamente por IA e revisadas pela equipe de suporte.
            Não informe senhas ou dados pessoais sensíveis na descrição.
          </p>
          <button className="btn primary" disabled={busy}>{busy ? 'Enviando…' : 'Abrir chamado'}</button>
        </form>

        <aside className="stack">
          <div className="card ai-card">
            <h2><span className="ai-tag">IA</span> Classificação prevista</h2>
            {!preview ? (
              <p className="muted">Comece a digitar para ver a categoria e a prioridade previstas.</p>
            ) : (
              <>
                <dl className="kv">
                  <dt>Categoria</dt>
                  <dd><strong>{preview.category}</strong> <Confidence value={preview.category_confidence} /></dd>
                  <dt>Prioridade</dt>
                  <dd><Badge kind="prio" value={preview.priority} /></dd>
                </dl>
                {preview.priority_rule && <p className="hint">Prioridade elevada pela regra: {preview.priority_rule}</p>}
                {preview.needs_triage && (
                  <p className="alert warn">Confiança baixa: um técnico vai revisar a classificação (triagem).</p>
                )}
              </>
            )}
          </div>

          <div className="card">
            <h2><span className="ai-tag">IA</span> Soluções que podem ajudar</h2>
            {suggestions.length === 0 ? (
              <p className="muted">Nenhuma solução parecida encontrada ainda.</p>
            ) : (
              <ul className="suggestions">
                {suggestions.map((s) => (
                  <li key={s.id}>
                    <button type="button" className="link" onClick={() => setOpen(open === s.id ? null : s.id)}>
                      {s.title}
                    </button>
                    <span className="muted small"> · {Math.round(s.score * 100)}% similar</span>
                    {open === s.id && (
                      <div className="solution">
                        <pre>{s.solution}</pre>
                        <button type="button" className="btn success small" onClick={() => resolvedByArticle(s)}>
                          Isso resolveu meu problema
                        </button>
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
