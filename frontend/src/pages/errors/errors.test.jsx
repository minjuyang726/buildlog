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

const record = (extra = {}) => ({
  id: 1,
  title: 'ModuleNotFoundError',
  content: "No module named 'requests'",
  solution: null,
  is_resolved: false,
  is_public: false,
  created_at: '2026-10-27T01:00:00Z',
  updated_at: null,
  resolved_at: null,
  author_nickname: 'alice',
  is_mine: true,
  ...extra,
})
const item = (id, title, extra = {}) => ({
  id,
  title,
  preview: `${title} 내용`,
  is_resolved: false,
  is_public: false,
  created_at: '2026-10-27T01:00:00Z',
  updated_at: null,
  resolved_at: null,
  ...extra,
})
const list = (...items) => [200, { items }]
const ALL = 'GET /api/errors?filter=all'

describe('오류 기록 목록', () => {
  it('해결 여부와 공개 여부를 보여준다', async () => {
    mockApi({ ...me, [ALL]: list(item(2, '해결한 오류', { is_resolved: true, resolved_at: '2026-10-27T03:00:00Z' }), item(1, '못 푼 오류')) })
    renderApp('/errors')
    const first = await screen.findByRole('heading', { level: 2, name: /해결한 오류/ })
    expect(first.textContent).toContain('해결')
    expect(screen.getByRole('heading', { level: 2, name: /못 푼 오류/ }).textContent).toContain('미해결')
    expect(screen.getByText(/해결 /, { selector: 'p.hint' })).toBeTruthy()
  })

  it('세 가지 보기 버튼이 해당 필터로 다시 받아 온다', async () => {
    const { calls } = mockApi({
      ...me,
      [ALL]: list(item(2, '해결한 오류', { is_resolved: true }), item(1, '못 푼 오류')),
      'GET /api/errors?filter=unresolved': list(item(1, '못 푼 오류')),
      'GET /api/errors?filter=resolved': list(item(2, '해결한 오류', { is_resolved: true })),
    })
    renderApp('/errors')
    await screen.findByText('해결한 오류')
    click('미해결')
    await waitFor(() => expect(screen.queryByText('해결한 오류')).toBeNull())
    expect(screen.getByText('못 푼 오류')).toBeTruthy()
    click('해결')
    await waitFor(() => expect(screen.queryByText('못 푼 오류')).toBeNull())
    expect(screen.getByText('해결한 오류')).toBeTruthy()
    expect(calls.map((c) => c.key)).toEqual(expect.arrayContaining(['GET /api/errors?filter=unresolved', 'GET /api/errors?filter=resolved']))
  })

  it('검색하면 보기 방식과 함께 검색어를 보낸다', async () => {
    const q = encodeURIComponent('requests')
    const { calls } = mockApi({
      ...me,
      [ALL]: list(item(1, '다른 오류'), item(2, 'import 오류')),
      [`GET /api/errors?filter=all&q=${q}`]: list(item(2, 'import 오류')),
    })
    renderApp('/errors')
    await screen.findByText('다른 오류')
    type('오류 기록 검색', ' requests ')
    click('검색')
    await waitFor(() => expect(screen.queryByText('다른 오류')).toBeNull())
    expect(screen.getByText('import 오류')).toBeTruthy()
    expect(calls.some((c) => c.key === `GET /api/errors?filter=all&q=${q}`)).toBe(true)
  })

  it('검색 결과가 없으면 안내를 보여준다', async () => {
    mockApi({ ...me, [ALL]: list(item(1, '오류')), [`GET /api/errors?filter=all&q=${encodeURIComponent('없음')}`]: list() })
    renderApp('/errors')
    await screen.findByText('오류')
    type('오류 기록 검색', '없음')
    click('검색')
    expect(await screen.findByText('검색 결과가 없습니다.')).toBeTruthy()
  })

  it('목록을 불러오지 못하면 실패 안내를 보여준다', async () => {
    mockApi({ ...me, [ALL]: new Error('network') })
    renderApp('/errors')
    expect(await screen.findByText(/목록을 불러오지 못했습니다/)).toBeTruthy()
  })
})

