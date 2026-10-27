import { useNavigate } from 'react-router-dom'
import { createError } from '../../api/errors.js'
import Card from '../../components/Card.jsx'
import ErrorForm from '../../components/ErrorForm.jsx'

export default function ErrorNew() {
  const navigate = useNavigate()

  async function handleSubmit(values) {
    await createError(values)
    navigate('/errors') // 저장에 성공하면 목록으로 이동
  }

  return (
    <>
      <h1>새 오류 기록</h1>
      <Card>
        <ErrorForm
          initial={{ title: '', content: '', solution: '', is_resolved: false, is_public: false }}
          submitLabel="저장"
          onSubmit={handleSubmit}
        />
      </Card>
    </>
  )
}
