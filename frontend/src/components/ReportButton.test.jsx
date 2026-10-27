import { cleanup, fireEvent, screen, within } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { ALICE, mockApi, renderApp } from '../test/helpers.jsx'

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

const click = (name, root = screen) => fireEvent.click(root.getByRole('button', { name }))
const type = (label, value) => fireEvent.change(screen.getByLabelText(label), { target: { value } })

const study = (extra = {}) => ({
  id: 1,
  title: '남의 공개 공부',
  content: '내용',
  is_public: true,
  created_at: '2026-10-27T01:00:00Z',
  updated_at: null,
  author_nickname: 'bobby',
  is_mine: false,
  ...extra,
})
const base = {
  'GET /api/auth/me': [200, ALICE],
  'GET /api/studies/1/like': [200, { liked: false, like_count: 0 }],
  'GET /api/studies/1/comments': [200, { items: [] }],
}

async function openDialog() {
  await screen.findByRole('heading', { name: /남의 공개 공부/ })
  fireEvent.click(screen.getByRole('button', { name: '신고' }))
  return screen.getByRole('dialog')
}

describe('신고 버튼', () => {
  it('다른 사람의 공개 기록에는 신고 버튼이 보인다', async () => {
    mockApi({ ...base, 'GET /api/studies/1': [200, study()] })
    renderApp('/studies/1')
    await screen.findByRole('heading', { name: /남의 공개 공부/ })
    expect(screen.getByRole('button', { name: '신고' })).toBeTruthy()
  })

  it('내 기록에는 신고 버튼이 없다', async () => {
    mockApi({ ...base, 'GET /api/studies/1': [200, study({ is_mine: true })] })
    renderApp('/studies/1')
    await screen.findByRole('heading', { name: /남의 공개 공부/ })
    expect(screen.queryByRole('button', { name: '신고' })).toBeNull()
  })

  it('이유를 적어 신고하면 접수 안내를 보여주고 창을 닫는다', async () => {
    const { calls } = mockApi({
      ...base,
      'GET /api/studies/1': [200, study()],
      'POST /api/reports': [201, { message: '신고가 접수되었습니다.' }],
    })
    renderApp('/studies/1')
    const dialog = await openDialog()
    type('신고 이유', '  욕설이 있습니다  ')
    click('신고하기', within(dialog))
    expect(await screen.findByText('신고가 접수되었습니다.')).toBeTruthy()
    expect(screen.queryByRole('dialog')).toBeNull()
    expect(calls.find((c) => c.key === 'POST /api/reports').body).toEqual({
      target_type: 'study',
      target_id: 1,
      reason: '  욕설이 있습니다  ',
    })
    // 신고해도 기록은 그대로 보인다.
    expect(screen.getByRole('heading', { name: /남의 공개 공부/ })).toBeTruthy()
  })

  it('이유가 규칙에 맞지 않으면 안내를 보여주고 적은 내용을 그대로 둔다', async () => {
    mockApi({
      ...base,
      'GET /api/studies/1': [200, study()],
      'POST /api/reports': [422, { errors: { reason: '신고 이유는 1자 이상 500자 이하로 입력해 주세요.' } }],
    })
    renderApp('/studies/1')
    const dialog = await openDialog()
    type('신고 이유', '   ')
    click('신고하기', within(dialog))
    expect(await screen.findByText('신고 이유는 1자 이상 500자 이하로 입력해 주세요.')).toBeTruthy()
    expect(screen.getByLabelText('신고 이유').value).toBe('   ')
    expect(screen.getByRole('dialog')).toBeTruthy()
  })

  it('이미 신고한 대상이면 그렇게 알려주고 적은 이유를 그대로 둔다', async () => {
    mockApi({
      ...base,
      'GET /api/studies/1': [200, study()],
      'POST /api/reports': [409, { errors: { target: '이미 신고한 대상입니다.' } }],
    })
    renderApp('/studies/1')
    const dialog = await openDialog()
    type('신고 이유', '또 신고')
    click('신고하기', within(dialog))
    expect(await screen.findByText('이미 신고한 대상입니다.')).toBeTruthy()
    expect(screen.getByLabelText('신고 이유').value).toBe('또 신고')
  })

  it('서버에 연결하지 못해도 적은 이유를 그대로 둔다', async () => {
    mockApi({ ...base, 'GET /api/studies/1': [200, study()], 'POST /api/reports': new Error('network') })
    renderApp('/studies/1')
    const dialog = await openDialog()
    type('신고 이유', '이유')
    click('신고하기', within(dialog))
    expect(await screen.findByText(/서버에 연결하지 못했습니다/)).toBeTruthy()
    expect(screen.getByLabelText('신고 이유').value).toBe('이유')
  })

  it('취소하면 신고하지 않고 창을 닫는다', async () => {
    const { fn } = mockApi({ ...base, 'GET /api/studies/1': [200, study()] })
    renderApp('/studies/1')
    const dialog = await openDialog()
    click('취소', within(dialog))
    expect(screen.queryByRole('dialog')).toBeNull()
    expect(fn.mock.calls.some(([u]) => u === '/api/reports')).toBe(false)
  })
})

