import { useState } from 'react'
import { Link } from 'react-router-dom'
import FormField from './FormField.jsx'
import PublicCheckbox from './PublicCheckbox.jsx'
import TextAreaField from './TextAreaField.jsx'

// 오류 기록을 새로 쓰거나 고칠 때 함께 쓰는 입력 양식.
// 해결 방법은 해결 전에는 비워 둘 수 있고, 해결로 표시하려면 반드시 입력해야 한다.
export default function ErrorForm({ initial, submitLabel, onSubmit }) {
  const [title, setTitle] = useState(initial.title)
  const [content, setContent] = useState(initial.content)
  const [solution, setSolution] = useState(initial.solution ?? '')
  const [isResolved, setIsResolved] = useState(initial.is_resolved)
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
      await onSubmit({ title, content, solution, is_resolved: isResolved, is_public: isPublic })
    } catch (err) {
      // 저장에 실패하면 입력한 내용은 그대로 두고 이유를 보여준다.
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
        label="오류 제목"
        type="text"
        hint="1~100자"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        error={errors.title}
      />
      <TextAreaField
        id="content"
        label="오류 내용"
        hint="1~5,000자. 화면에 뜬 오류 문구를 그대로 붙여넣으면 나중에 찾기 쉽습니다."
        value={content}
        onChange={(e) => setContent(e.target.value)}
        error={errors.content}
      />
      <TextAreaField
        id="solution"
        label="해결 방법"
        hint="해결하기 전에는 비워 둘 수 있습니다. 입력하면 1~5,000자."
        rows={6}
        value={solution}
        onChange={(e) => setSolution(e.target.value)}
        error={errors.solution}
      />
      <div className="form-row">
        <label className="check">
          <input type="checkbox" checked={isResolved} onChange={(e) => setIsResolved(e.target.checked)} />
          해결했습니다
        </label>
        <p className="hint">해결로 표시하려면 해결 방법을 함께 적어야 합니다.</p>
      </div>
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
        <Link to="/errors" className="button button-secondary">
          취소
        </Link>
      </div>
    </form>
  )
}
