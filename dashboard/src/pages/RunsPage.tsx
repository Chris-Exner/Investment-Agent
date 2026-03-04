import { useState, useEffect } from 'react'
import { api } from '../api/client'
import type { RunSummary, TaskInfo } from '../types'
import RunRow from '../components/RunRow'
import TaskTriggerButton from '../components/TaskTriggerButton'

export default function RunsPage() {
  const [runs, setRuns] = useState<RunSummary[]>([])
  const [tasks, setTasks] = useState<TaskInfo[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function load() {
      try {
        const [runsData, tasksData] = await Promise.all([
          api.getRuns(30),
          api.getTasks(),
        ])
        setRuns(runsData)
        setTasks(tasksData)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Fehler beim Laden')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  if (loading) return <div className="loading">Lade Daten…</div>
  if (error) return <div className="error-message">{error}</div>

  return (
    <div className="page">
      <div className="page-header">
        <h2>Letzte Läufe</h2>
        <button className="btn btn-secondary" onClick={() => window.location.reload()}>
          ↻ Aktualisieren
        </button>
      </div>

      <div className="section">
        <h3>Task ausführen</h3>
        <div className="trigger-grid">
          {tasks.map((task) => (
            <TaskTriggerButton
              key={task.name}
              taskName={task.name}
              label={`${task.description || task.name}`}
            />
          ))}
        </div>
      </div>

      <div className="section">
        <h3>Verlauf</h3>
        {runs.length === 0 ? (
          <div className="empty-state">Noch keine Läufe aufgezeichnet.</div>
        ) : (
          <div className="table-wrapper">
            <table className="table">
              <thead>
                <tr>
                  <th>Task</th>
                  <th>Status</th>
                  <th>Zeitpunkt</th>
                  <th>Dauer</th>
                  <th>Kanäle</th>
                  <th>Fehler</th>
                </tr>
              </thead>
              <tbody>
                {runs.map((run) => (
                  <RunRow key={run.id} run={run} />
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
