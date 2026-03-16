import type { ChatMessage as ChatMessageType, PositionProposal } from '../../types'
import DataCardRenderer from './DataCardRenderer'

interface Props {
  message: ChatMessageType
  onConfirmPosition?: (proposal: PositionProposal) => void
}

export default function ChatMessage({ message, onConfirmPosition }: Props) {
  const isUser = message.role === 'user'

  // Don't render tool messages — data shown via data_cards on assistant messages
  if (message.role === 'tool') return null

  return (
    <div className={`chat-msg ${isUser ? 'chat-msg-user' : 'chat-msg-assistant'}`}>
      <div className="chat-msg-bubble">
        {message.content && (
          <div className="chat-msg-content">{message.content}</div>
        )}
        {message.data_cards && message.data_cards.length > 0 && (
          <div className="chat-msg-cards">
            {message.data_cards.map((card, i) => (
              <DataCardRenderer
                key={i}
                card={card}
                onConfirmPosition={onConfirmPosition}
              />
            ))}
          </div>
        )}
      </div>
      <span className="chat-msg-time">
        {message.created_at
          ? new Date(message.created_at).toLocaleTimeString('de-DE', {
              hour: '2-digit',
              minute: '2-digit',
            })
          : ''}
      </span>
    </div>
  )
}
