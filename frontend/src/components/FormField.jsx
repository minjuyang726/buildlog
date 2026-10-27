// 이름표, 입력칸, 안내 문구, 오류 문구를 한 묶음으로 보여주는 입력 항목.
export default function FormField({ id, label, hint, error, ...inputProps }) {
  const describedBy = [hint && `${id}-hint`, error && `${id}-error`].filter(Boolean).join(' ') || undefined
  return (
    <div className="form-row">
      <label htmlFor={id}>{label}</label>
      <input id={id} name={id} className="field" aria-invalid={error ? 'true' : undefined} aria-describedby={describedBy} {...inputProps} />
      {hint && (
        <p id={`${id}-hint`} className="hint">
          {hint}
        </p>
      )}
      {error && (
        <p id={`${id}-error`} className="error-text" role="alert">
          {error}
        </p>
      )}
    </div>
  )
}
