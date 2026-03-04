import { useNavigate } from 'react-router-dom'
import type { RunSummary } from '../types'
import StatusBadge from './StatusBadge'

interface Props {
  run: RunSummary
}

function formatDate(iso: string): string {
  const d = new Date(iso)
  return d.toLocaleString('de-DE', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export default function RunRow({ run }: Props) {
  const navigate = useNavigate()

  return (
    <tr className="run-row" onClick={() => navigate(`/runs/${run.id}`)}>
      <td className="run-task">{run.task_name}</td>
      <td><StatusBadge status={run.status} /></td>
      <td className="run-date">{formatDate(run.started_at)}</td>
      <td className="run-duration">
        {run.duration_seconds != null ? `${run.duration_seconds.toFixed(1)}s` : '–'}
      </td>
      <td className="run-channels">
        {run.channels_delivered.length > 0
          ? run.channels_delivered.join(', ')
          : run.status === 'success' ? 'dry-run' : '–'}
      </td>
      <td className="run-error">
        {run.error_message
          ? <span title={run.error_message}>{run.error_message.slice(0, 60)}</span>
          : '–'}
      </td>
    </tr>
  )
}
