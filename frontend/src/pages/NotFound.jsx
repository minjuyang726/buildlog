import { Link } from 'react-router-dom'

export default function NotFound() {
  return (
    <>
      <h1>페이지를 찾을 수 없습니다</h1>
      <p className="muted">주소가 잘못되었거나 없어진 페이지입니다.</p>
      <Link to="/">홈으로 가기</Link>
    </>
  )
}
