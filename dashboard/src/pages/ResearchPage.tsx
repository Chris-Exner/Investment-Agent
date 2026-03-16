import { useState, useEffect, useCallback } from 'react'
import { api } from '../api/client'
import type { ConversationSummary, ConversationDetail, PositionProposal, ChatMessage } from '../types'
import ConversationList from '../components/research/ConversationList'
import ChatWindow from '../components/research/ChatWindow'
import ChatInput from '../components/research/ChatInput'

export default function ResearchPage() {
  const [conversations, setConversations] = useState<ConversationSummary[]>([])
  const [activeId, setActiveId] = useState<number | null>(null)
  const [conversation, setConversation] = useState<ConversationDetail | null>(null)
  const [sending, setSending] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Load conversations list
  const loadConversations = useCallback(async () => {
    try {
      const data = await api.getConversations()
      setConversations(data)
    } catch (err) {
      console.error('Failed to load conversations:', err)
    }
  }, [])

  useEffect(() => {
    loadConversations()
  }, [loadConversations])

  // Load active conversation detail
  useEffect(() => {
    if (activeId === null) {
      setConversation(null)
      return
    }
    let cancelled = false
    async function load() {
      try {
        const data = await api.getConversation(activeId!)
        if (!cancelled) setConversation(data)
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : 'Fehler beim Laden')
      }
    }
    load()
    return () => { cancelled = true }
  }, [activeId])

  // Create new conversation
  const handleNew = useCallback(async () => {
    try {
      const conv = await api.createConversation()
      setConversations((prev) => [conv, ...prev])
      setActiveId(conv.id)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Fehler beim Erstellen')
    }
  }, [])

  // Delete conversation
  const handleDelete = useCallback(async (id: number) => {
    try {
      await api.deleteConversation(id)
      setConversations((prev) => prev.filter((c) => c.id !== id))
      if (activeId === id) {
        setActiveId(null)
        setConversation(null)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Fehler beim Löschen')
    }
  }, [activeId])

  // Send message
  const handleSend = useCallback(async (content: string) => {
    if (!activeId || sending) return

    setSending(true)
    setError(null)

    // Optimistically add user message
    const tempUserMsg: ChatMessage = {
      id: Date.now(),
      role: 'user',
      content,
      tool_calls: null,
      data_cards: [],
      created_at: new Date().toISOString(),
    }
    setConversation((prev) => prev ? {
      ...prev,
      messages: [...prev.messages, tempUserMsg],
    } : prev)

    try {
      const response = await api.sendMessage(activeId, content)

      // Replace temp message with real ones
      setConversation((prev) => {
        if (!prev) return prev
        // Remove temp user message, add real user + assistant
        const filtered = prev.messages.filter((m) => m.id !== tempUserMsg.id)
        return {
          ...prev,
          messages: [...filtered, response.user_message, response.assistant_message],
          message_count: prev.message_count + 2,
        }
      })

      // Refresh conversation list (title may have changed)
      loadConversations()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Fehler bei der Verarbeitung')
      // Remove temp message on error
      setConversation((prev) => prev ? {
        ...prev,
        messages: prev.messages.filter((m) => m.id !== tempUserMsg.id),
      } : prev)
    } finally {
      setSending(false)
    }
  }, [activeId, sending, loadConversations])

  // Confirm position from proposal
  const handleConfirmPosition = useCallback(async (proposal: PositionProposal) => {
    if (!activeId) return

    try {
      await api.confirmPosition(activeId, {
        ticker: proposal.ticker,
        name: proposal.name,
        thesis: proposal.thesis,
        bear_triggers: proposal.bear_triggers,
      })

      // Add confirmation message to chat
      const confirmMsg: ChatMessage = {
        id: Date.now(),
        role: 'assistant',
        content: `Position **${proposal.ticker}** (${proposal.name}) wurde erfolgreich erstellt und wird ab sofort im Investment Thesis Check überwacht.`,
        tool_calls: null,
        data_cards: [],
        created_at: new Date().toISOString(),
      }
      setConversation((prev) => prev ? {
        ...prev,
        messages: [...prev.messages, confirmMsg],
      } : prev)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Fehler beim Erstellen der Position')
    }
  }, [activeId])

  return (
    <div className="research-page">
      <aside className="research-sidebar">
        <button className="btn btn-primary research-new-btn" onClick={handleNew}>
          + Neue Recherche
        </button>
        <ConversationList
          conversations={conversations}
          activeId={activeId}
          onSelect={setActiveId}
          onDelete={handleDelete}
        />
      </aside>

      <section className="research-chat">
        {error && (
          <div className="research-error">
            {error}
            <button className="btn-icon" onClick={() => setError(null)}>×</button>
          </div>
        )}

        {conversation ? (
          <>
            <ChatWindow
              messages={conversation.messages}
              sending={sending}
              onConfirmPosition={handleConfirmPosition}
            />
            <ChatInput onSend={handleSend} disabled={sending} />
          </>
        ) : (
          <div className="research-empty">
            <h3>Investment-Recherche</h3>
            <p>
              Starte eine neue Recherche oder wähle eine bestehende aus der Seitenleiste.
            </p>
            <button className="btn btn-primary" onClick={handleNew}>
              Neue Recherche starten
            </button>
          </div>
        )}
      </section>
    </div>
  )
}
