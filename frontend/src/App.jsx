import { useState, useEffect, useRef, useCallback } from 'react'
import { v4 as uuidv4 } from 'uuid'
import ChatMessage from './components/ChatMessage'
import TypingIndicator from './components/TypingIndicator'
import InputBar from './components/InputBar'
import styles from './App.module.css'

// ── Session ID lives in a ref so it can be regenerated on close ──────────────

// ── SSE reader ────────────────────────────────────────────────────────────────
async function* readSSE(response) {
  const reader  = response.body.getReader()
  const decoder = new TextDecoder()
  let   buffer  = ''
  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop()
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        try { yield JSON.parse(line.slice(6)) } catch { /* skip */ }
      }
    }
  }
}

// ── SVG icons (all inline — no external deps) ─────────────────────────────────
export function BotSVG({ size = 22, color = 'currentColor' }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
         aria-hidden="true" focusable="false"
         stroke={color} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="11" width="18" height="11" rx="2.5" />
      <path d="M12 11V7" />
      <circle cx="12" cy="5" r="2" />
      <circle cx="8.5" cy="16" r="1.2" fill={color} stroke="none" />
      <circle cx="15.5" cy="16" r="1.2" fill={color} stroke="none" />
      <path d="M9 19.5h6" strokeWidth="1.6" />
    </svg>
  )
}

function ChatIcon() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none"
         stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
    </svg>
  )
}

function XIcon({ color = '#fff', size = 18 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
         stroke={color} strokeWidth="2.5" strokeLinecap="round">
      <line x1="18" y1="6"  x2="6"  y2="18" />
      <line x1="6"  y1="6"  x2="18" y2="18" />
    </svg>
  )
}

function MinusIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none"
         stroke="#fff" strokeWidth="2.5" strokeLinecap="round">
      <line x1="5" y1="12" x2="19" y2="12" />
    </svg>
  )
}

// ── Welcome / empty state ─────────────────────────────────────────────────────
const SUGGESTION_CHIPS = [
  'Membership plans', 'Swimming pool', 'Cricket academy', 'Opening hours',
]

function WelcomeScreen({ onChip, exiting }) {
  return (
    <div className={`${styles.welcome} ${exiting ? styles.welcomeExit : ''}`}>
      <div className={styles.welcomeBadge}>
        <BotSVG size={30} color="var(--bsc-red)" />
      </div>
      <div className={styles.welcomeTitle}>BSC AI Assistant</div>
      <p className={styles.welcomeText}>
        Hi! I&apos;m here to answer questions about Bashundhara Sports City —
        memberships, facilities, academies, bookings & more.
      </p>
      <div className={styles.welcomeChips}>
        {SUGGESTION_CHIPS.map(c => (
          <button key={c} className={styles.welcomeChip}
            onClick={() => onChip(c)} tabIndex={0}>{c}</button>
        ))}
      </div>
    </div>
  )
}

