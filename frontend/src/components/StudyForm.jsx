import { useState } from 'react'
import { Link } from 'react-router-dom'
import FormField from './FormField.jsx'
import TextAreaField from './TextAreaField.jsx'

// 공부 기록을 새로 쓰거나 고칠 때 함께 쓰는 입력 양식.
// 저장에 실패하면 입력한 내용을 그대로 두고 이유를 보여준다.
export default function StudyForm({ initial, submitLabel, onSubmit }) {
  const [title, setTitle] = useState(initial.title)
  const [content, setContent] = useState(initial.content)
  const [isPublic, setIsPublic] = useState(initial.is_public)
  const [errors, setErrors] = useState({})
  const [formError, setFormError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event) {
    event.preventDefault()
    setSubmitting(true)
    setErrors({})
    setFormError('')
    try {
      await onSubmit({ title, content, is_public: isPublic })
    } catch (err) {
      const fieldErrors = err.errors ?? {}
      setErrors(fieldErrors)
      setFormError(Object.keys(fieldErrors).length > 0 ? '' : err.message)
      setSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} noValidate>
      <FormField
        id="title"
        label="제목"
        type="text"
        hint="1~100자"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        error={errors.title}
      />
      <TextAreaField
        id="content"
        label="내용"
        hint="1~5,000자"
        value={content}
        onChange={(e) => setContent(e.target.value)}
        error={errors.content}
      />
      <div className="form-row">
        <label className="check">
          <input type="checkbox" checked={isPublic} onChange={(e) => setIsPublic(e.target.checked)} />
          공개 (로그인한 다른 사용자도 볼 수 있습니다)
        </label>
        <p className="hint">체크하지 않으면 나만 볼 수 있는 비공개 기록으로 저장됩니다.</p>
      </div>
      {formError && (
        <p className="error-text" role="alert">
          {formError}
        </p>
      )}
      <div className="actions">
        <button type="submit" className="button" disabled={submitting}>
          {submitLabel}
        </button>
        <Link to="/studies" className="button button-secondary">
          취소
        </Link>
      </div>
    </form>
  )
}
