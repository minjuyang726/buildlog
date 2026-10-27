import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../context/auth.js'

// 로그인한 사용자만 들어갈 수 있는 화면을 감싼다. 로그인하지 않았으면 로그인 화면으로 보낸다.
// 화면에서 막는 것은 편의일 뿐이고, 실제 권한 검사는 서버가 한다.
export default function ProtectedRoute() {
  const { user, loading } = useAuth()
  if (loading) return <p className="muted">불러오는 중입니다.</p>
  if (!user) return <Navigate to="/login" replace />
  return <Outlet />
}
