import { useNavigate } from 'react-router-dom'
import { createStudy } from '../../api/studies.js'
import Card from '../../components/Card.jsx'
import StudyForm from '../../components/StudyForm.jsx'

export default function StudyNew() {
  const navigate = useNavigate()

  async function handleSubmit(values) {
    await createStudy(values)
    navigate('/studies') // 저장에 성공하면 목록으로 이동
  }

  return (
    <>
      <h1>새 공부 기록</h1>
      <Card>
        <StudyForm initial={{ title: '', content: '', is_public: false }} submitLabel="저장" onSubmit={handleSubmit} />
      </Card>
    </>
  )
}
