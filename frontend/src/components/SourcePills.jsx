import styles from './SourcePills.module.css'

function BookIcon() {
  return (
    <svg width="13" height="13" viewBox="0 0 24 24" fill="none"
      stroke="#757575" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
      <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
    </svg>
  )
}

function DocIcon() {
  return (
    <svg width="13" height="13" viewBox="0 0 24 24" fill="none"
      stroke="#E53935" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
      <polyline points="14 2 14 8 20 8"/>
      <line x1="16" y1="13" x2="8" y2="13"/>
      <line x1="16" y1="17" x2="8" y2="17"/>
    </svg>
  )
}

function truncate(str, n) {
  return str && str.length > n ? str.slice(0, n - 1) + '…' : str
}

export default function SourcePills({ sources }) {
  if (!sources || sources.length === 0) return null

  return (
    <div className={styles.sources}>
      <div className={styles.sourcesLabel}>
        <BookIcon />
        <span>Sources</span>
      </div>
      <div className={styles.pills}>
        {sources.map((s, i) => {
          const label = s.question
            ? truncate(s.question, 48)
            : s.category || s.id || 'Source'
          return (
            <div key={i} className={styles.pill}>
              <DocIcon />
              <span>{label}</span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
