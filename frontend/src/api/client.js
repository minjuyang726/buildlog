// 서버(FastAPI)에 요청을 보내는 공통 함수.
// 화면은 서버에만 요청하고, 데이터베이스에는 직접 접근하지 않는다.

export const NETWORK_ERROR_MESSAGE = '서버에 연결하지 못했습니다. 잠시 후 다시 시도해 주세요.'
const DEFAULT_ERROR_MESSAGE = '요청을 처리하지 못했습니다. 잠시 후 다시 시도해 주세요.'

export class ApiError extends Error {
  constructor(status, message, errors = {}) {
    super(message)
    this.status = status // 0이면 서버에 연결하지 못한 경우
    this.errors = errors // 항목별 안내 문구 { email: '...', nickname: '...' }
  }
}

async function request(method, path, body) {
  let response
  try {
    response = await fetch(`/api${path}`, {
      method,
      credentials: 'include',
      headers: body === undefined ? undefined : { 'Content-Type': 'application/json' },
      body: body === undefined ? undefined : JSON.stringify(body),
    })
  } catch {
    throw new ApiError(0, NETWORK_ERROR_MESSAGE)
  }

  if (response.status === 204) return null

  let data = null
  try {
    data = await response.json()
  } catch {
    data = null
  }

  if (!response.ok) {
    const errors = data?.errors ?? {}
    const message =
      typeof data?.detail === 'string'
        ? data.detail
        : Object.keys(errors).length > 0
          ? '입력한 내용을 다시 확인해 주세요.'
          : DEFAULT_ERROR_MESSAGE
    throw new ApiError(response.status, message, errors)
  }
  return data
}

export const apiGet = (path) => request('GET', path)
export const apiPost = (path, body) => request('POST', path, body ?? {})
export const apiPatch = (path, body) => request('PATCH', path, body)
export const apiDelete = (path) => request('DELETE', path)

export function getHealth() {
  return apiGet('/health')
}
