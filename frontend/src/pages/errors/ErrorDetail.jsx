import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { deleteError, getError } from '../../api/errors.js'
import Card from '../../components/Card.jsx'
import Comments from '../../components/Comments.jsx'
import ConfirmDialog from '../../components/ConfirmDialog.jsx'
import LikeButton from '../../components/LikeButton.jsx'
import { formatDateTime } from '../../utils/format.js'

export default function ErrorDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [record, setRecord] = useState(null)
  const [error, setError] = useState('')
  const [confirming, setConfirming] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [deleteFailure, setDeleteFailure] = useState('')

  useEffect(() => {
    let active = true
    getError(id)
      .then((data) => active && setRecord(data))
      .catch((err) => active && setError(err.message))
    return () => {
      active = false
    }
  }, [id])

  async function handleDelete() {
    setDeleting(true)
    setDeleteFailure('')
    try {
      await deleteError(id)
      navigate('/errors')
    } catch (err) {
      setDeleteFailure(err.message)
      setConfirming(false)
      setDeleting(false)
    }
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

  return (
    <>
      <p>
        <Link to={record.is_mine ? '/errors' : '/public'}>← {record.is_mine ? '목록으로' : '공개 기록으로'}</Link>
      </p>
      <Card>
        <h1 className="record-title">
          {record.title}
          <span className={`badge ${record.is_resolved ? 'badge-resolved' : 'badge-open'}`}>
            {record.is_resolved ? '해결' : '미해결'}
          </span>
          <span className={`badge ${record.is_public ? 'badge-public' : ''}`}>{record.is_public ? '공개' : '비공개'}</span>
        </h1>
        <p className="hint">
          {record.author_nickname} · 작성 {formatDateTime(record.created_at)}
          {record.updated_at && ` · 수정 ${formatDateTime(record.updated_at)}`}
          {record.resolved_at && ` · 해결 ${formatDateTime(record.resolved_at)}`}
        </p>

        <h2 className="section-title">오류 내용</h2>
        <div className="record-body">{record.content}</div>

        <h2 className="section-title">해결 방법</h2>
        {record.solution ? (
          <div className="record-body">{record.solution}</div>
        ) : (
          <p className="muted">아직 해결 방법이 없습니다.</p>
        )}

        {record.is_public && <LikeButton parent="errors" parentId={record.id} />}
        {deleteFailure && (
          <p className="error-text" role="alert">
            삭제하지 못했습니다. {deleteFailure}
          </p>
        )}
        {record.is_mine && (
          <div className="actions">
            <Link to={`/errors/${record.id}/edit`} className="button">
              {record.is_resolved ? '수정' : '해결 방법 쓰기 · 수정'}
            </Link>
            <button type="button" className="button button-danger" onClick={() => setConfirming(true)}>
              삭제
            </button>
          </div>
        )}
      </Card>
      {/* 댓글은 공개된 기록에서만 보인다. 비공개가 되면 숨겨지고, 다시 공개하면 돌아온다. */}
      {record.is_public && <Comments parent="errors" parentId={record.id} />}
      {confirming && (
        <ConfirmDialog
          title="오류 기록을 삭제할까요?"
          message="삭제한 기록은 되돌릴 수 없습니다."
          onConfirm={handleDelete}
          onCancel={() => setConfirming(false)}
          busy={deleting}
        />
      )}
    </>
  )
}
