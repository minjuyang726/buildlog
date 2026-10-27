import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { getError, updateError } from '../../api/errors.js'
import Card from '../../components/Card.jsx'
import ErrorForm from '../../components/ErrorForm.jsx'

export default function ErrorEdit() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [record, setRecord] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    getError(id)
      .then((data) => active && setRecord(data))
      .catch((err) => active && setError(err.message))
    return () => {
      active = false
    }
  }, [id])

  async function handleSubmit(values) {
    await updateError(id, values)
    navigate('/errors') // 수정에 성공하면 목록으로 이동
  }

  if (error) {
    return (
      <>
        <p className="error-text" role="alert">
          {error}
        </p>
        <Link to="/errors">목록으로</Link>
      </>
    )
  }
  if (!record) return <p className="muted">불러오는 중입니다.</p>
  if (!record.is_mine) {
    return (
      <>
        <p className="error-text" role="alert">
          작성자만 수정할 수 있습니다.
        </p>
        <Link to={`/errors/${id}`}>돌아가기</Link>
      </>
    )
  }

  return (
    <>
      <h1>오류 기록 수정</h1>
      <Card>
        <ErrorForm
          initial={{
            title: record.title,
            content: record.content,
            solution: record.solution ?? '',
            is_resolved: record.is_resolved,
            is_public: record.is_public,
          }}
          submitLabel="저장"
          onSubmit={handleSubmit}
        />
      </Card>
    </>
  )
}
