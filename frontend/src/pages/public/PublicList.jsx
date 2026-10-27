import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { listPublic } from '../../api/public.js'
import { formatDateTime } from '../../utils/format.js'

const KINDS = [
  { value: 'all', label: '전체' },
  { value: 'study', label: '공부 기록' },
  { value: 'todo', label: '할 일' },
  { value: 'error', label: '오류 기록' },
]
const KIND_LABELS = { study: '공부 기록', todo: '할 일', error: '오류 기록' }
const LINKS = { study: (id) => `/studies/${id}`, error: (id) => `/errors/${id}` }

function Meta({ item }) {
  return (
    <p className="hint">
      {item.author_nickname}
      {item.is_mine && ' (나)'} · {formatDateTime(item.created_at)}
    </p>
  )
}

function PublicCard({ item }) {
  const status =
    item.kind === 'todo' ? (item.is_done ? '완료' : '남은 일') : item.kind === 'error' ? (item.is_resolved ? '해결' : '미해결') : null
  const heading = (
    <h2 className="record-title">
      <span className="badge">{KIND_LABELS[item.kind]}</span>
      {item.title}
      {status && <span className="badge">{status}</span>}
    </h2>
  )
  const body = (
    <>
      {heading}
      {item.preview && <p className="record-preview">{item.preview}</p>}
      <Meta item={item} />
    </>
  )
  const to = LINKS[item.kind]?.(item.id)
  // 할 일은 따로 읽는 화면이 없어서 목록에서 바로 보여준다.
  return to ? (
    <Link to={to} className="record-link">
      <article className="card record">{body}</article>
    </Link>
  ) : (
    <article className="card record">{body}</article>
  )
}

export default function PublicList() {
  const [kind, setKind] = useState('all')
  const [input, setInput] = useState('')
  const [keyword, setKeyword] = useState('')
  const [items, setItems] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    listPublic(kind, keyword)
      .then((data) => {
        if (!active) return
        setItems(data.items)
        setError('')
      })
      .catch((err) => active && setError(err.message))
    return () => {
      active = false
    }
  }, [kind, keyword])

  function handleSearch(event) {
    event.preventDefault()
    setKeyword(input.trim())
  }

  return (
    <>
      <div className="page-head">
        <h1>공개 기록</h1>
      </div>
      <p className="muted">작성자가 공개로 설정한 기록입니다. 읽기만 할 수 있습니다.</p>

      <div className="filters" role="group" aria-label="기록 종류">
        {KINDS.map((k) => (
          <button
            key={k.value}
            type="button"
            className={`chip ${kind === k.value ? 'chip-active' : ''}`}
            aria-pressed={kind === k.value}
            onClick={() => setKind(k.value)}
          >
            {k.label}
          </button>
        ))}
      </div>

      <form className="search" onSubmit={handleSearch} role="search">
        <label htmlFor="q" className="visually-hidden">
          공개 기록 검색
        </label>
        <input
          id="q"
          type="search"
          className="field"
          placeholder="공개 기록 검색"
          value={input}
          onChange={(e) => setInput(e.target.value)}
        />
        <button type="submit" className="button">
          검색
        </button>
      </form>

      {error && (
        <p className="error-text" role="alert">
          공개 기록을 불러오지 못했습니다. {error}
        </p>
      )}
      {!error && items === null && <p className="muted">불러오는 중입니다.</p>}
      {!error && items?.length === 0 && (
        <p className="muted">{keyword ? '검색 결과가 없습니다.' : '아직 공개된 기록이 없습니다.'}</p>
      )}
      {items?.map((item) => (
        <PublicCard key={`${item.kind}-${item.id}`} item={item} />
      ))}
    </>
  )
}
