import { useEffect, useState } from 'react'
import { getHealth } from '../api/client.js'
import Card from '../components/Card.jsx'

const MESSAGES = {
  checking: '서버 상태를 확인하는 중입니다.',
  ok: '서버 연결됨',
  failed: '서버 연결 실패. 서버가 켜져 있는지 확인해 주세요.',
}

export default function Home() {
  const [status, setStatus] = useState('checking')

  useEffect(() => {
    let active = true
    getHealth()
      .then((data) => active && setStatus(data.status === 'ok' ? 'ok' : 'failed'))
      .catch(() => active && setStatus('failed'))
    return () => {
      active = false
    }
  }, [])

  return (
    <>
      <h1>BuildLog</h1>
      <p className="muted">공부 기록, 할 일, 오류 기록을 한곳에 모아 두는 곳입니다.</p>
      <Card title="서버 상태">
        <p role="status" className={`status status-${status}`}>
          {MESSAGES[status]}
        </p>
      </Card>
    </>
  )
}
