import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { listErrors } from '../../api/errors.js'
import { formatDateTime } from '../../utils/format.js'

const FILTERS = [
  { value: 'all', label: '전체' },
  { value: 'unresolved', label: '미해결' },
  { value: 'resolved', label: '해결' },
]

export default function ErrorList() {
  const [filter, setFilter] = useState('all')
  const [input, setInput] = useState('')
  const [keyword, setKeyword] = useState('') // 실제로 검색에 사용한 검색어
  const [items, setItems] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    listErrors(filter, keyword)
      .then((data) => {
        if (!active) return
        setItems(data.items)
        setError('')
      })
      .catch((err) => active && setError(err.message))
    return () => {
      active = false
    }
  }, [filter, keyword])

  function handleSearch(event) {
    event.preventDefault()
    setKeyword(input.trim())
  }

  return (
    <>
      <div className="page-head">
        <h1>오류 기록</h1>
        <Link to="/errors/new" className="button">
          새 오류 기록
        </Link>
      </div>

      <div className="filters" role="group" aria-label="보기 방식">
        {FILTERS.map((f) => (
          <button
            key={f.value}
            type="button"
            className={`chip ${filter === f.value ? 'chip-active' : ''}`}
            aria-pressed={filter === f.value}
            onClick={() => setFilter(f.value)}
          >
            {f.label}
          </button>
        ))}
      </div>

      <form className="search" onSubmit={handleSearch} role="search">
        <label htmlFor="q" className="visually-hidden">
          오류 기록 검색
        </label>
        <input
          id="q"
          type="search"
          className="field"
          placeholder="오류 제목이나 내용으로 검색"
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
        <p className="muted">{keyword ? '검색 결과가 없습니다.' : '해당하는 오류 기록이 없습니다.'}</p>
      )}
      {items?.map((item) => (
        <Link key={item.id} to={`/errors/${item.id}`} className="record-link">
          <article className="card record">
            <h2 className="record-title">
              {item.title}
              <span className={`badge ${item.is_resolved ? 'badge-resolved' : 'badge-open'}`}>
                {item.is_resolved ? '해결' : '미해결'}
              </span>
              <span className={`badge ${item.is_public ? 'badge-public' : ''}`}>{item.is_public ? '공개' : '비공개'}</span>
            </h2>
            <p className="record-preview">{item.preview}</p>
            <p className="hint">
              작성 {formatDateTime(item.created_at)}
              {item.updated_at && ` · 수정 ${formatDateTime(item.updated_at)}`}
              {item.resolved_at && ` · 해결 ${formatDateTime(item.resolved_at)}`}
            </p>
          </article>
        </Link>
      ))}
    </>
  )
}
