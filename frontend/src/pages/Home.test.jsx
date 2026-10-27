import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import Home from './Home.jsx'

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

describe('Home', () => {
  it('서버가 정상이면 "서버 연결됨"을 보여준다', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({ ok: true, json: async () => ({ status: 'ok' }) }),
    )
    render(<Home />)
    expect(await screen.findByText('서버 연결됨')).toBeTruthy()
  })

  it('서버에 연결하지 못하면 "서버 연결 실패" 안내를 보여준다', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('network')))
    render(<Home />)
    expect(await screen.findByText(/서버 연결 실패/)).toBeTruthy()
  })
})
