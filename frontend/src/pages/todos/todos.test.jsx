import { cleanup, fireEvent, screen, waitFor, within } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { ALICE, mockApi, renderApp } from '../../test/helpers.jsx'

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

const me = { 'GET /api/auth/me': [200, ALICE] }
const type = (label, value) => fireEvent.change(screen.getByLabelText(label), { target: { value } })
const click = (name) => fireEvent.click(screen.getByRole('button', { name }))

const todo = (id, title, extra = {}) => ({
  id,
  title,
  is_done: false,
  is_public: false,
  created_at: '2026-10-27T01:00:00Z',
  updated_at: null,
  completed_at: null,
  author_nickname: 'alice',
  is_mine: true,
  ...extra,
})
const list = (...items) => [200, { items }]

describe('할 일 목록', () => {
  it('서버가 보낸 순서(미완료 먼저)대로 보여주고 완료 항목에는 완료 시각을 보여준다', async () => {
    mockApi({
      ...me,
      'GET /api/todos?filter=all': list(todo(2, '남은 일'), todo(1, '끝낸 일', { is_done: true, completed_at: '2026-10-27T02:00:00Z' })),
    })
    renderApp('/todos')
    const boxes = await screen.findAllByRole('checkbox')
    expect(boxes.map((b) => b.checked)).toEqual([false, true])
    expect(screen.getByText(/완료 /, { selector: 'p.hint' })).toBeTruthy()
    expect(screen.getByText('끝낸 일').closest('article').className).toContain('todo-done')
  })

  it('수정한 시각이 있으면 목록 항목에 보여준다', async () => {
    mockApi({ ...me, 'GET /api/todos?filter=all': list(todo(1, '고친 일', { updated_at: '2026-10-28T01:00:00Z' })) })
    renderApp('/todos')
    expect(await screen.findByText(/수정 /, { selector: 'p.hint' })).toBeTruthy()
  })

  it('세 가지 보기 버튼이 해당 필터로 목록을 다시 받아 온다', async () => {
    const { calls } = mockApi({
      ...me,
      'GET /api/todos?filter=all': list(todo(2, '남은 일'), todo(1, '끝낸 일', { is_done: true, completed_at: '2026-10-27T02:00:00Z' })),
      'GET /api/todos?filter=open': list(todo(2, '남은 일')),
      'GET /api/todos?filter=done': list(todo(1, '끝낸 일', { is_done: true, completed_at: '2026-10-27T02:00:00Z' })),
    })
    renderApp('/todos')
    await screen.findByText('끝낸 일')
    expect(screen.getByRole('button', { name: '전체' }).getAttribute('aria-pressed')).toBe('true')

    click('남은 일')
    await waitFor(() => expect(screen.queryByText('끝낸 일')).toBeNull())
    expect(screen.getByText('남은 일', { selector: 'span' })).toBeTruthy()
    expect(screen.getByRole('button', { name: '남은 일' }).getAttribute('aria-pressed')).toBe('true')

    click('완료한 일')
    await waitFor(() => expect(screen.queryByText('남은 일', { selector: 'span' })).toBeNull())
    expect(screen.getByText('끝낸 일')).toBeTruthy()
    expect(calls.map((c) => c.key)).toEqual(expect.arrayContaining(['GET /api/todos?filter=open', 'GET /api/todos?filter=done']))
  })

  it('항목이 없으면 보기에 맞는 안내를 보여준다', async () => {
    mockApi({ ...me, 'GET /api/todos?filter=all': list(), 'GET /api/todos?filter=open': list(), 'GET /api/todos?filter=done': list() })
    renderApp('/todos')
    expect(await screen.findByText(/아직 할 일이 없습니다/)).toBeTruthy()
    click('남은 일')
    expect(await screen.findByText('남은 일이 없습니다.')).toBeTruthy()
    click('완료한 일')
    expect(await screen.findByText('완료한 일이 없습니다.')).toBeTruthy()
  })

  it('목록을 불러오지 못하면 실패 안내를 보여준다', async () => {
    mockApi({ ...me, 'GET /api/todos?filter=all': new Error('network') })
    renderApp('/todos')
    expect(await screen.findByText(/목록을 불러오지 못했습니다/)).toBeTruthy()
  })

  it('검색 입력칸이 없다 (내 할 일 검색은 첫 버전에 없음)', async () => {
    mockApi({ ...me, 'GET /api/todos?filter=all': list(todo(1, '일')) })
    renderApp('/todos')
    await screen.findByText('일')
    expect(screen.queryByRole('search')).toBeNull()
    expect(screen.queryByRole('searchbox')).toBeNull()
  })
})

