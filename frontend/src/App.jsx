import React from 'react'
import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import CallInterface from './pages/CallInterface'
import AgentDashboard from './pages/AgentDashboard'
import DemoMode from './pages/DemoMode'

function NavBar() {
  const base = 'px-4 py-2 rounded-lg text-sm font-semibold transition-all'
  const active = 'bg-white text-brand-900'
  const inactive = 'text-white/70 hover:text-white hover:bg-white/10'

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-brand-900 border-b border-brand-700 shadow-md">
      <div className="max-w-screen-xl mx-auto px-4 py-2 flex items-center gap-3 flex-wrap">
        <span className="text-white font-bold text-lg mr-2">🎙️ VaakSetu</span>
        <NavLink to="/demo"
          className={({ isActive }) => `${base} ${isActive ? 'bg-amber-400 text-gray-900' : 'text-amber-300 hover:text-white hover:bg-white/10'}`}
        >
          🏆 Demo Mode
        </NavLink>
        <NavLink to="/"
          className={({ isActive }) => `${base} ${isActive ? active : inactive}`}
        >
          📞 Call Interface
        </NavLink>
        <NavLink to="/dashboard"
          className={({ isActive }) => `${base} ${isActive ? active : inactive}`}
        >
          🖥️ Agent Dashboard
        </NavLink>
        <a
          href="http://localhost:8000/docs"
          target="_blank"
          rel="noreferrer"
          className={`${base} ${inactive}`}
        >
          📖 API Docs ↗
        </a>
        <span className="ml-auto text-xs text-indigo-300 hidden sm:block">AI for Bharat 2026 · Theme 12</span>
      </div>
    </nav>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <NavBar />
      <div className="pt-12">
        <Routes>
          <Route path="/"          element={<CallInterface />} />
          <Route path="/demo"      element={<DemoMode />} />
          <Route path="/dashboard" element={<AgentDashboard />} />
        </Routes>
      </div>
    </BrowserRouter>
  )
}
