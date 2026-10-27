// 서버(FastAPI)에 요청을 보내는 공통 함수.
// 화면은 서버에만 요청하고, 데이터베이스에는 직접 접근하지 않는다.
export async function apiGet(path) {
  const response = await fetch(`/api${path}`, { credentials: 'include' })
  if (!response.ok) {
    throw new Error(`요청에 실패했습니다. (${response.status})`)
  }
  return response.json()
}

export function getHealth() {
  return apiGet('/health')
}
