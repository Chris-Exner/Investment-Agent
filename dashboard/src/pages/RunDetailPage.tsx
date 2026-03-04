import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import type { RunDetail } from '../types'
import StatusBadge from '../components/StatusBadge'

function formatDate(iso: string): string {
  const d = new Date(iso)
  return d.toLocaleString('de-DE', {
    weekday: 'long',
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}

export default function RunDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [run, setRun] = useState<RunDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!id) return
    async function load() {
      try {
        const data = await api.getRunDetail(parseInt(id!, 10))
        setRun(data)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Fehler beim Laden')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [id])

  if (loading) return <div className="loading">Lade Details…</div>
  if (error) return <div className="error-message">{error}</div>
  if (!run) return <div className="error-message">Run nicht gefunden</div>

  return (
    <div className="page">
      <button className="btn btn-secondary btn-sm" onClick={() => navigate('/runs')}>
        ← Zurück
      </button>

      <div className="detail-header">
        <h2>{run.task_name}</h2>
        <StatusBadge status={run.status} />
      </div>

      <div className="detail-meta">
        <div className="meta-item">
          <span className="meta-label">Zeitpunkt</span>
          <span>{formatDate(run.started_at)}</span>
        </div>
        {run.duration_seconds != null && (
          <div className="meta-item">
            <span className="meta-label">Dauer</span>
            <span>{run.duration_seconds.toFixed(1)}s</span>
          </div>
        )}
        <div className="meta-item">
          <span className="meta-label">Kanäle</span>
          <span>
            {run.channels_delivered.length > 0
              ? run.channels_delivered.join(', ')
              : 'dry-run'}
          </span>
        </div>
      </div>

      {run.error_message && (
        <div className="error-block">
          <strong>Fehler:</strong> {run.error_message}
        </div>
      )}

      {run.analysis_text && (
        <div className="section">
          <h3>Analyse</h3>
          <div
            className="analysis-text"
            dangerouslySetInnerHTML={{ __html: run.analysis_text }}
          />
        </div>
      )}

      {run.structured_data && (
        <div className="section">
          <details>
            <summary>Strukturierte Daten (JSON)</summary>
            <pre className="json-block">
              {JSON.stringify(run.structured_data, null, 2)}
            </pre>
          </details>
        </div>
      )}
    </div>
  )
}
