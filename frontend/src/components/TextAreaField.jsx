// FormField의 여러 줄 입력 버전.
export default function TextAreaField({ id, label, hint, error, rows = 8, ...props }) {
  const describedBy = [hint && `${id}-hint`, error && `${id}-error`].filter(Boolean).join(' ') || undefined
  return (
    <div className="form-row">
      <label htmlFor={id}>{label}</label>
      <textarea
        id={id}
        name={id}
        rows={rows}
        className="field"
        aria-invalid={error ? 'true' : undefined}
        aria-describedby={describedBy}
        {...props}
      />
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