describe('댓글과 공개 할 일 신고', () => {
  const comment = (id, extra = {}) => ({
    id,
    content: `댓글 ${id}`,
    author_nickname: 'bobby',
    is_mine: false,
    can_delete: false,
    created_at: '2026-10-27T02:00:00Z',
    updated_at: null,
    ...extra,
  })

  it('남의 댓글에만 신고 버튼이 있고 내 댓글에는 없다', async () => {
    mockApi({
      ...base,
      'GET /api/studies/1': [200, study()],
      'GET /api/studies/1/comments': [200, { items: [comment(1), comment(2, { is_mine: true, can_delete: true })] }],
    })
    renderApp('/studies/1')
    const others = (await screen.findByText('댓글 1')).closest('article')
    const mine = screen.getByText('댓글 2').closest('article')
    expect(within(others).getByRole('button', { name: '신고' })).toBeTruthy()
    expect(within(mine).queryByRole('button', { name: '신고' })).toBeNull()
  })

  it('댓글을 신고하면 댓글 번호로 요청하고, 댓글은 그대로 남는다', async () => {
    const { calls } = mockApi({
      ...base,
      'GET /api/studies/1': [200, study()],
      'GET /api/studies/1/comments': [200, { items: [comment(7)] }],
      'POST /api/reports': [201, { message: '신고가 접수되었습니다.' }],
    })
    renderApp('/studies/1')
    const article = (await screen.findByText('댓글 7')).closest('article')
    fireEvent.click(within(article).getByRole('button', { name: '신고' }))
    type('신고 이유', '광고')
    click('신고하기', within(screen.getByRole('dialog')))
    expect(await screen.findByText('신고가 접수되었습니다.')).toBeTruthy()
    expect(calls.find((c) => c.key === 'POST /api/reports').body).toMatchObject({ target_type: 'comment', target_id: 7 })
    expect(screen.getByText('댓글 7')).toBeTruthy()
  })

  it('공개 기록 화면에서 남의 할 일을 바로 신고할 수 있다', async () => {
    const { calls } = mockApi({
      'GET /api/auth/me': [200, ALICE],
      'GET /api/public?kind=all': [
        200,
        {
          items: [
            { kind: 'todo', id: 5, title: '남의 할 일', preview: null, author_nickname: 'bobby', is_mine: false, created_at: '2026-10-27T01:00:00Z', is_done: false },
            { kind: 'todo', id: 6, title: '내 할 일', preview: null, author_nickname: 'alice', is_mine: true, created_at: '2026-10-27T01:00:00Z', is_done: false },
          ],
        },
      ],
      'POST /api/reports': [201, { message: '신고가 접수되었습니다.' }],
    })
    renderApp('/public')
    const others = (await screen.findByText('남의 할 일')).closest('article')
    expect(within(screen.getByText('내 할 일').closest('article')).queryByRole('button', { name: '신고' })).toBeNull()
    fireEvent.click(within(others).getByRole('button', { name: '신고' }))
    type('신고 이유', '부적절')
    click('신고하기', within(screen.getByRole('dialog')))
    expect(await screen.findByText('신고가 접수되었습니다.')).toBeTruthy()
    expect(calls.find((c) => c.key === 'POST /api/reports').body).toMatchObject({ target_type: 'todo', target_id: 5 })
  })

  it('신고 내용을 보여주는 화면이나 메뉴가 없다', async () => {
    mockApi({ 'GET /api/auth/me': [200, ALICE], 'GET /api/public?kind=all': [200, { items: [] }] })
    renderApp('/public')
    await screen.findByText('아직 공개된 기록이 없습니다.')
    expect(screen.queryByRole('link', { name: /신고/ })).toBeNull()
  })
})
