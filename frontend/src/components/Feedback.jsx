export default function Feedback({ title, children, error = false, onRetry }) {
  return <div className={`feedback ${error ? 'feedback-error' : ''}`} role={error ? 'alert' : 'status'}>
    <strong>{title}</strong>{children && <p>{children}</p>}
    {onRetry && <button type="button" className="text-button" onClick={onRetry}>Try again →</button>}
  </div>
}
