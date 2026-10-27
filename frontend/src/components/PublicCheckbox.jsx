// 공개 여부를 고르는 체크 상자. 체크하지 않으면 비공개로 저장된다.
export default function PublicCheckbox({ checked, onChange }) {
  return (
    <div className="form-row">
      <label className="check">
        <input type="checkbox" checked={checked} onChange={(e) => onChange(e.target.checked)} />
        공개 (로그인한 다른 사용자도 볼 수 있습니다)
      </label>
      <p className="hint">체크하지 않으면 나만 볼 수 있는 비공개로 저장됩니다.</p>
    </div>
  )
}
