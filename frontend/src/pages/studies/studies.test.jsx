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

const item = (id, title, extra = {}) => ({
  id,
  title,
  preview: `${title}의 내용`,
  is_public: false,
  created_at: '2026-10-27T01:00:00Z',
  updated_at: null,
  ...extra,
})
const study = (extra = {}) => ({
  id: 1,
  title: '파이썬 복습',
  content: '첫 줄\n둘째 줄',
  is_public: false,
  created_at: '2026-10-27T01:00:00Z',
  updated_at: null,
  author_nickname: 'alice',
  is_mine: true,
  ...extra,
})

describe('공부 기록 목록', () => {
  it('받아온 순서(최신순)대로 제목과 공개 여부를 보여준다', async () => {
    mockApi({ ...me, 'GET /api/studies': [200, { items: [item(2, '둘째 기록', { is_public: true }), item(1, '첫째 기록')] }] })
    renderApp('/studies')
    await screen.findByRole('heading', { level: 2, name: /둘째 기록/ })
    const titles = screen.getAllByRole('heading', { level: 2 }).map((h) => h.textContent)
    expect(titles[0]).toContain('둘째 기록')
    expect(titles[0]).toContain('공개')
    expect(titles[1]).toContain('첫째 기록')
    expect(titles[1]).toContain('비공개')
  })

  it('기록이 없으면 안내를 보여준다', async () => {
    mockApi({ ...me, 'GET /api/studies': [200, { items: [] }] })
    renderApp('/studies')
    expect(await screen.findByText(/아직 공부 기록이 없습니다/)).toBeTruthy()
  })

  it('검색어를 입력하면 검색 결과를 보여준다', async () => {
    const { calls } = mockApi({
      ...me,
      'GET /api/studies': [200, { items: [item(1, '자바'), item(2, '파이썬 기초')] }],
      [`GET /api/studies?q=${encodeURIComponent('파이썬')}`]: [200, { items: [item(2, '파이썬 기초')] }],
    })
    renderApp('/studies')
    await screen.findByText('자바')
    type('공부 기록 검색', '  파이썬  ')
    click('검색')
    await waitFor(() => expect(screen.queryByText('자바')).toBeNull())
    expect(screen.getByText('파이썬 기초')).toBeTruthy()
    expect(calls.some((c) => c.key === `GET /api/studies?q=${encodeURIComponent('파이썬')}`)).toBe(true)
  })

  it('검색 결과가 없으면 안내를 보여주고, 빈 검색어로 다시 검색하면 전체 목록이 나온다', async () => {
    mockApi({
      ...me,
      'GET /api/studies': [200, { items: [item(1, '자바')] }],
      [`GET /api/studies?q=${encodeURIComponent('없는단어')}`]: [200, { items: [] }],
    })
    renderApp('/studies')
    await screen.findByText('자바')
    type('공부 기록 검색', '없는단어')
    click('검색')
    expect(await screen.findByText('검색 결과가 없습니다.')).toBeTruthy()
    type('공부 기록 검색', '   ')
    click('검색')
    expect(await screen.findByText('자바')).toBeTruthy()
  })

  it('목록을 불러오지 못하면 실패 안내를 보여준다', async () => {
    mockApi({ ...me, 'GET /api/studies': new Error('network') })
    renderApp('/studies')
    expect(await screen.findByText(/목록을 불러오지 못했습니다/)).toBeTruthy()
  })
})

