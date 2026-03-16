import type {
  Position, PositionInput, TaskInfo, RunStatus, RunSummary, RunDetail,
  ConversationSummary, ConversationDetail, SendMessageResponse
} from '../types'

const BASE = '/api'

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(error.detail || res.statusText)
  }
  if (res.status === 204) return undefined as T
  return res.json()
}

export const api = {
  // Positions
  getPositions: () =>
    request<Position[]>('/positions'),

  createPosition: (data: PositionInput) =>
    request<Position>('/positions', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  updatePosition: (ticker: string, data: PositionInput) =>
    request<Position>(`/positions/${encodeURIComponent(ticker)}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),

  deletePosition: (ticker: string) =>
    request<void>(`/positions/${encodeURIComponent(ticker)}`, {
      method: 'DELETE',
    }),

  // Tasks
  getTasks: () =>
    request<TaskInfo[]>('/tasks'),

  triggerRun: (taskName: string, dryRun = true) =>
    request<RunStatus>(`/tasks/${encodeURIComponent(taskName)}/run`, {
      method: 'POST',
      body: JSON.stringify({ dry_run: dryRun }),
    }),

  getRunStatus: (taskName: string, runId: string) =>
    request<RunStatus>(`/tasks/${encodeURIComponent(taskName)}/run/${runId}`),

  // Runs
  getRuns: (limit = 30) =>
    request<RunSummary[]>(`/runs?limit=${limit}`),

  getRunDetail: (runId: number) =>
    request<RunDetail>(`/runs/${runId}`),

  // Research
  getConversations: () =>
    request<ConversationSummary[]>('/research/conversations'),

  createConversation: (title = 'Neue Recherche') =>
    request<ConversationSummary>('/research/conversations', {
      method: 'POST',
      body: JSON.stringify({ title }),
    }),

  getConversation: (id: number) =>
    request<ConversationDetail>(`/research/conversations/${id}`),

  deleteConversation: (id: number) =>
    request<void>(`/research/conversations/${id}`, { method: 'DELETE' }),

  sendMessage: (conversationId: number, content: string) =>
    request<SendMessageResponse>(
      `/research/conversations/${conversationId}/messages`,
      { method: 'POST', body: JSON.stringify({ content }) }
    ),

  confirmPosition: (conversationId: number, data: PositionInput) =>
    request<Position>(
      `/research/conversations/${conversationId}/confirm-position`,
      { method: 'POST', body: JSON.stringify(data) }
    ),
}
