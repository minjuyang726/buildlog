// 삭제처럼 되돌릴 수 없는 일을 하기 전에 한 번 더 묻는 확인창.
export default function ConfirmDialog({ title, message, confirmLabel = '삭제', onConfirm, onCancel, busy = false }) {
  return (
    <div className="dialog-backdrop">
      <div className="dialog" role="alertdialog" aria-modal="true" aria-labelledby="dialog-title" aria-describedby="dialog-message">
        <h2 id="dialog-title" className="dialog-title">
          {title}
        </h2>
        <p id="dialog-message">{message}</p>
        <div className="actions">
          <button type="button" className="button button-danger" onClick={onConfirm} disabled={busy}>
            {confirmLabel}
          </button>
          <button type="button" className="button button-secondary" onClick={onCancel} disabled={busy}>
            취소
          </button>
        </div>
      </div>
    </div>
  )
}
