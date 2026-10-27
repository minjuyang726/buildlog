import { render } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { vi } from 'vitest'
import App from '../App.jsx'
import { AuthProvider } from '../context/AuthContext.jsx'

export const ALICE = { id: 1, email: 'alice@example.com', nickname: 'alice' }
export const NOT_LOGGED_IN = [401, { detail: '로그인이 필요합니다.' }]

// 서버 대신 정해 둔 응답을 돌려주는 가짜 fetch. 키는 "METHOD /api/경로" 형태.
export function mockApi(handlers) {
  const calls = []
  const fn = vi.fn(async (url, options = {}) => {
    const method = options.method ?? 'GET'
    const key = `${method} ${url}`
    const body = options.body ? JSON.parse(options.body) : undefined
    calls.push({ key, body })
    const handler = handlers[key]
    if (!handler) throw new Error(`가짜 서버에 응답이 없습니다: ${key}`)
    const result = typeof handler === 'function' ? handler(body) : handler
    if (result instanceof Error) throw result
    const [status, data] = result
    return { ok: status >= 200 && status < 300, status, json: async () => data }
  })
  vi.stubGlobal('fetch', fn)
  return { fn, calls }
}

export function renderApp(route = '/') {
  return render(
    <MemoryRouter initialEntries={[route]}>
      <AuthProvider>
        <App />
      </AuthProvider>
    </MemoryRouter>,
  )
}
