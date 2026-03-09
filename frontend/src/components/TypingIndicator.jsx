import { BotSVG } from '../App'
import styles from './TypingIndicator.module.css'

export default function TypingIndicator() {
  return (
    <div className={styles.row} aria-label="AI is typing" role="status">
      <div className={styles.labelRow}>
        <div className={styles.avatar} aria-hidden="true">
          <BotSVG size={16} color="var(--bsc-red)" />
        </div>
        <span className={styles.label}>AI Assistant</span>
      </div>
      <div className={styles.bubble}>
        <span className={styles.dot} />
        <span className={styles.dot} />
        <span className={styles.dot} />
      </div>
    </div>
  )
}
