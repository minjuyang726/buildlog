import { cleanup, fireEvent, screen, waitFor, within } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { ALICE, mockApi, renderApp } from '../test/helpers.jsx'

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

const me = {
  'GET /api/auth/me': [200, ALICE],
  'GET /api/studies/1/like': [200, { liked: false, like_count: 0 }],
  'GET /api/errors/3/like': [200, { liked: false, like_count: 0 }],
}
const type = (label, value) => fireEvent.change(screen.getByLabelText(label), { target: { value } })
const click = (name) => fireEvent.click(screen.getByRole('button', { name }))

const study = (extra = {}) => ({
  id: 1,
  title: '공개 공부',
  content: '내용',
  is_public: true,
  created_at: '2026-10-27T01:00:00Z',
  updated_at: null,
  author_nickname: 'alice',
  is_mine: true,
  ...extra,
})
const comment = (id, content, extra = {}) => ({
  id,
  content,
  author_nickname: 'bobby',
  is_mine: false,
  can_delete: false,
  created_at: '2026-10-27T02:00:00Z',
  updated_at: null,
  ...extra,
})
const page = (...items) => [200, { items }]
const LIST = 'GET /api/studies/1/comments'

describe('댓글 영역', () => {
  it('공개된 공부 기록에서는 댓글을 서버가 보낸 순서(오래된 순)대로 보여준다', async () => {
    mockApi({ ...me, 'GET /api/studies/1': [200, study()], [LIST]: page(comment(1, '첫 댓글'), comment(2, '둘째 댓글')) })
    renderApp('/studies/1')
    expect(await screen.findByRole('heading', { name: '댓글 (2)' })).toBeTruthy()
    const bodies = screen.getAllByText(/댓글$/, { selector: '.record-body' }).map((n) => n.textContent)
    expect(bodies).toEqual(['첫 댓글', '둘째 댓글'])
  })

  it('비공개 기록에는 댓글 영역이 보이지 않고 댓글을 요청하지도 않는다', async () => {
    const { fn } = mockApi({ ...me, 'GET /api/studies/1': [200, study({ is_public: false })] })
    renderApp('/studies/1')
    await screen.findByRole('heading', { name: /공개 공부/ })
    expect(screen.queryByRole('heading', { name: /^댓글/ })).toBeNull()
    expect(fn.mock.calls.some(([url]) => String(url).includes('/comments'))).toBe(false)
  })

  it('오류 기록에서도 댓글을 보여준다', async () => {
    mockApi({
      ...me,
      'GET /api/errors/3': [
        200,
        { id: 3, title: '오류', content: '내용', solution: null, is_resolved: false, is_public: true, created_at: '2026-10-27T01:00:00Z', updated_at: null, resolved_at: null, author_nickname: 'alice', is_mine: true },
      ],
      'GET /api/errors/3/comments': page(comment(1, '오류 댓글')),
    })
    renderApp('/errors/3')
    expect(await screen.findByText('오류 댓글')).toBeTruthy()
  })

  it('댓글이 없으면 안내를 보여준다', async () => {
    mockApi({ ...me, 'GET /api/studies/1': [200, study()], [LIST]: page() })
    renderApp('/studies/1')
    expect(await screen.findByText('아직 댓글이 없습니다.')).toBeTruthy()
  })

  it('댓글을 불러오지 못하면 안내를 보여준다', async () => {
    mockApi({ ...me, 'GET /api/studies/1': [200, study()], [LIST]: new Error('network') })
    renderApp('/studies/1')
    expect(await screen.findByText(/댓글을 불러오지 못했습니다/)).toBeTruthy()
  })
})

