// --- Positions ---

export interface Position {
  ticker: string
  name: string
  thesis: string
  bear_triggers: string[]
}

export type PositionInput = Position

// --- Tasks ---

export interface TaskInfo {
  name: string
  description: string
  analysis_type: string
  schedule_cron: string
  schedule_enabled: boolean
  has_positions: boolean
}

// --- Runs ---

export interface RunStatus {
  run_id: string
  task_name: string
  status: 'running' | 'success' | 'failed'
  started_at: string | null
  duration_seconds: number | null
  error_message: string | null
  tokens_input: number
  tokens_output: number
  analysis_text: string | null
}

export interface RunSummary {
  id: number
  task_name: string
  status: string
  started_at: string
  completed_at: string | null
  duration_seconds: number | null
  channels_delivered: string[]
  error_message: string | null
  result_id: number | null
}

export interface RunDetail extends RunSummary {
  analysis_text: string | null
  structured_data: Record<string, unknown> | null
}
