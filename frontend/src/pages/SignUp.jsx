import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { signup } from '../api/auth.js'
import Card from '../components/Card.jsx'
import FormField from '../components/FormField.jsx'

export default function SignUp() {
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [nickname, setNickname] = useState('')
  const [password, setPassword] = useState('')
  const [errors, setErrors] = useState({})
  const [formError, setFormError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event) {
    event.preventDefault()
    setSubmitting(true)
    setErrors({})
    setFormError('')
    try {
      await signup(email, password, nickname)
      navigate('/login', { state: { message: '회원가입이 완료되었습니다. 로그인해 주세요.' } })
    } catch (err) {
      // 실패하면 이메일과 닉네임은 남기고 비밀번호만 지운다.
      setPassword('')
      const fieldErrors = err.errors ?? {}
      setErrors(fieldErrors)
      setFormError(Object.keys(fieldErrors).length > 0 ? '' : err.message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <>
      <h1>회원가입</h1>
      <Card>
        <form onSubmit={handleSubmit} noValidate>
          <FormField
            id="email"
            label="이메일"
            type="email"
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            error={errors.email}
          />
          <FormField
            id="password"
            label="비밀번호"
            type="password"
            autoComplete="new-password"
            hint="8자 이상 64자 이하"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            error={errors.password}
          />
          <FormField
            id="nickname"
            label="닉네임"
            type="text"
            autoComplete="nickname"
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
          <button type="submit" className="button" disabled={submitting}>
            회원가입
          </button>
        </form>
      </Card>
      <p className="muted">
        이미 계정이 있나요? <Link to="/login">로그인</Link>
      </p>
    </>
  )
}