describe('오류 기록 쓰기', () => {
  it('해결 방법 없이 미해결로 저장할 수 있고, 성공하면 목록으로 이동한다', async () => {
    const { calls } = mockApi({ ...me, 'POST /api/errors': [201, record()], [ALL]: list(item(1, 'ModuleNotFoundError')) })
    renderApp('/errors/new')
    await screen.findByRole('heading', { name: '새 오류 기록' })
    expect(screen.getByLabelText(/^공개/).checked).toBe(false)
    expect(screen.getByLabelText('해결했습니다').checked).toBe(false)
    type('오류 제목', 'ModuleNotFoundError')
    type('오류 내용', "No module named 'requests'")
    click('저장')
    expect(await screen.findByRole('heading', { name: '오류 기록' })).toBeTruthy()
    expect(calls.find((c) => c.key === 'POST /api/errors').body).toEqual({
      title: 'ModuleNotFoundError',
      content: "No module named 'requests'",
      solution: '',
      is_resolved: false,
      is_public: false,
    })
  })

  it('해결로 표시했는데 해결 방법이 없으면 해결 방법 칸에 안내를 보여주고 입력은 그대로 둔다', async () => {
    mockApi({
      ...me,
      'POST /api/errors': [422, { errors: { solution: '해결 방법을 입력해야 해결 상태로 바꿀 수 있습니다.' } }],
    })
    renderApp('/errors/new')
    await screen.findByRole('heading', { name: '새 오류 기록' })
    type('오류 제목', '제목')
    type('오류 내용', '쓰던 내용')
    fireEvent.click(screen.getByLabelText('해결했습니다'))
    click('저장')
    const message = await screen.findByText('해결 방법을 입력해야 해결 상태로 바꿀 수 있습니다.')
    expect(message.id).toBe('solution-error')
    expect(screen.getByLabelText('오류 내용').value).toBe('쓰던 내용')
    expect(screen.getByLabelText('해결했습니다').checked).toBe(true)
  })

  it('서버에 연결하지 못해도 입력한 내용을 그대로 둔다', async () => {
    mockApi({ ...me, 'POST /api/errors': new Error('network') })
    renderApp('/errors/new')
    await screen.findByRole('heading', { name: '새 오류 기록' })
    type('오류 제목', '제목')
    type('오류 내용', '내용')
    type('해결 방법', '방법')
    click('저장')
    expect(await screen.findByText(/서버에 연결하지 못했습니다/)).toBeTruthy()
    expect(screen.getByLabelText('해결 방법').value).toBe('방법')
  })
})

