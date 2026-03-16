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

// --- Research ---

export interface ConversationSummary {
  id: number
  title: string
  created_at: string
  updated_at: string
  message_count: number
  status: string
}

export interface ChatMessage {
  id: number
  role: 'user' | 'assistant' | 'tool'
  content: string
  tool_calls: ToolCallInfo[] | null
  data_cards: DataCard[]
  created_at: string
}

export interface ToolCallInfo {
  id: string
  function_name: string
  arguments: Record<string, unknown>
}

export interface DataCard {
  type: string
  function_name: string
  arguments: Record<string, unknown>
  data: Record<string, unknown> | Record<string, unknown>[]
}

export interface ConversationDetail extends ConversationSummary {
  messages: ChatMessage[]
}

export interface SendMessageResponse {
  user_message: ChatMessage
  assistant_message: ChatMessage
  position_proposal: PositionProposal | null
  tokens_input: number
  tokens_output: number
}

export interface PositionProposal {
  ticker: string
  name: string
  thesis: string
  bear_triggers: string[]
  reasoning: string
}
