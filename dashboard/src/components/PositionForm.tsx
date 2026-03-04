import { useState, useEffect } from 'react'
import type { Position, PositionInput } from '../types'

interface Props {
  initial?: Position | null
  onSave: (data: PositionInput) => void
  onCancel: () => void
}

export default function PositionForm({ initial, onSave, onCancel }: Props) {
  const [ticker, setTicker] = useState('')
  const [name, setName] = useState('')
  const [thesis, setThesis] = useState('')
  const [triggers, setTriggers] = useState<string[]>([''])

  useEffect(() => {
    if (initial) {
      setTicker(initial.ticker)
      setName(initial.name)
      setThesis(initial.thesis)
      setTriggers(initial.bear_triggers.length > 0 ? [...initial.bear_triggers] : [''])
    }
  }, [initial])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSave({
      ticker: ticker.trim().toUpperCase(),
      name: name.trim(),
      thesis: thesis.trim(),
      bear_triggers: triggers.filter((t) => t.trim() !== ''),
    })
  }

  const addTrigger = () => setTriggers([...triggers, ''])

  const updateTrigger = (index: number, value: string) => {
    const updated = [...triggers]
    updated[index] = value
    setTriggers(updated)
  }

  const removeTrigger = (index: number) => {
    setTriggers(triggers.filter((_, i) => i !== index))
  }

  return (
    <div className="modal-backdrop" onClick={onCancel}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h2>{initial ? 'Position bearbeiten' : 'Neue Position'}</h2>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="ticker">Ticker</label>
            <input
              id="ticker"
              type="text"
              value={ticker}
              onChange={(e) => setTicker(e.target.value)}
              placeholder="z.B. NVDA"
              required
              disabled={!!initial}
            />
          </div>

          <div className="form-group">
            <label htmlFor="name">Unternehmen</label>
            <input
              id="name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="z.B. NVIDIA"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="thesis">Investment-These</label>
            <textarea
              id="thesis"
              value={thesis}
              onChange={(e) => setThesis(e.target.value)}
              placeholder="Beschreibe deine Bull-These..."
              rows={6}
              required
            />
          </div>

          <div className="form-group">
            <label>Bear-Trigger</label>
            {triggers.map((trigger, i) => (
              <div key={i} className="trigger-row">
                <input
                  type="text"
                  value={trigger}
                  onChange={(e) => updateTrigger(i, e.target.value)}
                  placeholder="z.B. Umsatzwachstum unter 10%"
                />
                {triggers.length > 1 && (
                  <button
                    type="button"
                    className="btn btn-icon"
                    onClick={() => removeTrigger(i)}
                    title="Entfernen"
                  >
                    ✕
                  </button>
                )}
              </div>
            ))}
            <button type="button" className="btn btn-secondary btn-sm" onClick={addTrigger}>
              + Trigger hinzufügen
            </button>
          </div>

          <div className="modal-actions">
            <button type="button" className="btn btn-secondary" onClick={onCancel}>
              Abbrechen
            </button>
            <button type="submit" className="btn btn-primary">
              {initial ? 'Speichern' : 'Hinzufügen'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
