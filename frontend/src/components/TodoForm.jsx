import { useState } from 'react'
import { Link } from 'react-router-dom'
import FormField from './FormField.jsx'
import PublicCheckbox from './PublicCheckbox.jsx'

// 할 일을 새로 쓰거나 고칠 때 함께 쓰는 입력 양식. 저장에 실패하면 입력한 내용을 그대로 둔다.
export default function TodoForm({ initial, submitLabel, onSubmit }) {
  const [title, setTitle] = useState(initial.title)
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
      await onSubmit({ title, is_public: isPublic })
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
      <PublicCheckbox checked={isPublic} onChange={setIsPublic} />
      {formError && (
        <p className="error-text" role="alert">
          {formError}
        </p>
      )}
      <div className="actions">
        <button type="submit" className="button" disabled={submitting}>
          {submitLabel}
        </button>
        <Link to="/todos" className="button button-secondary">
          취소
        </Link>
      </div>
    </form>
  )
}
