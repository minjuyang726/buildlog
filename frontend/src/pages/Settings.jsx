import { useState } from 'react'
import { changeNickname } from '../api/auth.js'
import Card from '../components/Card.jsx'
import FormField from '../components/FormField.jsx'
import { useAuth } from '../context/auth.js'

export default function Settings() {
  const { user, setUser } = useAuth()
  const [nickname, setNickname] = useState(user.nickname)
  const [errors, setErrors] = useState({})
  const [formError, setFormError] = useState('')
  const [message, setMessage] = useState('')
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event) {
    event.preventDefault()
    setSubmitting(true)
    setErrors({})
    setFormError('')
    setMessage('')
    try {
      const updated = await changeNickname(nickname)
      setUser(updated)
      setNickname(updated.nickname)
      setMessage('닉네임을 변경했습니다.')
    } catch (err) {
      // 실패하면 입력한 새 닉네임을 그대로 둔다.
      const fieldErrors = err.errors ?? {}
      setErrors(fieldErrors)
      setFormError(Object.keys(fieldErrors).length > 0 ? '' : err.message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <>
      <h1>계정 설정</h1>
      <Card title="닉네임 변경">
        <p className="muted">이메일: {user.email}</p>
        <form onSubmit={handleSubmit} noValidate>
          <FormField
            id="nickname"
            label="새 닉네임"
            type="text"
            hint="2~20자, 한글·영문·숫자·밑줄(_)만 사용할 수 있습니다."
            value={nickname}
            onChange={(e) => setNickname(e.target.value)}
            error={errors.nickname}
          />
          {formError && (
            <p className="error-text" role="alert">
              {formError}
            </p>
          )}
          {message && (
            <p className="success-text" role="status">
              {message}
            </p>
          )}
          <button type="submit" className="button" disabled={submitting}>
            변경
          </button>
        </form>
      </Card>
    </>
  )
}
