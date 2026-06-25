import { useState, useRef, useEffect } from 'react'
import { useLocation } from 'react-router-dom'
import { MessageCircle, X, Send, Check, Wrench } from 'lucide-react'
import Markdown from 'react-markdown'
import { cn } from '@/lib/utils'

const DEFAULT_MODEL = 'claude-haiku-4-5-20251001'

const SUGGESTED_PROMPTS = [
  'How are my shoes holding up?',
  'Any good deals on Adidas right now?',
  'Which shoe should I retire soon?',
  'Log 10km on my Teal Evo SL from today',
]

const MARKDOWN_COMPONENTS = {
  p: ({ children }) => <p className="mb-1.5 last:mb-0 leading-relaxed">{children}</p>,
  ul: ({ children }) => <ul className="list-disc pl-4 mb-1.5 space-y-0.5">{children}</ul>,
  ol: ({ children }) => <ol className="list-decimal pl-4 mb-1.5 space-y-0.5">{children}</ol>,
  li: ({ children }) => <li className="leading-relaxed">{children}</li>,
  strong: ({ children }) => <strong className="font-semibold text-foreground">{children}</strong>,
  em: ({ children }) => <em className="italic">{children}</em>,
  a: ({ href, children }) => (
    <a href={href} className="text-primary underline" target="_blank" rel="noopener noreferrer">
      {children}
    </a>
  ),
  h1: ({ children }) => <h1 className="text-sm font-bold mb-1 mt-2 first:mt-0">{children}</h1>,
  h2: ({ children }) => <h2 className="text-sm font-semibold mb-1 mt-2 first:mt-0">{children}</h2>,
  h3: ({ children }) => <h3 className="text-sm font-semibold mb-0.5 mt-1.5 first:mt-0">{children}</h3>,
  code: ({ children, className }) =>
    className ? (
      <pre className="bg-background rounded p-2 overflow-x-auto text-xs mb-1.5 border border-border">
        <code>{children}</code>
      </pre>
    ) : (
      <code className="bg-background rounded px-1 py-0.5 text-xs">{children}</code>
    ),
  pre: ({ children }) => <>{children}</>,
}

function ToolPill({ indicator }) {
  const isDone = indicator.status !== 'calling'
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full transition-all',
        isDone ? 'text-faint' : 'text-muted-foreground bg-secondary animate-pulse'
      )}
    >
      {isDone ? (
        <Check className="h-3 w-3 text-primary/70" />
      ) : (
        <Wrench className="h-3 w-3" />
      )}
      {indicator.tool}
    </span>
  )
}

function UserMessage({ content }) {
  return (
    <div className="flex justify-end">
      <div className="max-w-[85%] rounded-[12px] rounded-br-[4px] bg-accent px-3 py-2 text-sm text-accent-foreground">
        <p className="whitespace-pre-wrap leading-relaxed">{content}</p>
      </div>
    </div>
  )
}

function AssistantMessage({ message }) {
  return (
    <div className="flex justify-start">
      <div className="max-w-[90%] rounded-[12px] rounded-bl-[4px] bg-secondary px-3 py-2 text-sm text-foreground">
        {message.toolIndicators?.length > 0 && (
          <div className="flex flex-wrap gap-1 mb-2 border-b border-border pb-2">
            {message.toolIndicators.map((ind) => (
              <ToolPill key={ind.id} indicator={ind} />
            ))}
          </div>
        )}

        {message.content ? (
          <Markdown components={MARKDOWN_COMPONENTS}>{message.content}</Markdown>
        ) : message.isStreaming ? (
          <span className="inline-flex items-center gap-1 py-1">
            <span className="h-1.5 w-1.5 rounded-full bg-muted-foreground animate-bounce [animation-delay:-0.3s]" />
            <span className="h-1.5 w-1.5 rounded-full bg-muted-foreground animate-bounce [animation-delay:-0.15s]" />
            <span className="h-1.5 w-1.5 rounded-full bg-muted-foreground animate-bounce" />
          </span>
        ) : null}
      </div>
    </div>
  )
}

function updateLast(messages, updater) {
  if (!messages.length) return messages
  const next = [...messages]
  next[next.length - 1] = updater(next[next.length - 1])
  return next
}

