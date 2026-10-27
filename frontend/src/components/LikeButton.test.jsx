import { cleanup, fireEvent, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { ALICE, mockApi, renderApp } from '../test/helpers.jsx'

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

const me = { 'GET /api/auth/me': [200, ALICE] }
const study = (extra = {}) => ({
  id: 1,
  title: '공개 공부',
  content: '내용',
  is_public: true,
  created_at: '2026-10-27T01:00:00Z',
  updated_at: null,
  author_nickname: 'bobby',
  is_mine: false,
  ...extra,
})
const base = { ...me, 'GET /api/studies/1/comments': [200, { items: [] }] }

describe('좋아요 버튼', () => {
  it('처음 누르면 등록하고 개수를 올리며, 다시 누르면 취소한다', async () => {
    let liked = false
    const { calls } = mockApi({
      ...base,
      'GET /api/studies/1': [200, study()],
      'GET /api/studies/1/like': [200, { liked: false, like_count: 3 }],
      'PUT /api/studies/1/like': () => {
        liked = true
        return [200, { liked: true, like_count: 4 }]
      },
      'DELETE /api/studies/1/like': () => {
        liked = false
        return [200, { liked: false, like_count: 3 }]
      },
    })
    renderApp('/studies/1')
    const button = await screen.findByRole('button', { name: '좋아요' })
    expect(button.getAttribute('aria-pressed')).toBe('false')
    expect(screen.getByLabelText('좋아요 수').textContent).toBe('3')

    fireEvent.click(button)
    const cancel = await screen.findByRole('button', { name: '좋아요 취소' })
    expect(cancel.getAttribute('aria-pressed')).toBe('true')
    expect(screen.getByLabelText('좋아요 수').textContent).toBe('4')
    expect(liked).toBe(true)

    fireEvent.click(cancel)
    await screen.findByRole('button', { name: '좋아요' })
    expect(screen.getByLabelText('좋아요 수').textContent).toBe('3')
    expect(calls.map((c) => c.key)).toEqual(expect.arrayContaining(['PUT /api/studies/1/like', 'DELETE /api/studies/1/like']))
  })

  it('이미 눌러 둔 상태로 열면 눌린 상태로 보인다', async () => {
    mockApi({
      ...base,
      'GET /api/studies/1': [200, study()],
      'GET /api/studies/1/like': [200, { liked: true, like_count: 1 }],
    })
    renderApp('/studies/1')
    expect((await screen.findByRole('button', { name: '좋아요 취소' })).getAttribute('aria-pressed')).toBe('true')
  })

  it('실패하면 이전 상태와 개수를 그대로 두고 안내를 보여준다', async () => {
    mockApi({
      ...base,
      'GET /api/studies/1': [200, study()],
      'GET /api/studies/1/like': [200, { liked: false, like_count: 3 }],
      'PUT /api/studies/1/like': new Error('network'),
    })
    renderApp('/studies/1')
    fireEvent.click(await screen.findByRole('button', { name: '좋아요' }))
    expect(await screen.findByText(/좋아요를 처리하지 못했습니다/)).toBeTruthy()
    expect(screen.getByRole('button', { name: '좋아요' }).getAttribute('aria-pressed')).toBe('false')
    expect(screen.getByLabelText('좋아요 수').textContent).toBe('3')
  })

  it('비공개 기록에는 좋아요 버튼이 없고 요청도 보내지 않는다', async () => {
    const { fn } = mockApi({ ...me, 'GET /api/studies/1': [200, study({ is_public: false, is_mine: true })] })
    renderApp('/studies/1')
    await screen.findByRole('heading', { name: /공개 공부/ })
    expect(screen.queryByLabelText('좋아요 수')).toBeNull()
    expect(fn.mock.calls.some(([url]) => String(url).includes('/like'))).toBe(false)
  })

  it('오류 기록에서도 좋아요를 누를 수 있다', async () => {
    mockApi({
      ...me,
      'GET /api/errors/3': [
        200,
        { id: 3, title: '오류', content: '내용', solution: null, is_resolved: false, is_public: true, created_at: '2026-10-27T01:00:00Z', updated_at: null, resolved_at: null, author_nickname: 'bobby', is_mine: false },
      ],
      'GET /api/errors/3/comments': [200, { items: [] }],
      'GET /api/errors/3/like': [200, { liked: false, like_count: 0 }],
      'PUT /api/errors/3/like': [200, { liked: true, like_count: 1 }],
    })
    renderApp('/errors/3')
    fireEvent.click(await screen.findByRole('button', { name: '좋아요' }))
    await waitFor(() => expect(screen.getByLabelText('좋아요 수').textContent).toBe('1'))
  })
})
