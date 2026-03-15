import ReactMarkdown from 'react-markdown'
import { BotSVG } from '../App'
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

function PencilIcon() {
  return (
    <svg width="13" height="13" viewBox="0 0 24 24" fill="none"
      stroke="currentColor" strokeWidth="2.2"
      strokeLinecap="round" strokeLinejoin="round"
      aria-hidden="true">
      <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
      <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
    </svg>
  )
}

function AiMessage({ message, onSend }) {
  const isStreaming = message.streaming === true
  const quickReplies = (!isStreaming && message.quickReplies?.length > 0) ? message.quickReplies : []

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
      </div>

      {quickReplies.length > 0 && (
        <div className={styles.quickReplies} role="group" aria-label="Quick reply options">
          {quickReplies.map(option => (
            <button
              key={option}
              className={styles.quickReplyBtn}
              onClick={() => onSend(option)}
            >
              {option}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

function UserMessage({ message, onEdit, isLocked }) {
  return (
    <div className={`${styles.row} ${styles.rowUser}`} aria-label="Your message">
      <div className={`${styles.labelRow} ${styles.labelRowUser}`}>
        <span className={`${styles.label} ${styles.labelUser}`}>You</span>
        <div className={`${styles.avatar} ${styles.avatarUser}`} aria-hidden="true">
          <UserAvatar />
        </div>
      </div>
      <div className={styles.bubbleRow}>
        <button
          className={styles.editBtn}
          onClick={onEdit}
          disabled={isLocked}
          aria-label="Edit this message"
          title="Edit message"
          type="button"
        >
          <PencilIcon />
        </button>
        <div className={`${styles.bubble} ${styles.bubbleUser}`}>{message.text}</div>
      </div>
    </div>
  )
}

export default function ChatMessage({ message, onSend, onEdit, isLocked }) {
  return message.role === 'ai'
    ? <AiMessage  message={message} onSend={onSend} />
    : <UserMessage message={message} onEdit={onEdit} isLocked={isLocked} />
}