describe('댓글 쓰기', () => {
  it('등록하면 입력칸을 비우고 목록을 다시 받아 온다', async () => {
    let items = []
    const { calls } = mockApi({
      ...me,
      'GET /api/studies/1': [200, study()],
      [LIST]: () => page(...items),
      'POST /api/studies/1/comments': (body) => {
        items = [comment(1, body.content, { author_nickname: 'alice', is_mine: true, can_delete: true })]
        return [201, items[0]]
      },
    })
    renderApp('/studies/1')
    await screen.findByText('아직 댓글이 없습니다.')
    type('댓글 쓰기', '새 댓글입니다')
    click('댓글 등록')
    expect(await screen.findByText('새 댓글입니다')).toBeTruthy()
    expect(screen.getByLabelText('댓글 쓰기').value).toBe('')
    expect(calls.find((c) => c.key === 'POST /api/studies/1/comments').body).toEqual({ content: '새 댓글입니다' })
  })

  it('실패하면 쓰던 댓글을 그대로 두고 안내를 보여준다', async () => {
    mockApi({
      ...me,
      'GET /api/studies/1': [200, study()],
      [LIST]: page(),
      'POST /api/studies/1/comments': [422, { errors: { content: '댓글은 1자 이상 500자 이하로 입력해 주세요.' } }],
    })
    renderApp('/studies/1')
    await screen.findByText('아직 댓글이 없습니다.')
    type('댓글 쓰기', '   ')
    click('댓글 등록')
    expect(await screen.findByText('댓글은 1자 이상 500자 이하로 입력해 주세요.')).toBeTruthy()
    expect(screen.getByLabelText('댓글 쓰기').value).toBe('   ')
  })

  it('서버에 연결하지 못해도 쓰던 댓글을 그대로 둔다', async () => {
    mockApi({ ...me, 'GET /api/studies/1': [200, study()], [LIST]: page(), 'POST /api/studies/1/comments': new Error('network') })
    renderApp('/studies/1')
    await screen.findByText('아직 댓글이 없습니다.')
    type('댓글 쓰기', '쓰던 댓글')
    click('댓글 등록')
    expect(await screen.findByText(/서버에 연결하지 못했습니다/)).toBeTruthy()
    expect(screen.getByLabelText('댓글 쓰기').value).toBe('쓰던 댓글')
  })
})

describe('댓글 수정·삭제 권한 표시', () => {
  const setup = () =>
    mockApi({
      ...me,
      'GET /api/studies/1': [200, study({ is_mine: false })],
      [LIST]: page(
        comment(1, '내 댓글', { author_nickname: 'alice', is_mine: true, can_delete: true }),
        comment(2, '남의 댓글', { is_mine: false, can_delete: false }),
      ),
    })

  it('내 댓글에만 수정·삭제 버튼이 있고 남의 댓글에는 없다', async () => {
    setup()
    renderApp('/studies/1')
    const mine = (await screen.findByText('내 댓글')).closest('article')
    const others = screen.getByText('남의 댓글').closest('article')
    expect(within(mine).getByRole('button', { name: '수정' })).toBeTruthy()
    expect(within(mine).getByRole('button', { name: '삭제' })).toBeTruthy()
    expect(within(others).queryByRole('button', { name: '수정' })).toBeNull()
    expect(within(others).queryByRole('button', { name: '삭제' })).toBeNull()
  })

  it('기록 작성자는 남의 댓글에 삭제 버튼만 보인다', async () => {
    mockApi({
      ...me,
      'GET /api/studies/1': [200, study()],
      [LIST]: page(comment(2, '남의 댓글', { is_mine: false, can_delete: true })),
    })
    renderApp('/studies/1')
    const article = (await screen.findByText('남의 댓글')).closest('article')
    expect(within(article).queryByRole('button', { name: '수정' })).toBeNull()
    expect(within(article).getByRole('button', { name: '삭제' })).toBeTruthy()
  })
})

