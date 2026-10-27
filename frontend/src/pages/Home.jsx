import { Link } from 'react-router-dom'
import Card from '../components/Card.jsx'
import { useAuth } from '../context/auth.js'

// 내 기록 홈: 세 가지 기록으로 이동하는 곳. 기록 화면은 이후 Phase에서 하나씩 연결한다.
const SECTIONS = [
  { title: '공부 기록', description: '오늘 공부한 내용을 제목과 내용으로 남깁니다.', to: '/studies' },
  { title: '할 일', description: '앞으로 할 일을 적고 끝내면 체크합니다.', to: '/todos' },
  { title: '오류 기록', description: '오류와 해결 방법을 모아 둡니다.', to: '/errors' },
  { title: '공개 기록', description: '다른 사용자가 공개한 기록을 읽고 검색합니다.', to: '/public' },
]

export default function Home() {
  const { user } = useAuth()
  return (
    <>
      <h1>{user.nickname}님, 안녕하세요.</h1>
      <p className="muted">공부 기록, 할 일, 오류 기록을 한곳에 모아 두는 곳입니다.</p>
      {SECTIONS.map((section) => (
        <Card key={section.title} title={section.title}>
          <p className="muted">{section.description}</p>
          {section.to ? <Link to={section.to}>{section.title} 열기</Link> : <p className="hint">준비 중입니다.</p>}
        </Card>
      ))}
    </>
  )
}
