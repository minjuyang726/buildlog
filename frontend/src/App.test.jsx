import { cleanup, fireEvent, screen, waitFor, within } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { ALICE, NOT_LOGGED_IN, mockApi, renderApp } from './test/helpers.jsx'

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

const type = (label, value) => fireEvent.change(screen.getByLabelText(label), { target: { value } })
const click = (name) => fireEvent.click(screen.getByRole('button', { name }))

describe('로그인하지 않은 사용자', () => {
  it('홈 주소로 들어가면 로그인 화면으로 이동한다', async () => {
    mockApi({ 'GET /api/auth/me': NOT_LOGGED_IN })
    renderApp('/')
    expect(await screen.findByRole('heading', { name: '로그인' })).toBeTruthy()
  })

  it('계정 설정 주소로 들어가도 로그인 화면으로 이동한다', async () => {
    mockApi({ 'GET /api/auth/me': NOT_LOGGED_IN })
    renderApp('/settings')
    expect(await screen.findByRole('heading', { name: '로그인' })).toBeTruthy()
  })

  it('메뉴에 로그인과 회원가입이 보이고 로그아웃은 보이지 않는다', async () => {
    mockApi({ 'GET /api/auth/me': NOT_LOGGED_IN })
    renderApp('/login')
    await screen.findByRole('heading', { name: '로그인' })
    const menu = within(screen.getByRole('navigation', { name: '주 메뉴' }))
    expect(menu.getByRole('link', { name: '회원가입' })).toBeTruthy()
    expect(menu.queryByRole('button', { name: '로그아웃' })).toBeNull()
  })
})

describe('회원가입 화면', () => {
  it('실패하면 이메일과 닉네임은 남기고 비밀번호만 지우며 안내를 보여준다', async () => {
    mockApi({
      'GET /api/auth/me': NOT_LOGGED_IN,
      'POST /api/auth/signup': [409, { errors: { nickname: '이미 사용 중인 닉네임입니다. 다른 닉네임을 입력해 주세요.' } }],
    })
    renderApp('/signup')
    await screen.findByRole('heading', { name: '회원가입' })
    type('이메일', 'alice@example.com')
    type('비밀번호', 'password1')
    type('닉네임', 'alice')
    click('회원가입')

    expect(await screen.findByText(/이미 사용 중인 닉네임/)).toBeTruthy()
    expect(screen.getByLabelText('이메일').value).toBe('alice@example.com')
    expect(screen.getByLabelText('닉네임').value).toBe('alice')
    expect(screen.getByLabelText('비밀번호').value).toBe('')
  })

  it('성공하면 로그인 화면으로 이동하고 완료 안내를 보여준다', async () => {
    const { calls } = mockApi({
      'GET /api/auth/me': NOT_LOGGED_IN,
      'POST /api/auth/signup': [201, ALICE],
    })
    renderApp('/signup')
    await screen.findByRole('heading', { name: '회원가입' })
    type('이메일', 'alice@example.com')
    type('비밀번호', 'password1')
    type('닉네임', 'alice')
    click('회원가입')

    expect(await screen.findByRole('heading', { name: '로그인' })).toBeTruthy()
    expect(screen.getByText('회원가입이 완료되었습니다. 로그인해 주세요.')).toBeTruthy()
    expect(calls.find((c) => c.key === 'POST /api/auth/signup').body).toEqual({
      email: 'alice@example.com',
      password: 'password1',
      nickname: 'alice',
    })
  })

  it('서버에 연결하지 못하면 안내를 보여주고 입력은 유지한다', async () => {
    mockApi({
      'GET /api/auth/me': NOT_LOGGED_IN,
      'POST /api/auth/signup': new Error('network'),
    })
    renderApp('/signup')
    await screen.findByRole('heading', { name: '회원가입' })
    type('이메일', 'alice@example.com')
    type('비밀번호', 'password1')
    type('닉네임', 'alice')
    click('회원가입')

    expect(await screen.findByText(/서버에 연결하지 못했습니다/)).toBeTruthy()
    expect(screen.getByLabelText('이메일').value).toBe('alice@example.com')
    expect(screen.getByLabelText('비밀번호').value).toBe('')
  })
})

