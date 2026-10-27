import { useState } from 'react'
import { createReport } from '../api/reports.js'
import TextAreaField from './TextAreaField.jsx'

// 공개 기록이나 댓글 옆에 붙는 신고 버튼. 누르면 신고 이유를 적는 창이 열린다.
export default function ReportButton({ targetType, targetId }) {
  const [open, setOpen] = useState(false)
  const [reason, setReason] = useState('')
  const [errors, setErrors] = useState({})
  const [formError, setFormError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [notice, setNotice] = useState('')

  function close() {
    setOpen(false)
    setErrors({})
    setFormError('')
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setSubmitting(true)
    setErrors({})
    setFormError('')
    try {
      const result = await createReport(targetType, targetId, reason)
      setNotice(result.message)
      setReason('')
      setOpen(false)
    } catch (err) {
      // 실패하면 적은 신고 이유를 그대로 두고 이유를 알려준다.
      const fieldErrors = err.errors ?? {}
      setErrors(fieldErrors)
      setFormError(fieldErrors.target ?? (Object.keys(fieldErrors).length > 0 ? '' : err.message))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <span className="report">
      <button
        type="button"
        className="button button-secondary"
        onClick={() => {
          setNotice('')
          setOpen(true)
        }}
      >
        신고
      </button>
      {notice && (
        <span className="success-text" role="status">
          {notice}
        </span>
      )}
      {open && (
        <div className="dialog-backdrop">
          <form className="dialog" role="dialog" aria-modal="true" aria-labelledby="report-title" onSubmit={handleSubmit} noValidate>
            <h2 id="report-title" className="dialog-title">
              신고하기
            </h2>
            <TextAreaField
              id="report-reason"
              label="신고 이유"
              hint="1~500자. 신고만으로 기록이나 댓글이 삭제되지는 않으며, 운영자가 확인합니다."
              rows={4}
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              error={errors.reason}
            />
            {formError && (
              <p className="error-text" role="alert">
                {formError}
              </p>
            )}
            <div className="actions">
              <button type="submit" className="button button-danger" disabled={submitting}>
                신고하기
              </button>
              <button type="button" className="button button-secondary" onClick={close} disabled={submitting}>
                취소
              </button>
            </div>
          </form>
        </div>
      )}
    </span>
  )
}