export default function ChatDrawer() {
  const [isOpen, setIsOpen] = useState(false)
  const [displayMessages, setDisplayMessages] = useState([])
  const [apiMessages, setApiMessages] = useState([])
  const [isStreaming, setIsStreaming] = useState(false)
  const [input, setInput] = useState('')

  const messagesEndRef = useRef(null)
  const textareaRef = useRef(null)
  const location = useLocation()

  // Reserve this slot so it's trivial to add /assistant exclusion later
  const hidden = location.pathname === '/assistant'

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [displayMessages])

  useEffect(() => {
    if (isOpen) textareaRef.current?.focus()
  }, [isOpen])

  const sendMessage = async (messageContent) => {
    const content = messageContent.trim()
    if (!content || isStreaming) return

    const updatedApiMessages = [...apiMessages, { role: 'user', content }]
    setApiMessages(updatedApiMessages)
    setDisplayMessages((prev) => [
      ...prev,
      { id: `u-${Date.now()}`, role: 'user', content },
      { id: `a-${Date.now()}`, role: 'assistant', content: '', toolIndicators: [], isStreaming: true },
    ])
    setInput('')
    setIsStreaming(true)

    let fullContent = ''

    try {
      const res = await fetch('/api/chat/message', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: updatedApiMessages, model: DEFAULT_MODEL }),
      })

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}))
        throw new Error(errData.detail || `Request failed (${res.status})`)
      }

      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      outer: while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })

        // SSE messages are separated by blank lines (\n\n or \r\n\r\n)
        const parts = buffer.split(/\r?\n\r?\n/)
        buffer = parts.pop() ?? ''

        for (const part of parts) {
          for (const line of part.split(/\r?\n/)) {
            if (!line.startsWith('data: ')) continue
            const raw = line.slice(6).trim()
            if (!raw) continue

            let event
            try {
              event = JSON.parse(raw)
            } catch {
              continue
            }

            if (event.type === 'text') {
              fullContent += event.content
              setDisplayMessages((prev) =>
                updateLast(prev, (m) => ({ ...m, content: m.content + event.content }))
              )
            } else if (event.type === 'tool_call') {
              setDisplayMessages((prev) =>
                updateLast(prev, (m) => ({
                  ...m,
                  toolIndicators: [
                    ...m.toolIndicators,
                    { id: `${event.tool}-${Date.now()}`, tool: event.tool, status: 'calling' },
                  ],
                }))
              )
            } else if (event.type === 'tool_result') {
              setDisplayMessages((prev) =>
                updateLast(prev, (m) => {
                  const indicators = [...m.toolIndicators]
                  // Mark the last 'calling' indicator for this tool as done
                  for (let i = indicators.length - 1; i >= 0; i--) {
                    if (indicators[i].tool === event.tool && indicators[i].status === 'calling') {
                      indicators[i] = { ...indicators[i], status: event.success ? 'done' : 'error' }
                      break
                    }
                  }
                  return { ...m, toolIndicators: indicators }
                })
              )
            } else if (event.type === 'error') {
              setDisplayMessages((prev) =>
                updateLast(prev, (m) => ({
                  ...m,
                  content: m.content || `Error: ${event.message}`,
                  isStreaming: false,
                }))
              )
              break outer
            } else if (event.type === 'done') {
              break outer
            }
          }
        }
      }
    } catch (err) {
      setDisplayMessages((prev) =>
        updateLast(prev, (m) => ({
          ...m,
          content: m.content || `Error: ${err.message}`,
          isStreaming: false,
        }))
      )
    } finally {
      setIsStreaming(false)
      if (fullContent) {
        setApiMessages((prev) => [...prev, { role: 'assistant', content: fullContent }])
      }
      // Ensure isStreaming flag is cleared on the last message
      setDisplayMessages((prev) => updateLast(prev, (m) => ({ ...m, isStreaming: false })))
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage(input)
    }
  }

  const handleTextareaInput = (e) => {
    e.target.style.height = 'auto'
    e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px'
  }

  if (hidden) return null

  return (
    <>
      {/* Floating trigger */}
      <button
        onClick={() => setIsOpen(true)}
        aria-label="Open Shoe Assistant"
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
          <span className="font-semibold text-foreground">Shoe Assistant</span>
          <button
            onClick={() => setIsOpen(false)}
            className="rounded-md p-1 text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
            aria-label="Close"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-4 py-3">
          {displayMessages.length === 0 ? (
            <div className="flex flex-col items-center gap-4 py-8 text-center">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-accent">
                <MessageCircle className="h-6 w-6 text-accent-foreground" />
              </div>
              <div>
                <p className="text-sm font-medium text-foreground">Shoe Assistant</p>
                <p className="mt-1 text-xs text-muted-foreground">
                  Ask about your shoes, find deals, or log a run
                </p>
              </div>
              <div className="mt-1 w-full space-y-2">
                {SUGGESTED_PROMPTS.map((prompt) => (
                  <button
                    key={prompt}
                    onClick={() => sendMessage(prompt)}
                    disabled={isStreaming}
                    className="w-full rounded-[10px] border border-border px-3 py-2 text-left text-sm text-muted-foreground transition-colors hover:border-primary/30 hover:bg-secondary hover:text-foreground disabled:pointer-events-none disabled:opacity-50"
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="space-y-3">
              {displayMessages.map((msg) =>
                msg.role === 'user' ? (
                  <UserMessage key={msg.id} content={msg.content} />
                ) : (
                  <AssistantMessage key={msg.id} message={msg} />
                )
              )}
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
              onClick={() => sendMessage(input)}
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
