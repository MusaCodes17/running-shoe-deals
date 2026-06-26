import { useState, useRef, useEffect } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { MessageCircle, X, Send, Maximize2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import { UserMessage, AssistantMessage, ModelDivider, EmptyState } from '@/components/chat/ChatMessages'
import { useChatStream } from '@/hooks/useChatStream'

const DEFAULT_MODEL = 'claude-haiku-4-5-20251001'

export default function ChatDrawer() {
  const [isOpen, setIsOpen] = useState(false)
  const [input, setInput] = useState('')

  const { displayMessages, apiMessages, isStreaming, sendMessage } = useChatStream({
    model: DEFAULT_MODEL,
  })

  const messagesEndRef = useRef(null)
  const textareaRef = useRef(null)
  const location = useLocation()
  const navigate = useNavigate()

  const hidden = location.pathname === '/assistant'

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [displayMessages])

  useEffect(() => {
    if (isOpen) textareaRef.current?.focus()
  }, [isOpen])

  const handleSend = (content) => {
    const trimmed = typeof content === 'string' ? content : input
    if (!trimmed.trim() || isStreaming) return
    sendMessage(trimmed.trim())
    setInput('')
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend(input)
    }
  }

  const handleTextareaInput = (e) => {
    e.target.style.height = 'auto'
    e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px'
  }

  const handleOpenFullPage = () => {
    // Hand off the current conversation to the full page via sessionStorage
    if (displayMessages.length > 0) {
      sessionStorage.setItem(
        'son-of-anton:drawer-handoff',
        JSON.stringify({ displayMessages, apiMessages })
      )
    }
    setIsOpen(false)
    navigate('/assistant')
  }

  if (hidden) return null

  return (
    <>
      {/* Floating trigger */}
      <button
        onClick={() => setIsOpen(true)}
        aria-label="Open Son of Anton"
        className={cn(
          'fixed bottom-6 right-6 z-40 flex items-center gap-2 rounded-full bg-primary px-4 py-3 text-sm font-semibold text-primary-foreground shadow-lg hover:bg-primary/90 transition-all duration-200',
          isOpen ? 'opacity-0 pointer-events-none translate-y-2' : 'opacity-100 translate-y-0'
        )}
      >
        <MessageCircle className="h-4 w-4" />
        Son of Anton
      </button>

      {/* Backdrop */}
      <div
        className={cn(
          'fixed inset-0 z-[50] bg-black/40 transition-opacity duration-300',
          isOpen ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'
        )}
        onClick={() => setIsOpen(false)}
      />

      {/* Drawer */}
      <div
        className={cn(
          'fixed right-0 top-0 z-[51] flex h-full w-[400px] flex-col border-l border-border bg-[#101215] transition-transform duration-300',
          'max-[500px]:w-full',
          isOpen ? 'translate-x-0' : 'translate-x-full'
        )}
      >
        {/* Header */}
        <div className="flex shrink-0 items-center justify-between border-b border-border px-4 py-3">
          <span className="font-semibold text-foreground">Son of Anton</span>
          <div className="flex items-center gap-1">
            <button
              onClick={handleOpenFullPage}
              className="rounded-md p-1 text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
              aria-label="Open full page"
              title="Open full page"
            >
              <Maximize2 className="h-4 w-4" />
            </button>
            <button
              onClick={() => setIsOpen(false)}
              className="rounded-md p-1 text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
              aria-label="Close"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-4 py-3">
          {displayMessages.length === 0 ? (
            <EmptyState onPromptClick={handleSend} isStreaming={isStreaming} />
          ) : (
            <div className="space-y-3">
              {displayMessages.map((msg) => {
                if (msg.role === 'user') return <UserMessage key={msg.id} content={msg.content} />
                if (msg.role === 'divider') return <ModelDivider key={msg.id} content={msg.content} />
                return <AssistantMessage key={msg.id} message={msg} />
              })}
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="shrink-0 border-t border-border px-4 py-3">
          <div className="flex items-end gap-2">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              onInput={handleTextareaInput}
              placeholder="Ask about your shoes…"
              disabled={isStreaming}
              rows={1}
              className="flex-1 resize-none rounded-[10px] border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 focus:ring-offset-background disabled:opacity-50"
              style={{ minHeight: '38px', maxHeight: '120px', overflowY: 'auto' }}
            />
            <button
              onClick={() => handleSend(input)}
              disabled={isStreaming || !input.trim()}
              aria-label="Send"
              className="flex h-[38px] w-[38px] shrink-0 items-center justify-center rounded-[10px] bg-primary text-primary-foreground transition-colors hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50"
            >
              <Send className="h-4 w-4" />
            </button>
          </div>
          <p className="mt-1.5 text-xs text-faint">Enter to send · Shift+Enter for newline</p>
        </div>
      </div>
    </>
  )
}
