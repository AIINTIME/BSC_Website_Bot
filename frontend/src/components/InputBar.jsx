import { useState, useRef } from 'react'
import styles from './InputBar.module.css'

function PaperclipIcon() {
  return (
    <svg width="17" height="17" viewBox="0 0 24 24" fill="none"
      stroke="#9CA3AF" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
      aria-hidden="true">
      <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19
               a4 4 0 0 1 5.66 5.66L9.41 17.41a2 2 0 0 1-2.83-2.83l8.49-8.48"/>
    </svg>
  )
}

function SendIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none"
      stroke="#fff" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"
      aria-hidden="true">
      <line x1="22" y1="2" x2="11" y2="13"/>
      <polygon points="22 2 15 22 11 13 2 9 22 2"/>
    </svg>
  )
}

export default function InputBar({ onSend, disabled }) {
  const [value, setValue] = useState('')
  const ref = useRef(null)

  const resize = () => {
    const el = ref.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = Math.min(el.scrollHeight, 96) + 'px'
  }

  const handleInput = (e) => {
    setValue(e.target.value)
    resize()
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      submit()
    }
  }

  const submit = () => {
    const text = value.trim()
    if (!text || disabled) return
    onSend(text)
    setValue('')
    if (ref.current) ref.current.style.height = 'auto'
  }

  return (
    <>
      <div className={styles.bar}>
        <button className={styles.attachBtn} type="button"
          aria-label="Attach file" title="Attach file">
          <PaperclipIcon />
        </button>

        <div className={styles.inputWrap}>
          <textarea
            ref={ref}
            className={styles.textarea}
            value={value}
            onChange={handleInput}
            onKeyDown={handleKeyDown}
            placeholder="Ask a question…"
            rows={1}
            autoComplete="off"
            spellCheck
            disabled={disabled}
            aria-label="Type your message"
          />
        </div>

        <button
          className={styles.sendBtn}
          onClick={submit}
          disabled={!value.trim() || disabled}
          type="button"
          aria-label="Send message"
        >
          <SendIcon />
        </button>
      </div>

      <p className={styles.footerNote}>
        Powered by BSC AI · Answers may not always be accurate
      </p>
    </>
  )
}