describe('공부 기록 쓰기', () => {
  it('공개 여부를 고르지 않으면 비공개로 저장하고, 성공하면 목록으로 이동한다', async () => {
    const { calls } = mockApi({
      ...me,
      'POST /api/studies': [201, study()],
      'GET /api/studies': [200, { items: [item(1, '파이썬 복습')] }],
    })
    renderApp('/studies/new')
    await screen.findByRole('heading', { name: '새 공부 기록' })
    expect(screen.getByLabelText(/^공개/).checked).toBe(false)
    type('제목', '파이썬 복습')
    type('내용', '내용입니다')
    click('저장')

    expect(await screen.findByRole('heading', { name: '공부 기록' })).toBeTruthy()
    expect(calls.find((c) => c.key === 'POST /api/studies').body).toEqual({
      title: '파이썬 복습',
      content: '내용입니다',
      is_public: false,
    })
  })

  it('공개를 체크하면 공개로 저장한다', async () => {
    const { calls } = mockApi({
      ...me,
      'POST /api/studies': [201, study({ is_public: true })],
      'GET /api/studies': [200, { items: [] }],
    })
    renderApp('/studies/new')
    await screen.findByRole('heading', { name: '새 공부 기록' })
    type('제목', 't')
    type('내용', 'c')
    fireEvent.click(screen.getByLabelText(/^공개/))
    click('저장')
    await screen.findByRole('heading', { name: '공부 기록' })
    expect(calls.find((c) => c.key === 'POST /api/studies').body.is_public).toBe(true)
  })

  it('저장에 실패하면 입력한 내용을 그대로 두고 항목별 안내를 보여준다', async () => {
    mockApi({
      ...me,
      'POST /api/studies': [422, { errors: { title: '제목은 1자 이상 100자 이하로 입력해 주세요.' } }],
    })
    renderApp('/studies/new')
    await screen.findByRole('heading', { name: '새 공부 기록' })
    type('제목', '')
    type('내용', '작성하던 내용')
    fireEvent.click(screen.getByLabelText(/^공개/))
    click('저장')

    expect(await screen.findByText('제목은 1자 이상 100자 이하로 입력해 주세요.')).toBeTruthy()
    expect(screen.getByLabelText('내용').value).toBe('작성하던 내용')
    expect(screen.getByLabelText(/^공개/).checked).toBe(true)
    expect(screen.getByRole('heading', { name: '새 공부 기록' })).toBeTruthy() // 이동하지 않음
  })

  it('서버에 연결하지 못해도 입력한 내용을 그대로 둔다', async () => {
    mockApi({ ...me, 'POST /api/studies': new Error('network') })
    renderApp('/studies/new')
    await screen.findByRole('heading', { name: '새 공부 기록' })
    type('제목', '제목')
    type('내용', '내용')
    click('저장')
    expect(await screen.findByText(/서버에 연결하지 못했습니다/)).toBeTruthy()
    expect(screen.getByLabelText('제목').value).toBe('제목')
    expect(screen.getByLabelText('내용').value).toBe('내용')
  })
})

describe('공부 기록 읽기', () => {
  it('내 기록은 내용, 작성·수정 시각, 수정·삭제 버튼을 보여준다', async () => {
    mockApi({ ...me, 'GET /api/studies/1': [200, study({ updated_at: '2026-10-28T01:00:00Z' })] })
    renderApp('/studies/1')
    expect(await screen.findByRole('heading', { name: /파이썬 복습/ })).toBeTruthy()
    expect(screen.getByText(/첫 줄/)).toBeTruthy()
    expect(screen.getByText(/수정/, { selector: 'p.hint' })).toBeTruthy()
    expect(screen.getByRole('link', { name: '수정' })).toBeTruthy()
    expect(screen.getByRole('button', { name: '삭제' })).toBeTruthy()
  })

  it('수정한 적이 없으면 수정 시각을 보여주지 않는다', async () => {
    mockApi({ ...me, 'GET /api/studies/1': [200, study()] })
    renderApp('/studies/1')
    const hint = await screen.findByText(/작성/, { selector: 'p.hint' })
    expect(hint.textContent).not.toContain('수정')
  })

  it('다른 사람의 공개 기록은 작성자를 보여주고 수정·삭제 버튼은 보여주지 않는다', async () => {
    mockApi({ ...me, 'GET /api/studies/5': [200, study({ id: 5, is_public: true, is_mine: false, author_nickname: 'bobby' })] })
    renderApp('/studies/5')
    expect(await screen.findByText(/bobby/)).toBeTruthy()
    expect(screen.queryByRole('link', { name: '수정' })).toBeNull()
    expect(screen.queryByRole('button', { name: '삭제' })).toBeNull()
  })

  it('볼 수 없는 기록이면 안내를 보여준다', async () => {
    mockApi({ ...me, 'GET /api/studies/9': [404, { detail: '기록을 찾을 수 없습니다.' }] })
    renderApp('/studies/9')
    expect(await screen.findByText('기록을 찾을 수 없습니다.')).toBeTruthy()
  })
})

