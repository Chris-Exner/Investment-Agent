import type { ConversationSummary } from '../../types'

interface Props {
  conversations: ConversationSummary[]
  activeId: number | null
  onSelect: (id: number) => void
  onDelete: (id: number) => void
}

export default function ConversationList({ conversations, activeId, onSelect, onDelete }: Props) {
  if (conversations.length === 0) {
    return <p className="conv-empty">Keine Recherchen vorhanden</p>
  }

  return (
    <ul className="conv-list">
      {conversations.map((c) => (
        <li
          key={c.id}
          className={`conv-item ${c.id === activeId ? 'active' : ''}`}
          onClick={() => onSelect(c.id)}
        >
          <div className="conv-item-title">{c.title}</div>
          <div className="conv-item-meta">
            {c.message_count} Nachrichten &middot;{' '}
            {new Date(c.updated_at).toLocaleDateString('de-DE', {
              day: '2-digit',
              month: '2-digit',
              hour: '2-digit',
              minute: '2-digit',
            })}
          </div>
          <button
            className="conv-item-delete"
            title="Recherche löschen"
            onClick={(e) => {
              e.stopPropagation()
              onDelete(c.id)
            }}
          >
            ×
          </button>
        </li>
      ))}
    </ul>
  )
}
