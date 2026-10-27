import { cleanup, fireEvent, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { ALICE, mockApi, renderApp } from '../../test/helpers.jsx'

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

const me = { 'GET /api/auth/me': [200, ALICE] }
const type = (label, value) => fireEvent.change(screen.getByLabelText(label), { target: { value } })
const click = (name) => fireEvent.click(screen.getByRole('button', { name }))

const item = (kind, id, title, extra = {}) => ({
  kind,
  id,
  title,
  preview: kind === 'todo' ? null : `${title} 미리보기`,
  author_nickname: 'bobby',
  is_mine: false,
  created_at: '2026-10-27T01:00:00Z',
  ...extra,
})
const list = (...items) => [200, { items }]
const ALL = 'GET /api/public?kind=all'

describe('공개 기록 화면', () => {
  it('세 종류의 기록을 종류 표시, 작성자와 함께 보여준다', async () => {
    mockApi({
      ...me,
      [ALL]: list(
        item('error', 3, '공개 오류', { is_resolved: true }),
        item('todo', 2, '공개 할 일', { is_done: false }),
        item('study', 1, '공개 공부'),
      ),
    })
    renderApp('/public')
    const headings = await screen.findAllByRole('heading', { level: 2 })
    expect(headings.map((h) => h.textContent)).toEqual([
      '오류 기록공개 오류해결',
      '할 일공개 할 일남은 일',
      '공부 기록공개 공부',
    ])
    expect(screen.getAllByText(/bobby/).length).toBe(3)
  })

  it('공부 기록과 오류 기록은 읽는 화면으로 연결하고, 할 일은 링크가 아니다', async () => {
    mockApi({
      ...me,
      [ALL]: list(item('study', 1, '공개 공부'), item('todo', 2, '공개 할 일', { is_done: true }), item('error', 3, '공개 오류', { is_resolved: false })),
    })
    renderApp('/public')
    await screen.findByText('공개 공부')
    expect(screen.getByText('공개 공부').closest('a').getAttribute('href')).toBe('/studies/1')
    expect(screen.getByText('공개 오류').closest('a').getAttribute('href')).toBe('/errors/3')
    expect(screen.getByText('공개 할 일').closest('a')).toBeNull()
  })

  it('내가 공개한 기록에는 (나) 표시가 붙는다', async () => {
    mockApi({ ...me, [ALL]: list(item('study', 1, '내 공개 기록', { author_nickname: 'alice', is_mine: true })) })
    renderApp('/public')
    expect(await screen.findByText(/alice \(나\)/)).toBeTruthy()
  })

  it('종류 버튼을 누르면 해당 종류만 다시 받아 온다', async () => {
    const { calls } = mockApi({
      ...me,
      [ALL]: list(item('study', 1, '공부'), item('todo', 2, '할 일')),
      'GET /api/public?kind=study': list(item('study', 1, '공부')),
      'GET /api/public?kind=todo': list(item('todo', 2, '할 일')),
      'GET /api/public?kind=error': list(),
    })
    renderApp('/public')
    await screen.findByRole('heading', { level: 2, name: /할 일/ })
    click('공부 기록')
    await waitFor(() => expect(screen.queryByText('할 일', { selector: 'h2' })).toBeNull())
    expect(screen.getByRole('button', { name: '공부 기록' }).getAttribute('aria-pressed')).toBe('true')
    click('할 일')
    await waitFor(() => expect(screen.queryByText('공부', { selector: 'h2' })).toBeNull())
    click('오류 기록')
    expect(await screen.findByText('아직 공개된 기록이 없습니다.')).toBeTruthy()
    expect(calls.map((c) => c.key)).toEqual(
      expect.arrayContaining(['GET /api/public?kind=study', 'GET /api/public?kind=todo', 'GET /api/public?kind=error']),
    )
  })

  it('검색하면 선택한 종류와 함께 검색어를 보내고, 빈 검색어는 전체를 보여준다', async () => {
    const q = encodeURIComponent('파이썬')
    const { calls } = mockApi({
      ...me,
      [ALL]: list(item('study', 1, '자바'), item('study', 2, '파이썬')),
      [`GET /api/public?kind=all&q=${q}`]: list(item('study', 2, '파이썬')),
    })
    renderApp('/public')
    await screen.findByText('자바')
    type('공개 기록 검색', ' 파이썬 ')
    click('검색')
    await waitFor(() => expect(screen.queryByText('자바')).toBeNull())
    expect(calls.some((c) => c.key === `GET /api/public?kind=all&q=${q}`)).toBe(true)
    type('공개 기록 검색', '   ')
    click('검색')
    expect(await screen.findByText('자바')).toBeTruthy()
  })

  it('검색 결과가 없으면 안내를 보여준다', async () => {
    mockApi({ ...me, [ALL]: list(item('study', 1, '공부')), [`GET /api/public?kind=all&q=${encodeURIComponent('없음')}`]: list() })
    renderApp('/public')
    await screen.findByText('공부')
    type('공개 기록 검색', '없음')
    click('검색')
    expect(await screen.findByText('검색 결과가 없습니다.')).toBeTruthy()
  })

  it('불러오지 못하면 실패 안내를 보여준다', async () => {
    mockApi({ ...me, [ALL]: new Error('network') })
    renderApp('/public')
    expect(await screen.findByText(/공개 기록을 불러오지 못했습니다/)).toBeTruthy()
  })

  it('로그인하지 않으면 로그인 화면으로 이동한다', async () => {
    mockApi({ 'GET /api/auth/me': [401, { detail: '로그인이 필요합니다.' }] })
    renderApp('/public')
    expect(await screen.findByRole('heading', { name: '로그인' })).toBeTruthy()
  })

  it('수정·삭제·쓰기 버튼이 없다 (읽기 전용)', async () => {
    mockApi({ ...me, [ALL]: list(item('study', 1, '공부'), item('todo', 2, '할 일')) })
    renderApp('/public')
    await screen.findByText('공부')
    for (const name of ['수정', '삭제', '저장']) {
      expect(screen.queryByRole('button', { name })).toBeNull()
    }
  })
})

describe('다른 사람의 공개 기록 읽기 화면', () => {
  it('돌아가기 링크가 공개 기록 화면을 가리킨다', async () => {
    mockApi({
      ...me,
      'GET /api/studies/1': [
        200,
        { id: 1, title: '남의 공부', content: '내용', is_public: true, created_at: '2026-10-27T01:00:00Z', updated_at: null, author_nickname: 'bobby', is_mine: false },
      ],
    })
    renderApp('/studies/1')
    const back = await screen.findByRole('link', { name: /공개 기록으로/ })
    expect(back.getAttribute('href')).toBe('/public')
  })
})
