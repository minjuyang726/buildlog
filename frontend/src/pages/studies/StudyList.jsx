import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { listStudies } from '../../api/studies.js'
import { formatDateTime } from '../../utils/format.js'

export default function StudyList() {
  const [input, setInput] = useState('')
  const [keyword, setKeyword] = useState('') // 실제로 검색에 사용한 검색어
  const [items, setItems] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    listStudies(keyword)
      .then((data) => {
        if (!active) return
        setItems(data.items)
        setError('')
      })
      .catch((err) => active && setError(err.message))
    return () => {
      active = false
    }
  }, [keyword])

  function handleSearch(event) {
    event.preventDefault()
    setKeyword(input.trim())
  }

  return (
    <>
      <div className="page-head">
        <h1>공부 기록</h1>
        <Link to="/studies/new" className="button">
          새 기록 쓰기
        </Link>
      </div>

      <form className="search" onSubmit={handleSearch} role="search">
        <label htmlFor="q" className="visually-hidden">
          공부 기록 검색
        </label>
        <input
          id="q"
          type="search"
          className="field"
          placeholder="제목이나 내용으로 검색"
          value={input}
          onChange={(e) => setInput(e.target.value)}
        />
        <button type="submit" className="button">
          검색
        </button>
      </form>

      {error && (
        <p className="error-text" role="alert">
          목록을 불러오지 못했습니다. {error}
        </p>
      )}
      {!error && items === null && <p className="muted">불러오는 중입니다.</p>}
      {!error && items?.length === 0 && (
        <p className="muted">{keyword ? '검색 결과가 없습니다.' : '아직 공부 기록이 없습니다. 첫 기록을 남겨 보세요.'}</p>
      )}
      {items?.map((item) => (
        <Link key={item.id} to={`/studies/${item.id}`} className="record-link">
          <article className="card record">
            <h2 className="record-title">
              {item.title}
              <span className={`badge ${item.is_public ? 'badge-public' : ''}`}>{item.is_public ? '공개' : '비공개'}</span>
            </h2>
            <p className="record-preview">{item.preview}</p>
            <p className="hint">
              {formatDateTime(item.created_at)}
              {item.updated_at && ` · 수정 ${formatDateTime(item.updated_at)}`}
            </p>
          </article>
        </Link>
      ))}
    </>
  )
}
