export default function Feedback({ loading, error, retry, title, children }) {
  if (loading) return <div className="feedback" role="status"><span className="spinner" />Loading…</div>
  if (error) return <div className="feedback"><h2>Something needs another try</h2><p role="alert">{error.message}</p>{retry && <button className="button secondary" onClick={retry}>Try again</button>}</div>
  return <div className="feedback"><span className="empty-mark" aria-hidden="true">↗</span><h2>{title}</h2>{children}</div>
}
