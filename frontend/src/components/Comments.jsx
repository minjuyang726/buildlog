import { useEffect, useState } from 'react'
import { createComment, deleteComment, listComments, updateComment } from '../api/comments.js'
import { formatDateTime } from '../utils/format.js'
import ConfirmDialog from './ConfirmDialog.jsx'
import TextAreaField from './TextAreaField.jsx'

// 공개된 공부 기록·오류 기록 아래에 보이는 댓글 영역. 오래된 댓글부터 보여준다.
export default function Comments({ parent, parentId }) {
  const [items, setItems] = useState(null)
  const [loadError, setLoadError] = useState('')
  const [reloadKey, setReloadKey] = useState(0)
  const [text, setText] = useState('')
  const [errors, setErrors] = useState({})
  const [formError, setFormError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [editing, setEditing] = useState(null) // { id, text, error }
  const [deleting, setDeleting] = useState(null)
  const [busy, setBusy] = useState(false)
  const [actionError, setActionError] = useState('')

  useEffect(() => {
    let active = true
    listComments(parent, parentId)
      .then((data) => {
        if (!active) return
        setItems(data.items)
        setLoadError('')
      })
      .catch((err) => active && setLoadError(err.message))
    return () => {
      active = false
    }
  }, [parent, parentId, reloadKey])

  const reload = () => setReloadKey((key) => key + 1)

  async function handleCreate(event) {
    event.preventDefault()
    setSubmitting(true)
    setErrors({})
    setFormError('')
    try {
      await createComment(parent, parentId, text)
      setText('')
      reload()
    } catch (err) {
      // 실패하면 쓰던 댓글을 그대로 둔다.
      const fieldErrors = err.errors ?? {}
      setErrors(fieldErrors)
      setFormError(Object.keys(fieldErrors).length > 0 ? '' : err.message)
    } finally {
      setSubmitting(false)
    }
  }

  async function handleUpdate(event) {
    event.preventDefault()
    try {
      await updateComment(editing.id, editing.text)
      setEditing(null)
      reload()
    } catch (err) {
      const message = err.errors?.content ?? err.message
      setEditing((current) => ({ ...current, error: message }))
    }
  }

  async function handleDelete() {
    setBusy(true)
    setActionError('')
    try {
      await deleteComment(deleting.id)
      setDeleting(null)
      reload()
    } catch (err) {
      setActionError(`댓글을 삭제하지 못했습니다. ${err.message}`)
      setDeleting(null)
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="comments" aria-labelledby="comments-title">
      <h2 id="comments-title" className="section-title">
        댓글{items ? ` (${items.length})` : ''}
      </h2>

      {loadError && (
        <p className="error-text" role="alert">
          댓글을 불러오지 못했습니다. {loadError}
        </p>
      )}
      {actionError && (
        <p className="error-text" role="alert">
          {actionError}
        </p>
      )}
      {!loadError && items?.length === 0 && <p className="muted">아직 댓글이 없습니다.</p>}

      {items?.map((comment) => (
        <article key={comment.id} className="comment">
          <p className="hint">
            {comment.author_nickname}
            {comment.is_mine && ' (나)'} · {formatDateTime(comment.created_at)}
            {comment.updated_at && ` · 수정 ${formatDateTime(comment.updated_at)}`}
          </p>
          {editing?.id === comment.id ? (
            <form onSubmit={handleUpdate} noValidate>
              <TextAreaField
                id={`edit-${comment.id}`}
                label="댓글 수정"
                rows={3}
                value={editing.text}
                onChange={(e) => setEditing({ ...editing, text: e.target.value })}
                error={editing.error}
              />
              <div className="actions">
                <button type="submit" className="button">
                  수정 저장
                </button>
                <button type="button" className="button button-secondary" onClick={() => setEditing(null)}>
                  수정 취소
                </button>
              </div>
            </form>
          ) : (
            <>
              <div className="record-body">{comment.content}</div>
              <div className="actions">
                {comment.is_mine && (
                  <button
                    type="button"
                    className="button button-secondary"
                    onClick={() => setEditing({ id: comment.id, text: comment.content, error: '' })}
                  >
                    수정
                  </button>
                )}
                {comment.can_delete && (
                  <button type="button" className="button button-danger" onClick={() => setDeleting(comment)}>
                    삭제
                  </button>
                )}
              </div>
            </>
          )}
        </article>
      ))}

      <form onSubmit={handleCreate} noValidate>
        <TextAreaField
          id="new-comment"
          label="댓글 쓰기"
          hint="1~500자"
          rows={3}
          value={text}
          onChange={(e) => setText(e.target.value)}
          error={errors.content}
        />
        {formError && (
          <p className="error-text" role="alert">
            {formError}
          </p>
        )}
        <button type="submit" className="button" disabled={submitting}>
          댓글 등록
        </button>
      </form>

      {deleting && (
        <ConfirmDialog
          title="댓글을 삭제할까요?"
          message="삭제한 댓글은 되돌릴 수 없습니다."
          onConfirm={handleDelete}
          onCancel={() => setDeleting(null)}
          busy={busy}
        />
      )}
    </section>
  )
}
