import { createContext, useContext, useEffect, useState } from 'react'
import { Navigate, NavLink, Route, Routes, useNavigate } from 'react-router-dom'
import { api, clearSession, getSession, saveSession } from './api.js'
import Login from './pages/Login.jsx'
import Register from './pages/Register.jsx'
import TicketList from './pages/TicketList.jsx'
import NewTicket from './pages/NewTicket.jsx'
import TicketDetail from './pages/TicketDetail.jsx'
import KnowledgeBase from './pages/KnowledgeBase.jsx'
import Dashboard from './pages/Dashboard.jsx'
import Admin from './pages/Admin.jsx'

const AuthContext = createContext(null)
export const useAuth = () => useContext(AuthContext)

const MetaContext = createContext(null)
export const useMeta = () => useContext(MetaContext)

const isStaff = (user) => user && (user.role === 'tecnico' || user.role === 'admin')

function Layout({ children }) {
  const { user, logout } = useAuth()
  return (
    <div className="layout">
      <header className="topbar">
        <div className="brand">
          <span className="logo" aria-hidden>HD</span>
          <span>HelpDesk Inteligente</span>
        </div>
        <nav className="nav">
          <NavLink to="/chamados" end>{isStaff(user) ? 'Chamados' : 'Meus chamados'}</NavLink>
          <NavLink to="/chamados/novo">Abrir chamado</NavLink>
          <NavLink to="/base">Base de conhecimento</NavLink>
          {isStaff(user) && <NavLink to="/painel">Painel</NavLink>}
          {user.role === 'admin' && <NavLink to="/admin">Administração</NavLink>}
        </nav>
        <div className="user">
          <span title={user.email}>{user.name}</span>
          <span className={`role role-${user.role}`}>{user.role}</span>
          <button className="btn ghost small" onClick={logout}>Sair</button>
        </div>
      </header>
      <main className="content">{children}</main>
    </div>
  )
}

function Private({ children, staff = false, admin = false }) {
  const { user } = useAuth()
  if (!user) return <Navigate to="/login" replace />
  if (staff && !isStaff(user)) return <Navigate to="/chamados" replace />
  if (admin && user.role !== 'admin') return <Navigate to="/chamados" replace />
  return <Layout>{children}</Layout>
}

export default function App() {
  const [session, setSession] = useState(getSession())
  const [meta, setMeta] = useState(null)
  const navigate = useNavigate()

  useEffect(() => {
    api('/meta').then(setMeta).catch(() => {})
  }, [])

  const auth = {
    user: session?.user,
    isStaff: isStaff(session?.user),
    login(data) {
      saveSession(data)
      setSession(getSession())
      navigate(isStaff(data.user) ? '/painel' : '/chamados')
    },
    logout() {
      clearSession()
      setSession(null)
      navigate('/login')
    },
  }

  return (
    <AuthContext.Provider value={auth}>
      <MetaContext.Provider value={meta}>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/cadastro" element={<Register />} />
          <Route path="/chamados" element={<Private><TicketList /></Private>} />
          <Route path="/chamados/novo" element={<Private><NewTicket /></Private>} />
          <Route path="/chamados/:id" element={<Private><TicketDetail /></Private>} />
          <Route path="/base" element={<Private><KnowledgeBase /></Private>} />
          <Route path="/painel" element={<Private staff><Dashboard /></Private>} />
          <Route path="/admin" element={<Private admin><Admin /></Private>} />
          <Route path="*" element={<Navigate to={session ? '/chamados' : '/login'} replace />} />
        </Routes>
      </MetaContext.Provider>
    </AuthContext.Provider>
  )
}
