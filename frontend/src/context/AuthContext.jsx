import { useCallback, useEffect, useMemo, useState } from 'react'
import * as authApi from '../api/auth.js'
import { AuthContext } from './auth.js'

// 로그인한 사용자 정보를 앱 전체에서 함께 쓰기 위한 보관소.
export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  // 처음 열 때 이미 로그인한 상태인지 서버에 물어본다.
  useEffect(() => {
    let active = true
    authApi
      .fetchMe()
      .then((me) => active && setUser(me))
      .catch(() => active && setUser(null))
      .finally(() => active && setLoading(false))
    return () => {
      active = false
    }
  }, [])

  const login = useCallback(async (email, password) => {
    const me = await authApi.login(email, password)
    setUser(me)
    return me
  }, [])

  // 서버 요청이 실패해도 화면에서는 로그인 상태를 끝낸다.
  const logout = useCallback(async () => {
    try {
      await authApi.logout()
    } catch {
      // 무시: 화면의 로그인 상태는 어떤 경우든 끝낸다.
    }
    setUser(null)
  }, [])

  const value = useMemo(() => ({ user, loading, login, logout, setUser }), [user, loading, login, logout])
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
