import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { deleteStudy, getStudy } from '../../api/studies.js'
import Card from '../../components/Card.jsx'
import ConfirmDialog from '../../components/ConfirmDialog.jsx'
import { formatDateTime } from '../../utils/format.js'

export default function StudyDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [study, setStudy] = useState(null)
  const [error, setError] = useState('')
  const [confirming, setConfirming] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [deleteError, setDeleteError] = useState('')

  useEffect(() => {
    let active = true
    getStudy(id)
      .then((data) => active && setStudy(data))
      .catch((err) => active && setError(err.message))
    return () => {
      active = false
    }
  }, [id])

  async function handleDelete() {
    setDeleting(true)
    setDeleteError('')
    try {
      await deleteStudy(id)
      navigate('/studies')
    } catch (err) {
      // 삭제에 실패하면 기록은 그대로 두고 이유를 알려준다.
      setDeleteError(err.message)
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
        <Link to="/studies">목록으로</Link>
      </>
    )
  }
  if (!study) return <p className="muted">불러오는 중입니다.</p>

  return (
    <>
      <p>
        <Link to={study.is_mine ? '/studies' : '/public'}>← {study.is_mine ? '목록으로' : '공개 기록으로'}</Link>
      </p>
      <Card>
        <h1 className="record-title">
          {study.title}
          <span className={`badge ${study.is_public ? 'badge-public' : ''}`}>{study.is_public ? '공개' : '비공개'}</span>
        </h1>
        <p className="hint">
          {study.author_nickname} · 작성 {formatDateTime(study.created_at)}
          {study.updated_at && ` · 수정 ${formatDateTime(study.updated_at)}`}
        </p>
        <div className="record-body">{study.content}</div>
        {deleteError && (
          <p className="error-text" role="alert">
            삭제하지 못했습니다. {deleteError}
          </p>
        )}
        {study.is_mine && (
          <div className="actions">
            <Link to={`/studies/${study.id}/edit`} className="button">
              수정
            </Link>
            <button type="button" className="button button-danger" onClick={() => setConfirming(true)}>
              삭제
            </button>
          </div>
        )}
      </Card>
      {confirming && (
        <ConfirmDialog
          title="공부 기록을 삭제할까요?"
          message="삭제한 기록은 되돌릴 수 없습니다."
          onConfirm={handleDelete}
          onCancel={() => setConfirming(false)}
          busy={deleting}
        />
      )}
    </>
  )
}