describe('완료 체크', () => {
  it('체크하면 완료 요청을 보내고 목록을 다시 받아 온다', async () => {
    let done = false
    const { calls } = mockApi({
      ...me,
      'GET /api/todos?filter=all': () => list(todo(1, '일', { is_done: done, completed_at: done ? '2026-10-27T02:00:00Z' : null })),
      'PUT /api/todos/1/done': (body) => {
        done = body.is_done
        return [200, todo(1, '일', { is_done: done })]
      },
    })
    renderApp('/todos')
    const box = await screen.findByRole('checkbox')
    fireEvent.click(box)
    await waitFor(() => expect(screen.getByRole('checkbox').checked).toBe(true))
    expect(calls.find((c) => c.key === 'PUT /api/todos/1/done').body).toEqual({ is_done: true })

    fireEvent.click(screen.getByRole('checkbox'))
    await waitFor(() => expect(screen.getByRole('checkbox').checked).toBe(false))
    expect(calls.filter((c) => c.key === 'PUT /api/todos/1/done').at(-1).body).toEqual({ is_done: false })
  })

  it('실패하면 기존 상태를 그대로 두고 이유를 알려준다', async () => {
    mockApi({
      ...me,
      'GET /api/todos?filter=all': list(todo(1, '일')),
      'PUT /api/todos/1/done': new Error('network'),
    })
    renderApp('/todos')
    fireEvent.click(await screen.findByRole('checkbox'))
    expect(await screen.findByText(/완료 상태를 바꾸지 못했습니다/)).toBeTruthy()
    expect(screen.getByRole('checkbox').checked).toBe(false)
  })
})

describe('할 일 쓰기', () => {
  it('기본은 비공개이고, 저장에 성공하면 목록으로 이동한다', async () => {
    const { calls } = mockApi({
      ...me,
      'POST /api/todos': [201, todo(1, '저장 버튼 만들기')],
      'GET /api/todos?filter=all': list(todo(1, '저장 버튼 만들기')),
    })
    renderApp('/todos/new')
    await screen.findByRole('heading', { name: '새 할 일' })
    expect(screen.getByLabelText(/^공개/).checked).toBe(false)
    type('제목', '저장 버튼 만들기')
    click('저장')
    expect(await screen.findByRole('heading', { name: '할 일' })).toBeTruthy()
    expect(calls.find((c) => c.key === 'POST /api/todos').body).toEqual({ title: '저장 버튼 만들기', is_public: false })
  })

  it('저장에 실패하면 입력한 제목과 공개 선택을 그대로 둔다', async () => {
    mockApi({
      ...me,
      'POST /api/todos': [422, { errors: { title: '제목은 1자 이상 100자 이하로 입력해 주세요.' } }],
    })
    renderApp('/todos/new')
    await screen.findByRole('heading', { name: '새 할 일' })
    type('제목', '   ')
    fireEvent.click(screen.getByLabelText(/^공개/))
    click('저장')
    expect(await screen.findByText(/제목은 1자 이상 100자 이하/)).toBeTruthy()
    expect(screen.getByLabelText('제목').value).toBe('   ')
    expect(screen.getByLabelText(/^공개/).checked).toBe(true)
  })
})

