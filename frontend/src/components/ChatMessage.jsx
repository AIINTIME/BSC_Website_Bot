import ReactMarkdown from 'react-markdown'
import { BotSVG } from '../App'
import SourcePills from './SourcePills'
import styles from './ChatMessage.module.css'

function UserAvatar() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none"
      stroke="#9CA3AF" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
      aria-hidden="true">
      <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
      <circle cx="12" cy="7" r="4" />
    </svg>
  )
}

function AiMessage({ message }) {
  const isStreaming = message.streaming === true
  return (
    <div className={`${styles.row} ${styles.rowAi}`} aria-label="AI Assistant message">
      <div className={styles.labelRow}>
        <div className={`${styles.avatar} ${styles.avatarAi}`} aria-hidden="true">
          <BotSVG size={16} color="var(--bsc-red)" />
        </div>
        <span className={`${styles.label} ${styles.labelAi}`}>AI Assistant</span>
      </div>

      <div className={`${styles.bubble} ${styles.bubbleAi} ${message.error ? styles.bubbleError : ''}`}>
        {message.error
          ? <p className={styles.errorText}>{message.text}</p>
          : (
            <div className="md">
              {isStreaming
                ? <span className={styles.streamingText}>{message.text}<span className={styles.cursor} aria-hidden="true" /></span>
                : <ReactMarkdown>{message.text}</ReactMarkdown>
              }
            </div>
          )
        }
        {!isStreaming && !message.error && message.sources?.length > 0 && (
          <SourcePills sources={message.sources} />
        )}
      </div>
    </div>
  )
}

function UserMessage({ message }) {
  return (
    <div className={`${styles.row} ${styles.rowUser}`} aria-label="Your message">
      <div className={`${styles.labelRow} ${styles.labelRowUser}`}>
        <span className={`${styles.label} ${styles.labelUser}`}>You</span>
        <div className={`${styles.avatar} ${styles.avatarUser}`} aria-hidden="true">
          <UserAvatar />
        </div>
      </div>
      <div className={`${styles.bubble} ${styles.bubbleUser}`}>{message.text}</div>
    </div>
  )
}

export default function ChatMessage({ message }) {
  return message.role === 'ai'
    ? <AiMessage  message={message} />
    : <UserMessage message={message} />
}
