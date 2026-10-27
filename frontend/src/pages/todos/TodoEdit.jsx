import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { getTodo, updateTodo } from '../../api/todos.js'
import Card from '../../components/Card.jsx'
import TodoForm from '../../components/TodoForm.jsx'

export default function TodoEdit() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [todo, setTodo] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    getTodo(id)
      .then((data) => active && setTodo(data))
      .catch((err) => active && setError(err.message))
    return () => {
      active = false
    }
  }, [id])

  async function handleSubmit(values) {
    await updateTodo(id, values)
    navigate('/todos') // 수정에 성공하면 목록으로 이동
  }

  if (error) {
    return (
      <>
        <p className="error-text" role="alert">
          {error}
        </p>
        <Link to="/todos">목록으로</Link>
      </>
    )
  }
  if (!todo) return <p className="muted">불러오는 중입니다.</p>
  if (!todo.is_mine) {
    return (
      <>
        <p className="error-text" role="alert">
          작성자만 수정할 수 있습니다.
        </p>
        <Link to="/todos">목록으로</Link>
      </>
    )
  }

  return (
    <>
      <h1>할 일 수정</h1>
      <Card>
        <TodoForm initial={{ title: todo.title, is_public: todo.is_public }} submitLabel="저장" onSubmit={handleSubmit} />
      </Card>
    </>
  )
}