describe('할 일 수정', () => {
  it('기존 값이 채워져 있고 저장하면 수정 요청 후 목록으로 이동한다', async () => {
    const { calls } = mockApi({
      ...me,
      'GET /api/todos/1': [200, todo(1, '원래 제목', { is_public: true })],
      'PUT /api/todos/1': [200, todo(1, '새 제목')],
      'GET /api/todos?filter=all': list(),
    })
    renderApp('/todos/1/edit')
    await screen.findByRole('heading', { name: '할 일 수정' })
    expect(screen.getByLabelText('제목').value).toBe('원래 제목')
    expect(screen.getByLabelText(/^공개/).checked).toBe(true)
    type('제목', '새 제목')
    click('저장')
    expect(await screen.findByRole('heading', { name: '할 일' })).toBeTruthy()
    expect(calls.find((c) => c.key === 'PUT /api/todos/1').body).toEqual({ title: '새 제목', is_public: true })
  })

  it('수정에 실패하면 고치던 제목을 그대로 둔다', async () => {
    mockApi({
      ...me,
      'GET /api/todos/1': [200, todo(1, '원래 제목')],
      'PUT /api/todos/1': new Error('network'),
    })
    renderApp('/todos/1/edit')
    await screen.findByRole('heading', { name: '할 일 수정' })
    type('제목', '고치는 중')
    click('저장')
    expect(await screen.findByText(/서버에 연결하지 못했습니다/)).toBeTruthy()
    expect(screen.getByLabelText('제목').value).toBe('고치는 중')
  })

  it('작성자가 아니면 수정 양식을 보여주지 않는다', async () => {
    mockApi({ ...me, 'GET /api/todos/7': [200, todo(7, '남의 일', { is_mine: false, is_public: true })] })
    renderApp('/todos/7/edit')
    expect(await screen.findByText('작성자만 수정할 수 있습니다.')).toBeTruthy()
    expect(screen.queryByLabelText('제목')).toBeNull()
  })
})

describe('할 일 삭제', () => {
  const setup = (extra = {}) =>
    mockApi({ ...me, 'GET /api/todos?filter=all': list(todo(1, '지울 일')), ...extra })

  it('확인창에서 취소하면 삭제하지 않는다', async () => {
    const { fn } = setup()
    renderApp('/todos')
    await screen.findByText('지울 일')
    click('삭제')
    fireEvent.click(within(screen.getByRole('alertdialog')).getByRole('button', { name: '취소' }))
    expect(screen.queryByRole('alertdialog')).toBeNull()
    expect(fn.mock.calls.some(([, o]) => o?.method === 'DELETE')).toBe(false)
    expect(screen.getByText('지울 일')).toBeTruthy()
  })

  it('확인창에서 삭제하면 삭제하고 목록을 다시 받아 온다', async () => {
    let deleted = false
    const { fn } = setup({
      'GET /api/todos?filter=all': () => list(...(deleted ? [] : [todo(1, '지울 일')])),
      'DELETE /api/todos/1': () => {
        deleted = true
        return [204, null]
      },
    })
    renderApp('/todos')
    await screen.findByText('지울 일')
    click('삭제')
    fireEvent.click(within(screen.getByRole('alertdialog')).getByRole('button', { name: '삭제' }))
    await waitFor(() => expect(screen.queryByText('지울 일')).toBeNull())
    expect(fn.mock.calls.some(([u, o]) => u === '/api/todos/1' && o?.method === 'DELETE')).toBe(true)
  })

  it('삭제에 실패하면 할 일을 그대로 두고 안내를 보여준다', async () => {
    setup({ 'DELETE /api/todos/1': new Error('network') })
    renderApp('/todos')
    await screen.findByText('지울 일')
    click('삭제')
    fireEvent.click(within(screen.getByRole('alertdialog')).getByRole('button', { name: '삭제' }))
    expect(await screen.findByText(/삭제하지 못했습니다/)).toBeTruthy()
    expect(screen.getByText('지울 일')).toBeTruthy()
  })
})
