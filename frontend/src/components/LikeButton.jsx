import { useEffect, useState } from 'react'
import { addLike, getLike, removeLike } from '../api/likes.js'

// 좋아요 버튼과 전체 개수. 누르면 등록, 다시 누르면 취소된다.
export default function LikeButton({ parent, parentId }) {
  const [state, setState] = useState(null) // { liked, like_count }
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    let active = true
    getLike(parent, parentId)
      .then((data) => active && setState(data))
      .catch((err) => active && setError(err.message))
    return () => {
      active = false
    }
  }, [parent, parentId])

  async function toggle() {
    setBusy(true)
    setError('')
    try {
      // 실패하면 아래에서 상태를 바꾸지 않으므로 이전 상태와 개수가 그대로 남는다.
      setState(await (state.liked ? removeLike(parent, parentId) : addLike(parent, parentId)))
    } catch (err) {
      setError(`좋아요를 처리하지 못했습니다. ${err.message}`)
    } finally {
      setBusy(false)
    }
  }

  if (!state) {
    return error ? (
      <p className="error-text" role="alert">
        좋아요를 불러오지 못했습니다. {error}
      </p>
    ) : null
  }

  return (
    <div className="like">
      <button type="button" className={`chip ${state.liked ? 'chip-active' : ''}`} aria-pressed={state.liked} onClick={toggle} disabled={busy}>
        {state.liked ? '좋아요 취소' : '좋아요'}
      </button>
      <span className="like-count" aria-label="좋아요 수">
        {state.like_count}
      </span>
      {error && (
        <p className="error-text" role="alert">
          {error}
        </p>
      )}
    </div>
  )
}
