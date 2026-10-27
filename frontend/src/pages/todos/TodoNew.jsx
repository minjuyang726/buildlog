import { useNavigate } from 'react-router-dom'
import { createTodo } from '../../api/todos.js'
import Card from '../../components/Card.jsx'
import TodoForm from '../../components/TodoForm.jsx'

export default function TodoNew() {
  const navigate = useNavigate()

  async function handleSubmit(values) {
    await createTodo(values)
    navigate('/todos') // 저장에 성공하면 목록으로 이동
  }

  return (
    <>
      <h1>새 할 일</h1>
      <Card>
        <TodoForm initial={{ title: '', is_public: false }} submitLabel="저장" onSubmit={handleSubmit} />
      </Card>
    </>
  )
}