describe('오류 기록 읽기와 삭제', () => {
  it('해결 방법이 없으면 안내하고, 내 기록이면 수정·삭제 버튼이 보인다', async () => {
    mockApi({ ...me, 'GET /api/errors/1': [200, record()] })
    renderApp('/errors/1')
    expect(await screen.findByText('아직 해결 방법이 없습니다.')).toBeTruthy()
    expect(screen.getByRole('link', { name: /해결 방법 쓰기/ })).toBeTruthy()
    expect(screen.getByRole('button', { name: '삭제' })).toBeTruthy()
  })

  it('해결한 기록은 해결 방법과 해결 시각을 보여준다', async () => {
    mockApi({
      ...me,
      'GET /api/errors/1': [200, record({ is_resolved: true, solution: 'pip install requests', resolved_at: '2026-10-27T03:00:00Z' })],
    })
    renderApp('/errors/1')
    expect(await screen.findByText('pip install requests')).toBeTruthy()
    expect(screen.getByText(/해결 /, { selector: 'p.hint' })).toBeTruthy()
  })

  it('다른 사람의 공개 기록에는 수정·삭제 버튼이 없다', async () => {
    mockApi({ ...me, 'GET /api/errors/5': [200, record({ id: 5, is_mine: false, is_public: true, author_nickname: 'bobby' })] })
    renderApp('/errors/5')
    expect(await screen.findByText(/bobby/)).toBeTruthy()
    expect(screen.queryByRole('button', { name: '삭제' })).toBeNull()
    expect(screen.queryByRole('link', { name: /수정/ })).toBeNull()
  })

  it('볼 수 없는 기록이면 안내를 보여준다', async () => {
    mockApi({ ...me, 'GET /api/errors/9': [404, { detail: '기록을 찾을 수 없습니다.' }] })
    renderApp('/errors/9')
    expect(await screen.findByText('기록을 찾을 수 없습니다.')).toBeTruthy()
  })

  it('삭제 확인창에서 취소하면 삭제하지 않고, 삭제하면 목록으로 이동한다', async () => {
    const { fn } = mockApi({
      ...me,
      'GET /api/errors/1': [200, record()],
      'DELETE /api/errors/1': [204, null],
      [ALL]: list(),
    })
    renderApp('/errors/1')
    await screen.findByRole('heading', { name: /ModuleNotFoundError/ })
    click('삭제')
    fireEvent.click(within(screen.getByRole('alertdialog')).getByRole('button', { name: '취소' }))
    expect(fn.mock.calls.some(([, o]) => o?.method === 'DELETE')).toBe(false)

    click('삭제')
    fireEvent.click(within(screen.getByRole('alertdialog')).getByRole('button', { name: '삭제' }))
    expect(await screen.findByRole('heading', { name: '오류 기록' })).toBeTruthy()
    expect(fn.mock.calls.some(([u, o]) => u === '/api/errors/1' && o?.method === 'DELETE')).toBe(true)
  })

  it('삭제에 실패하면 기록을 그대로 두고 안내를 보여준다', async () => {
    mockApi({ ...me, 'GET /api/errors/1': [200, record()], 'DELETE /api/errors/1': new Error('network') })
    renderApp('/errors/1')
    await screen.findByRole('heading', { name: /ModuleNotFoundError/ })
    click('삭제')
    fireEvent.click(within(screen.getByRole('alertdialog')).getByRole('button', { name: '삭제' }))
    expect(await screen.findByText(/삭제하지 못했습니다/)).toBeTruthy()
    expect(screen.getByRole('heading', { name: /ModuleNotFoundError/ })).toBeTruthy()
  })
})

describe('오류 기록 수정', () => {
  it('기존 값이 채워져 있고, 해결 방법을 적어 해결로 바꾼 뒤 저장하면 목록으로 이동한다', async () => {
    const { calls } = mockApi({
      ...me,
      'GET /api/errors/1': [200, record()],
      'PUT /api/errors/1': [200, record({ is_resolved: true, solution: '설치함' })],
      [ALL]: list(),
    })
    renderApp('/errors/1/edit')
    await screen.findByRole('heading', { name: '오류 기록 수정' })
    expect(screen.getByLabelText('오류 제목').value).toBe('ModuleNotFoundError')
    expect(screen.getByLabelText('해결했습니다').checked).toBe(false)
    type('해결 방법', '설치함')
    fireEvent.click(screen.getByLabelText('해결했습니다'))
    click('저장')
    expect(await screen.findByRole('heading', { name: '오류 기록' })).toBeTruthy()
    expect(calls.find((c) => c.key === 'PUT /api/errors/1').body).toMatchObject({ solution: '설치함', is_resolved: true })
  })

  it('수정에 실패하면 고치던 입력값을 그대로 둔다', async () => {
    mockApi({
      ...me,
      'GET /api/errors/1': [200, record()],
      'PUT /api/errors/1': [422, { errors: { title: '오류 제목은 1자 이상 100자 이하로 입력해 주세요.' } }],
    })
    renderApp('/errors/1/edit')
    await screen.findByRole('heading', { name: '오류 기록 수정' })
    type('오류 제목', '')
    type('해결 방법', '쓰던 방법')
    click('저장')
    expect(await screen.findByText(/오류 제목은 1자 이상/)).toBeTruthy()
    expect(screen.getByLabelText('해결 방법').value).toBe('쓰던 방법')
  })

  it('작성자가 아니면 수정 양식을 보여주지 않는다', async () => {
    mockApi({ ...me, 'GET /api/errors/5': [200, record({ id: 5, is_mine: false, is_public: true })] })
    renderApp('/errors/5/edit')
    expect(await screen.findByText('작성자만 수정할 수 있습니다.')).toBeTruthy()
    expect(screen.queryByLabelText('오류 제목')).toBeNull()
  })
})