// ── App ───────────────────────────────────────────────────────────────────────
export default function App() {
  const [isOpen,        setIsOpen]        = useState(false)
  const [messages,      setMessages]      = useState([])
  const [isTyping,      setIsTyping]      = useState(false)
  const [isLocked,      setIsLocked]      = useState(false)
  const [unread,        setUnread]        = useState(0)
  const [welcomeGone,   setWelcomeGone]   = useState(false)
  const [welcomeExit,   setWelcomeExit]   = useState(false)
  const bottomRef    = useRef(null)
  const hasGreeted   = useRef(false)
  const inputBarRef  = useRef(null)
  const sessionIdRef = useRef(uuidv4())

  // Close chat: reset everything and generate a new session
  const closeChat = useCallback(() => {
    sessionIdRef.current = uuidv4()
    hasGreeted.current   = false
    setMessages([])
    setIsTyping(false)
    setIsLocked(false)
    setUnread(0)
    setWelcomeGone(false)
    setWelcomeExit(false)
    setIsOpen(false)
  }, [])

  // Dismiss welcome card with flip animation
  const dismissWelcome = useCallback(() => {
    setWelcomeExit(true)
    setTimeout(() => setWelcomeGone(true), 450)
  }, [])

  // Scroll to bottom whenever messages or typing change
  useEffect(() => {
    if (isOpen) bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isTyping, isOpen])

  // Clear badge when opened
  useEffect(() => { if (isOpen) setUnread(0) }, [isOpen])

  // Proactive greeting — fire once when widget first opens
  useEffect(() => {
    if (!isOpen || hasGreeted.current) return
    hasGreeted.current = true
    triggerWelcome()
  }, [isOpen]) // eslint-disable-line react-hooks/exhaustive-deps

  // ── Streaming helpers ──────────────────────────────────────────────────────
  const appendToken = useCallback((token) => {
    setMessages(prev => {
      const copy = [...prev]
      const last = copy[copy.length - 1]
      if (last?.role === 'ai' && last.streaming)
        copy[copy.length - 1] = { ...last, text: last.text + token }
      return copy
    })
  }, [])

  const finaliseMsg = useCallback((sources, quickReplies, contactStep) => {
    setMessages(prev => {
      const copy = [...prev]
      const last = copy[copy.length - 1]
      if (last?.role === 'ai' && last.streaming)
        copy[copy.length - 1] = { ...last, streaming: false, sources: sources || [], quickReplies: quickReplies || [] }
      // Tag the preceding user message with its contact-flow step so edit can restore it
      if (contactStep) {
        const userIdx = copy.length - 2
        if (userIdx >= 0 && copy[userIdx]?.role === 'user')
          copy[userIdx] = { ...copy[userIdx], contactStep }
      }
      return copy
    })
    if (!isOpen) setUnread(n => n + 1)
  }, [isOpen])

  // Clear quick reply buttons from all messages (called when user sends a message)
  const clearQuickReplies = useCallback(() => {
    setMessages(prev => prev.map(m => m.quickReplies?.length ? { ...m, quickReplies: [] } : m))
  }, [])

  // Edit a user message: truncate from that index, reset backend state, pre-fill the input bar
  const editMessage = useCallback((index) => {
    if (isLocked) return
    const msg = messages[index]
    setMessages(prev => prev.slice(0, index))
    // If this was a contact-form message, wind the backend back to that step
    if (msg.contactStep) {
      fetch('/api/chat/reset-session', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionIdRef.current, to_state: msg.contactStep }),
      }).catch(() => {})
    }
    inputBarRef.current?.fill(msg.text)
  }, [isLocked, messages])

  // ── Silent probe — fires on open, no user bubble shown ───────────────────
  const triggerWelcome = useCallback(async () => {
    setIsTyping(true)
    setIsLocked(true)
    try {
      const res = await fetch('/api/chat/stream', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ message: '__init__', session_id: sessionIdRef.current }),
      })
      if (!res.ok || !res.body) return
      setIsTyping(false)
      setMessages(prev => [...prev, { role: 'ai', text: '', streaming: true, sources: [] }])
      for await (const event of readSSE(res)) {
        if (event.token)         appendToken(event.token)
        if (event.done === true) {
          finaliseMsg(event.sources, event.quick_replies)
          if (event.contact_done) dismissWelcome()
        }
      }
    } catch { /* ignore network errors on open */ } finally {
      setIsTyping(false)
      setIsLocked(false)
    }
  }, [appendToken, finaliseMsg, dismissWelcome])

  // ── Send ───────────────────────────────────────────────────────────────────
  const sendMessage = useCallback(async (text) => {
    if (!text.trim() || isLocked) return

    clearQuickReplies()
    setMessages(prev => [...prev, { role: 'user', text }])
    setIsTyping(true)
    setIsLocked(true)

    try {
      const res = await fetch('/api/chat/stream', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ message: text, session_id: sessionIdRef.current }),
      })

      if (!res.ok || !res.body) {
        const err = await res.json().catch(() => ({}))
        setIsTyping(false)
        setMessages(prev => [...prev, {
          role: 'ai', error: true,
          text: err.detail || `Server error (${res.status}).`,
        }])
        return
      }

      setIsTyping(false)
      setMessages(prev => [...prev, { role: 'ai', text: '', streaming: true, sources: [] }])

      for await (const event of readSSE(res)) {
        if (event.error) {
          setMessages(prev => {
            const c = [...prev]
            c[c.length - 1] = { role: 'ai', error: true, text: event.error, streaming: false }
            return c
          })
          break
        }
        if (event.token)         appendToken(event.token)
        if (event.done === true) {
          finaliseMsg(event.sources, event.quick_replies, event.contact_state)
          if (event.contact_done) dismissWelcome()
        }
      }
    } catch {
      setIsTyping(false)
      const errMsg = 'Unable to reach the server. Please check your connection.'
      setMessages(prev => {
        const c = [...prev]
        if (c[c.length - 1]?.streaming)
          c[c.length - 1] = { role: 'ai', error: true, text: errMsg, streaming: false }
        else c.push({ role: 'ai', error: true, text: errMsg })
        return c
      })
    } finally {
      setIsLocked(false)
    }
  }, [isLocked, appendToken, finaliseMsg, dismissWelcome, clearQuickReplies])

  return (
    <>
      {/* ── Chat panel ─────────────────────────────────────────────────────── */}
      <div
        className={`${styles.widget} ${isOpen ? styles.widgetOpen : ''}`}
        role="dialog"
        aria-label="BSC AI Assistant"
        aria-modal="true"
        aria-hidden={!isOpen}
      >
        {/* Header */}
        <header className={styles.header}>
          <div className={styles.headerLeft}>
            <div className={styles.headerAvatar} aria-hidden="true">
              <BotSVG size={22} color="#fff" />
            </div>
            <div className={styles.headerInfo}>
              <span className={styles.headerTitle}>BSC AI Assistant</span>
              <span className={styles.headerStatus}>
                <span className={styles.statusDot} aria-hidden="true" />
                Online — ready to help
              </span>
            </div>
          </div>
          <div className={styles.headerActions}>
            <button className={styles.iconBtn}
              onClick={() => setIsOpen(false)}
              aria-label="Minimise chat" title="Minimise">
              <MinusIcon />
            </button>
            <button className={styles.iconBtn}
              onClick={closeChat}
              aria-label="Close chat" title="Close">
              <XIcon />
            </button>
          </div>
        </header>

        {/* Messages */}
        <main className={styles.messages} aria-live="polite" aria-relevant="additions">
          {/* Welcome card: visible until contact form is done, then flips away */}
          {!welcomeGone && <WelcomeScreen onChip={sendMessage} exiting={welcomeExit} />}
          {messages.map((msg, i) => (
            <ChatMessage key={i} message={msg} onSend={sendMessage}
              onEdit={() => editMessage(i)} isLocked={isLocked} />
          ))}
          {isTyping && <TypingIndicator />}
          <div ref={bottomRef} />
        </main>

        {/* Input */}
        <InputBar ref={inputBarRef} onSend={sendMessage} disabled={isLocked} />
      </div>

      {/* ── Launcher button ────────────────────────────────────────────────── */}
      <button
        className={styles.launcher}
        onClick={() => setIsOpen(o => !o)}
        aria-label={isOpen ? 'Close chat' : 'Open BSC AI Assistant'}
        aria-expanded={isOpen}
      >
        {/* Chat icon — visible when closed */}
        <span className={`${styles.launcherIcon} ${isOpen ? styles.launcherIconHidden : ''}`}
              aria-hidden="true">
          <ChatIcon />
        </span>
        {/* Close icon — visible when open */}
        <span className={`${styles.launcherIcon} ${!isOpen ? styles.launcherIconHidden : ''}`}
              aria-hidden="true">
          <XIcon />
        </span>
        {/* Unread badge */}
        {!isOpen && unread > 0 && (
          <span className={styles.badge} aria-label={`${unread} unread messages`}>
            {unread > 9 ? '9+' : unread}
          </span>
        )}
      </button>
    </>
  )
}