describe('댓글 수정', () => {
  it('수정하면 수정 요청을 보내고 목록을 다시 받아 온다', async () => {
    let content = '원래 댓글'
    const { calls } = mockApi({
      ...me,
      'GET /api/studies/1': [200, study()],
      [LIST]: () => page(comment(1, content, { author_nickname: 'alice', is_mine: true, can_delete: true })),
      'PUT /api/comments/1': (body) => {
        content = body.content
        return [200, comment(1, content)]
      },
    })
    renderApp('/studies/1')
    await screen.findByText('원래 댓글')
    click('수정')
    expect(screen.getByLabelText('댓글 수정').value).toBe('원래 댓글')
    type('댓글 수정', '고친 댓글')
    click('수정 저장')
    expect(await screen.findByText('고친 댓글')).toBeTruthy()
    expect(calls.find((c) => c.key === 'PUT /api/comments/1').body).toEqual({ content: '고친 댓글' })
  })

  it('수정에 실패하면 고치던 내용을 그대로 두고, 취소하면 원래 댓글이 보인다', async () => {
    mockApi({
      ...me,
      'GET /api/studies/1': [200, study()],
      [LIST]: page(comment(1, '원래 댓글', { author_nickname: 'alice', is_mine: true, can_delete: true })),
      'PUT /api/comments/1': [422, { errors: { content: '댓글은 1자 이상 500자 이하로 입력해 주세요.' } }],
    })
    renderApp('/studies/1')
    await screen.findByText('원래 댓글')
    click('수정')
    type('댓글 수정', '')
    click('수정 저장')
    expect(await screen.findByText('댓글은 1자 이상 500자 이하로 입력해 주세요.')).toBeTruthy()
    expect(screen.getByLabelText('댓글 수정').value).toBe('')
    click('수정 취소')
    expect(screen.getByText('원래 댓글')).toBeTruthy()
  })
})

describe('댓글 삭제', () => {
  const comments = [comment(1, '지울 댓글', { author_nickname: 'alice', is_mine: true, can_delete: true })]

  it('확인창에서 취소하면 삭제하지 않는다', async () => {
    const { fn } = mockApi({ ...me, 'GET /api/studies/1': [200, study()], [LIST]: page(...comments) })
    renderApp('/studies/1')
    await screen.findByText('지울 댓글')
    fireEvent.click(within(screen.getByText('지울 댓글').closest('article')).getByRole('button', { name: '삭제' }))
    fireEvent.click(within(screen.getByRole('alertdialog')).getByRole('button', { name: '취소' }))
    expect(fn.mock.calls.some(([, o]) => o?.method === 'DELETE')).toBe(false)
    expect(screen.getByText('지울 댓글')).toBeTruthy()
  })

  it('확인창에서 삭제하면 삭제 요청을 보내고 목록을 다시 받아 온다', async () => {
    let deleted = false
    const { fn } = mockApi({
      ...me,
      'GET /api/studies/1': [200, study()],
      [LIST]: () => page(...(deleted ? [] : comments)),
      'DELETE /api/comments/1': () => {
        deleted = true
        return [204, null]
      },
    })
    renderApp('/studies/1')
    await screen.findByText('지울 댓글')
    fireEvent.click(within(screen.getByText('지울 댓글').closest('article')).getByRole('button', { name: '삭제' }))
    fireEvent.click(within(screen.getByRole('alertdialog')).getByRole('button', { name: '삭제' }))
    await waitFor(() => expect(screen.queryByText('지울 댓글')).toBeNull())
    expect(fn.mock.calls.some(([u, o]) => u === '/api/comments/1' && o?.method === 'DELETE')).toBe(true)
  })

  it('삭제에 실패하면 댓글을 그대로 두고 안내를 보여준다', async () => {
    mockApi({ ...me, 'GET /api/studies/1': [200, study()], [LIST]: page(...comments), 'DELETE /api/comments/1': new Error('network') })
    renderApp('/studies/1')
    await screen.findByText('지울 댓글')
    fireEvent.click(within(screen.getByText('지울 댓글').closest('article')).getByRole('button', { name: '삭제' }))
    fireEvent.click(within(screen.getByRole('alertdialog')).getByRole('button', { name: '삭제' }))
    expect(await screen.findByText(/댓글을 삭제하지 못했습니다/)).toBeTruthy()
    expect(screen.getByText('지울 댓글')).toBeTruthy()
  })
})