describe('공부 기록 삭제', () => {
  it('확인창에서 취소하면 삭제하지 않는다', async () => {
    const { fn } = mockApi({ ...me, 'GET /api/studies/1': [200, study()] })
    renderApp('/studies/1')
    await screen.findByRole('heading', { name: /파이썬 복습/ })
    click('삭제')
    const dialog = screen.getByRole('alertdialog')
    fireEvent.click(within(dialog).getByRole('button', { name: '취소' }))
    expect(screen.queryByRole('alertdialog')).toBeNull()
    expect(fn.mock.calls.some(([, o]) => o?.method === 'DELETE')).toBe(false)
    expect(screen.getByRole('heading', { name: /파이썬 복습/ })).toBeTruthy()
  })

  it('확인창에서 삭제하면 삭제하고 목록으로 이동한다', async () => {
    const { fn } = mockApi({
      ...me,
      'GET /api/studies/1': [200, study()],
      'DELETE /api/studies/1': [204, null],
      'GET /api/studies': [200, { items: [] }],
    })
    renderApp('/studies/1')
    await screen.findByRole('heading', { name: /파이썬 복습/ })
    click('삭제')
    fireEvent.click(within(screen.getByRole('alertdialog')).getByRole('button', { name: '삭제' }))
    expect(await screen.findByRole('heading', { name: '공부 기록' })).toBeTruthy()
    expect(fn.mock.calls.some(([u, o]) => u === '/api/studies/1' && o?.method === 'DELETE')).toBe(true)
  })

  it('삭제에 실패하면 기록을 그대로 두고 안내를 보여준다', async () => {
    mockApi({
      ...me,
      'GET /api/studies/1': [200, study()],
      'DELETE /api/studies/1': new Error('network'),
    })
    renderApp('/studies/1')
    await screen.findByRole('heading', { name: /파이썬 복습/ })
    click('삭제')
    fireEvent.click(within(screen.getByRole('alertdialog')).getByRole('button', { name: '삭제' }))
    expect(await screen.findByText(/삭제하지 못했습니다/)).toBeTruthy()
    expect(screen.getByRole('heading', { name: /파이썬 복습/ })).toBeTruthy()
    expect(screen.queryByRole('alertdialog')).toBeNull()
  })
})

describe('공부 기록 수정', () => {
  it('기존 값이 채워져 있고, 저장하면 수정 요청을 보낸 뒤 목록으로 이동한다', async () => {
    const { calls } = mockApi({
      ...me,
      'GET /api/studies/1': [200, study({ is_public: true })],
      'PUT /api/studies/1': [200, study({ title: '새 제목' })],
      'GET /api/studies': [200, { items: [] }],
    })
    renderApp('/studies/1/edit')
    await screen.findByRole('heading', { name: '공부 기록 수정' })
    expect(screen.getByLabelText('제목').value).toBe('파이썬 복습')
    expect(screen.getByLabelText(/^공개/).checked).toBe(true)
    type('제목', '새 제목')
    click('저장')
    expect(await screen.findByRole('heading', { name: '공부 기록' })).toBeTruthy()
    expect(calls.find((c) => c.key === 'PUT /api/studies/1').body).toEqual({
      title: '새 제목',
      content: '첫 줄\n둘째 줄',
      is_public: true,
    })
  })

  it('수정에 실패하면 고치던 입력값을 그대로 둔다', async () => {
    mockApi({
      ...me,
      'GET /api/studies/1': [200, study()],
      'PUT /api/studies/1': [422, { errors: { content: '내용은 1자 이상 5,000자 이하로 입력해 주세요.' } }],
    })
    renderApp('/studies/1/edit')
    await screen.findByRole('heading', { name: '공부 기록 수정' })
    type('내용', '')
    type('제목', '고치는 중인 제목')
    click('저장')
    expect(await screen.findByText(/내용은 1자 이상 5,000자 이하/)).toBeTruthy()
    expect(screen.getByLabelText('제목').value).toBe('고치는 중인 제목')
  })

  it('작성자가 아니면 수정 양식을 보여주지 않는다', async () => {
    mockApi({ ...me, 'GET /api/studies/5': [200, study({ id: 5, is_mine: false, is_public: true })] })
    renderApp('/studies/5/edit')
    expect(await screen.findByText('작성자만 수정할 수 있습니다.')).toBeTruthy()
    expect(screen.queryByLabelText('제목')).toBeNull()
  })
})
