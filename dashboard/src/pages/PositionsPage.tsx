import { useState, useEffect, useCallback } from 'react'
import { api } from '../api/client'
import type { Position, PositionInput } from '../types'
import PositionCard from '../components/PositionCard'
import PositionForm from '../components/PositionForm'
import TaskTriggerButton from '../components/TaskTriggerButton'

export default function PositionsPage() {
  const [positions, setPositions] = useState<Position[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showForm, setShowForm] = useState(false)
  const [editingPosition, setEditingPosition] = useState<Position | null>(null)

  const loadPositions = useCallback(async () => {
    try {
      setError(null)
      const data = await api.getPositions()
      setPositions(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Fehler beim Laden')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadPositions()
  }, [loadPositions])

  const handleSave = async (data: PositionInput) => {
    try {
      if (editingPosition) {
        await api.updatePosition(editingPosition.ticker, data)
      } else {
        await api.createPosition(data)
      }
      setShowForm(false)
      setEditingPosition(null)
      loadPositions()
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Fehler beim Speichern')
    }
  }

  const handleEdit = (position: Position) => {
    setEditingPosition(position)
    setShowForm(true)
  }

  const handleDelete = async (ticker: string) => {
    if (!confirm(`Position "${ticker}" wirklich löschen?`)) return
    try {
      await api.deletePosition(ticker)
      loadPositions()
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Fehler beim Löschen')
    }
  }

  const handleCancel = () => {
    setShowForm(false)
    setEditingPosition(null)
  }

  if (loading) return <div className="loading">Lade Positionen…</div>
  if (error) return <div className="error-message">{error}</div>

  return (
    <div className="page">
      <div className="page-header">
        <h2>Investment-Positionen</h2>
        <button
          className="btn btn-primary"
          onClick={() => {
            setEditingPosition(null)
            setShowForm(true)
          }}
        >
          + Neue Position
        </button>
      </div>

      {positions.length === 0 ? (
        <div className="empty-state">
          Keine Positionen konfiguriert. Füge deine erste Position hinzu.
        </div>
      ) : (
        <div className="card-grid">
          {positions.map((pos) => (
            <PositionCard
              key={pos.ticker}
              position={pos}
              onEdit={handleEdit}
              onDelete={handleDelete}
            />
          ))}
        </div>
      )}

      <div className="section">
        <h3>Analyse ausführen</h3>
        <TaskTriggerButton taskName="investment_thesis_check" label="Thesis Check (täglich)" />
        <TaskTriggerButton taskName="investment_thesis_check_weekend" label="Thesis Check (Wochenend-Review)" />
      </div>

      {showForm && (
        <PositionForm
          initial={editingPosition}
          onSave={handleSave}
          onCancel={handleCancel}
        />
      )}
    </div>
  )
}
