import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { getStudy, updateStudy } from '../../api/studies.js'
import Card from '../../components/Card.jsx'
import StudyForm from '../../components/StudyForm.jsx'

export default function StudyEdit() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [study, setStudy] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    getStudy(id)
      .then((data) => active && setStudy(data))
      .catch((err) => active && setError(err.message))
    return () => {
      active = false
    }
  }, [id])

  async function handleSubmit(values) {
    await updateStudy(id, values)
    navigate('/studies') // 수정에 성공하면 목록으로 이동
  }

  if (error) {
    return (
      <>
        <p className="error-text" role="alert">
          {error}
        </p>
        <Link to="/studies">목록으로</Link>
      </>
    )
  }
  if (!study) return <p className="muted">불러오는 중입니다.</p>
  if (!study.is_mine) {
    return (
      <>
        <p className="error-text" role="alert">
          작성자만 수정할 수 있습니다.
        </p>
        <Link to={`/studies/${id}`}>돌아가기</Link>
      </>
    )
  }

  return (
    <>
      <h1>공부 기록 수정</h1>
      <Card>
        <StudyForm
          initial={{ title: study.title, content: study.content, is_public: study.is_public }}
          submitLabel="저장"
          onSubmit={handleSubmit}
        />
      </Card>
    </>
  )
}
