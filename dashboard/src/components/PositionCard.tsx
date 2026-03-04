import type { Position } from '../types'

interface Props {
  position: Position
  onEdit: (position: Position) => void
  onDelete: (ticker: string) => void
}

export default function PositionCard({ position, onEdit, onDelete }: Props) {
  const thesisPreview =
    position.thesis.length > 180
      ? position.thesis.slice(0, 180) + '…'
      : position.thesis

  return (
    <div className="card">
      <div className="card-header">
        <span className="card-ticker">{position.ticker}</span>
        <span className="card-name">{position.name}</span>
      </div>

      <p className="card-thesis">{thesisPreview}</p>

      {position.bear_triggers.length > 0 && (
        <div className="card-triggers">
          <span className="card-triggers-label">
            🐻 {position.bear_triggers.length} Bear-Trigger
          </span>
          <ul className="card-triggers-list">
            {position.bear_triggers.map((t, i) => (
              <li key={i}>{t}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="card-actions">
        <button className="btn btn-secondary" onClick={() => onEdit(position)}>
          Bearbeiten
        </button>
        <button className="btn btn-danger" onClick={() => onDelete(position.ticker)}>
          Löschen
        </button>
      </div>
    </div>
  )
}
