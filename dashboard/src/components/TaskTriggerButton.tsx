import { useState, useRef, useCallback } from 'react'
import { api } from '../api/client'
import type { RunStatus } from '../types'

interface Props {
  taskName: string
  label: string
  onRunComplete?: () => void
}

export default function TaskTriggerButton({ taskName, label, onRunComplete }: Props) {
  const [status, setStatus] = useState<'idle' | 'running' | 'success' | 'failed'>('idle')
  const [result, setResult] = useState<RunStatus | null>(null)
  const intervalRef = useRef<number | null>(null)

  const clearPolling = () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
      intervalRef.current = null
    }
  }

  const trigger = useCallback(async (dryRun: boolean) => {
    setStatus('running')
    setResult(null)
    clearPolling()

    try {
      const run = await api.triggerRun(taskName, dryRun)
      const runId = run.run_id

      intervalRef.current = window.setInterval(async () => {
        try {
          const s = await api.getRunStatus(taskName, runId)
          if (s.status !== 'running') {
            clearPolling()
            setStatus(s.status as 'success' | 'failed')
            setResult(s)
            onRunComplete?.()
          }
        } catch {
          clearPolling()
          setStatus('failed')
        }
      }, 2000)
    } catch (err) {
      setStatus('failed')
      setResult({
        run_id: '',
        task_name: taskName,
        status: 'failed',
        started_at: null,
        duration_seconds: null,
        error_message: err instanceof Error ? err.message : 'Unbekannter Fehler',
        tokens_input: 0,
        tokens_output: 0,
        analysis_text: null,
      })
    }
  }, [taskName])

  return (
    <div className="trigger-block">
      <div className="trigger-header">
        <span className="trigger-label">{label}</span>
        <div className="trigger-buttons">
          <button
            className="btn btn-primary btn-sm"
            onClick={() => trigger(true)}
            disabled={status === 'running'}
          >
            {status === 'running' ? '⏳ Läuft…' : '▶ Dry Run'}
          </button>
          <button
            className="btn btn-secondary btn-sm"
            onClick={() => trigger(false)}
            disabled={status === 'running'}
          >
            ▶ + Senden
          </button>
        </div>
      </div>

      {status === 'success' && result && (
        <div className="trigger-result trigger-result-success">
          <div className="trigger-meta">
            ✅ Fertig in {result.duration_seconds?.toFixed(1)}s
            {' · '}{result.tokens_input} / {result.tokens_output} Tokens
          </div>
          {result.analysis_text && (
            <details className="trigger-details">
              <summary>Analyse anzeigen</summary>
              <div
                className="analysis-text"
                dangerouslySetInnerHTML={{ __html: result.analysis_text }}
              />
            </details>
          )}
        </div>
      )}

      {status === 'failed' && result && (
        <div className="trigger-result trigger-result-error">
          ❌ {result.error_message || 'Fehlgeschlagen'}
        </div>
      )}
    </div>
  )
}
