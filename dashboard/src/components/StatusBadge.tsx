interface Props {
  status: string
}

export default function StatusBadge({ status }: Props) {
  const classMap: Record<string, string> = {
    success: 'badge badge-success',
    failed: 'badge badge-error',
    running: 'badge badge-running',
  }

  const labelMap: Record<string, string> = {
    success: 'Erfolgreich',
    failed: 'Fehlgeschlagen',
    running: 'Läuft…',
  }

  return (
    <span className={classMap[status] || 'badge'}>
      {labelMap[status] || status}
    </span>
  )
}
