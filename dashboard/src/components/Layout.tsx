import { NavLink, Outlet } from 'react-router-dom'

export default function Layout() {
  return (
    <div className="app">
      <header className="header">
        <h1 className="header-title">📊 Analyst Dashboard</h1>
        <nav className="nav">
          <NavLink to="/" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
            Positionen
          </NavLink>
          <NavLink to="/runs" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
            Letzte Läufe
          </NavLink>
        </nav>
      </header>
      <main className="main">
        <Outlet />
      </main>
    </div>
  )
}
