import { Link, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/auth.js'

// 모든 화면에 공통으로 보이는 위쪽 메뉴와 본문 틀.
export default function Layout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  async function handleLogout() {
    await logout()
    navigate('/login')
  }

  return (
    <div className="app">
      <header className="topbar">
        <div className="topbar-inner">
          <Link to="/" className="brand">
            BuildLog
          </Link>
          <nav className="nav" aria-label="주 메뉴">
            {user ? (
              <>
                <Link to="/">홈</Link>
                <Link to="/studies">공부 기록</Link>
                <Link to="/todos">할 일</Link>
                <Link to="/errors">오류 기록</Link>
                <Link to="/public">공개 기록</Link>
                <Link to="/settings">계정 설정</Link>
                <span className="nav-user">{user.nickname}</span>
                <button type="button" className="nav-button" onClick={handleLogout}>
                  로그아웃
                </button>
              </>
            ) : (
              <>
                <Link to="/login">로그인</Link>
                <Link to="/signup">회원가입</Link>
              </>
            )}
          </nav>
        </div>
      </header>
      <main className="content">
        <Outlet />
      </main>
    </div>
  )
}
