import { useState } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import Card from '../components/Card.jsx'
import FormField from '../components/FormField.jsx'
import { useAuth } from '../context/auth.js'

export default function Login() {
  const { user, login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [formError, setFormError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  if (user) return <Navigate to="/" replace />

  async function handleSubmit(event) {
    event.preventDefault()
    setSubmitting(true)
    setFormError('')
    try {
      await login(email, password)
      navigate('/')
    } catch (err) {
      // 실패하면 이메일은 남기고 비밀번호만 지운다.
      setPassword('')
      setFormError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <>
      <h1>로그인</h1>
      {location.state?.message && (
        <p className="success-text" role="status">
          {location.state.message}
        </p>
      )}
      <Card>
        <form onSubmit={handleSubmit} noValidate>
          <FormField
            id="email"
            label="이메일"
            type="email"
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <FormField
            id="password"
            label="비밀번호"
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          {formError && (
            <p className="error-text" role="alert">
              {formError}
            </p>
          )}
          <button type="submit" className="button" disabled={submitting}>
            로그인
          </button>
        </form>
      </Card>
      <p className="muted">
        계정이 없나요? <Link to="/signup">회원가입</Link>
      </p>
    </>
  )
}
