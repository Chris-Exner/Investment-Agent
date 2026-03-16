import { useEffect, useRef } from 'react'
import type { ChatMessage as ChatMessageType, PositionProposal } from '../../types'
import ChatMessage from './ChatMessage'

interface Props {
  messages: ChatMessageType[]
  sending: boolean
  onConfirmPosition?: (proposal: PositionProposal) => void
}

export default function ChatWindow({ messages, sending, onConfirmPosition }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, sending])

  // Filter out tool messages for display
  const visibleMessages = messages.filter((m) => m.role !== 'tool')

  return (
    <div className="chat-messages">
      {visibleMessages.length === 0 && !sending && (
        <div className="chat-welcome">
          <h3>Investment-Recherche</h3>
          <p>
            Starte eine Diskussion über Branchen, Trends oder einzelne Unternehmen.
            Der Agent kann Live-Marktdaten abrufen und hilft dir, neue Investments zu identifizieren.
          </p>
          <div className="chat-suggestions">
            <span>Beispiele:</span>
            <ul>
              <li>„Welche Branchen profitieren aktuell von KI?"</li>
              <li>„Analysiere NVDA als langfristiges Investment"</li>
              <li>„Vergleiche die Bewertung von AMD, INTC und NVDA"</li>
              <li>„Welche Sektoren performen aktuell am besten?"</li>
            </ul>
          </div>
        </div>
      )}
      {visibleMessages.map((msg) => (
        <ChatMessage
          key={msg.id}
          message={msg}
          onConfirmPosition={onConfirmPosition}
        />
      ))}
      {sending && (
        <div className="chat-msg chat-msg-assistant">
          <div className="chat-msg-bubble">
            <div className="typing-indicator">
              <span></span><span></span><span></span>
            </div>
          </div>
        </div>
      )}
      <div ref={bottomRef} />
    </div>
  )
}
