import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { deleteTodo, listTodos, setTodoDone } from '../../api/todos.js'
import ConfirmDialog from '../../components/ConfirmDialog.jsx'
import { formatDateTime } from '../../utils/format.js'

const FILTERS = [
  { value: 'all', label: '전체' },
  { value: 'open', label: '남은 일' },
  { value: 'done', label: '완료한 일' },
]

const EMPTY_MESSAGES = {
  all: '아직 할 일이 없습니다. 첫 할 일을 적어 보세요.',
  open: '남은 일이 없습니다.',
  done: '완료한 일이 없습니다.',
}

export default function TodoList() {
  const [filter, setFilter] = useState('all')
  const [items, setItems] = useState(null)
  const [error, setError] = useState('')
  const [actionError, setActionError] = useState('')
  const [deleting, setDeleting] = useState(null) // 삭제 확인 중인 할 일
  const [busy, setBusy] = useState(false)
  const [reloadKey, setReloadKey] = useState(0) // 값이 바뀌면 목록을 다시 받아 온다.

  useEffect(() => {
    let active = true
    listTodos(filter)
      .then((data) => {
        if (!active) return
        setItems(data.items)
        setError('')
      })
      .catch((err) => active && setError(err.message))
    return () => {
      active = false
    }
  }, [filter, reloadKey])

  const reload = () => setReloadKey((key) => key + 1)

  async function toggle(todo) {
    setActionError('')
    try {
      await setTodoDone(todo.id, !todo.is_done)
      reload() // 순서와 필터 결과가 바뀌므로 목록을 다시 받는다.
    } catch (err) {
      // 실패하면 기존 상태를 그대로 두고 이유를 알려준다.
      setActionError(`완료 상태를 바꾸지 못했습니다. ${err.message}`)
    }
  }

  async function confirmDelete() {
    setBusy(true)
    setActionError('')
    try {
      await deleteTodo(deleting.id)
      setDeleting(null)
      reload()
    } catch (err) {
      setActionError(`삭제하지 못했습니다. ${err.message}`)
      setDeleting(null)
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <div className="page-head">
        <h1>할 일</h1>
        <Link to="/todos/new" className="button">
          새 할 일
        </Link>
      </div>

      <div className="filters" role="group" aria-label="보기 방식">
        {FILTERS.map((f) => (
          <button
            key={f.value}
            type="button"
            className={`chip ${filter === f.value ? 'chip-active' : ''}`}
            aria-pressed={filter === f.value}
            onClick={() => setFilter(f.value)}
          >
            {f.label}
          </button>
        ))}
      </div>

      {error && (
        <p className="error-text" role="alert">
          목록을 불러오지 못했습니다. {error}
        </p>
      )}
      {actionError && (
        <p className="error-text" role="alert">
          {actionError}
        </p>
      )}
      {!error && items === null && <p className="muted">불러오는 중입니다.</p>}
      {!error && items?.length === 0 && <p className="muted">{EMPTY_MESSAGES[filter]}</p>}
      {items?.map((todo) => (
        <article key={todo.id} className={`card todo ${todo.is_done ? 'todo-done' : ''}`}>
          <label className="check todo-title">
            <input type="checkbox" checked={todo.is_done} onChange={() => toggle(todo)} />
            <span>{todo.title}</span>
          </label>
          <span className={`badge ${todo.is_public ? 'badge-public' : ''}`}>{todo.is_public ? '공개' : '비공개'}</span>
          <p className="hint todo-meta">
            작성 {formatDateTime(todo.created_at)}
            {todo.updated_at && ` · 수정 ${formatDateTime(todo.updated_at)}`}
            {todo.completed_at && ` · 완료 ${formatDateTime(todo.completed_at)}`}
          </p>
          <div className="actions todo-actions">
            <Link to={`/todos/${todo.id}/edit`} className="button button-secondary">
              수정
            </Link>
            <button type="button" className="button button-danger" onClick={() => setDeleting(todo)}>
              삭제
            </button>
          </div>
        </article>
      ))}

      {deleting && (
        <ConfirmDialog
          title="할 일을 삭제할까요?"
          message={`"${deleting.title}" 항목을 삭제합니다. 삭제한 할 일은 되돌릴 수 없습니다.`}
          onConfirm={confirmDelete}
          onCancel={() => setDeleting(null)}
          busy={busy}
        />
      )}
    </>
  )
}