describe('로그인 화면', () => {
  it('실패하면 이메일은 남기고 비밀번호만 지우며 안내를 보여준다', async () => {
    mockApi({
      'GET /api/auth/me': NOT_LOGGED_IN,
      'POST /api/auth/login': [401, { detail: '로그인 정보가 맞지 않습니다.' }],
    })
    renderApp('/login')
    await screen.findByRole('heading', { name: '로그인' })
    type('이메일', 'alice@example.com')
    type('비밀번호', 'wrong-password')
    click('로그인')

    expect(await screen.findByText('로그인 정보가 맞지 않습니다.')).toBeTruthy()
    expect(screen.getByLabelText('이메일').value).toBe('alice@example.com')
    expect(screen.getByLabelText('비밀번호').value).toBe('')
  })

  it('성공하면 내 기록 홈으로 이동한다', async () => {
    mockApi({
      'GET /api/auth/me': NOT_LOGGED_IN,
      'POST /api/auth/login': [200, ALICE],
    })
    renderApp('/login')
    await screen.findByRole('heading', { name: '로그인' })
    type('이메일', 'alice@example.com')
    type('비밀번호', 'password1')
    click('로그인')

    expect(await screen.findByRole('heading', { name: 'alice님, 안녕하세요.' })).toBeTruthy()
    expect(screen.getByText('공부 기록')).toBeTruthy()
    expect(screen.getByText('할 일')).toBeTruthy()
    expect(screen.getByText('오류 기록')).toBeTruthy()
  })

  it('이미 로그인한 상태로 들어오면 홈으로 이동한다', async () => {
    mockApi({ 'GET /api/auth/me': [200, ALICE] })
    renderApp('/login')
    expect(await screen.findByRole('heading', { name: 'alice님, 안녕하세요.' })).toBeTruthy()
  })
})

describe('로그아웃', () => {
  it('누르면 로그인 화면으로 이동하고 기록 화면에 들어갈 수 없다', async () => {
    const { fn } = mockApi({
      'GET /api/auth/me': [200, ALICE],
      'POST /api/auth/logout': [204, null],
    })
    renderApp('/')
    await screen.findByRole('heading', { name: 'alice님, 안녕하세요.' })
    click('로그아웃')

    expect(await screen.findByRole('heading', { name: '로그인' })).toBeTruthy()
    expect(screen.queryByRole('button', { name: '로그아웃' })).toBeNull()
    expect(fn).toHaveBeenCalledWith('/api/auth/logout', expect.objectContaining({ method: 'POST' }))
  })

  it('서버 요청이 실패해도 화면에서는 로그인 상태를 끝낸다', async () => {
    mockApi({
      'GET /api/auth/me': [200, ALICE],
      'POST /api/auth/logout': new Error('network'),
    })
    renderApp('/')
    await screen.findByRole('heading', { name: 'alice님, 안녕하세요.' })
    click('로그아웃')
    expect(await screen.findByRole('heading', { name: '로그인' })).toBeTruthy()
  })
})

describe('계정 설정 화면', () => {
  it('닉네임을 바꾸면 안내와 위쪽 메뉴에 새 닉네임이 보인다', async () => {
    const { calls } = mockApi({
      'GET /api/auth/me': [200, ALICE],
      'PATCH /api/auth/me/nickname': [200, { ...ALICE, nickname: '새닉네임' }],
    })
    renderApp('/settings')
    await screen.findByRole('heading', { name: '계정 설정' })
    expect(screen.getByLabelText('새 닉네임').value).toBe('alice')
    type('새 닉네임', '새닉네임')
    click('변경')

    expect(await screen.findByText('닉네임을 변경했습니다.')).toBeTruthy()
    await waitFor(() => expect(screen.getByText('새닉네임', { selector: '.nav-user' })).toBeTruthy())
    expect(calls.find((c) => c.key === 'PATCH /api/auth/me/nickname').body).toEqual({ nickname: '새닉네임' })
  })

  it('실패하면 입력한 닉네임을 그대로 두고 안내를 보여준다', async () => {
    mockApi({
      'GET /api/auth/me': [200, ALICE],
      'PATCH /api/auth/me/nickname': [409, { errors: { nickname: '이미 사용 중인 닉네임입니다. 다른 닉네임을 입력해 주세요.' } }],
    })
    renderApp('/settings')
    await screen.findByRole('heading', { name: '계정 설정' })
    type('새 닉네임', 'bobby')
    click('변경')

    expect(await screen.findByText(/이미 사용 중인 닉네임/)).toBeTruthy()
    expect(screen.getByLabelText('새 닉네임').value).toBe('bobby')
  })
})
