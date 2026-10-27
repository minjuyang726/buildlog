import { Link, Outlet } from 'react-router-dom'

// 모든 화면에 공통으로 보이는 위쪽 메뉴와 본문 틀.
export default function Layout() {
  return (
    <div className="app">
      <header className="topbar">
        <div className="topbar-inner">
          <Link to="/" className="brand">
            BuildLog
          </Link>
          <nav className="nav" aria-label="주 메뉴">
            <Link to="/">홈</Link>
          </nav>
        </div>
      </header>
      <main className="content">
        <Outlet />
      </main>
    </div>
  )
}
