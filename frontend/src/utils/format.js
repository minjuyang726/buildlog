// 서버가 보낸 UTC 시각을 사용자의 시간대로 바꿔 보기 좋게 보여준다.
export function formatDateTime(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleString('ko-KR', { dateStyle: 'medium', timeStyle: 'short' })
}
