import { useState } from 'react'
import { Check, Copy, Tag } from 'lucide-react'
import { cn } from '@/lib/utils'

/**
 * Displays a promo code as a copyable pill. Click to copy the code.
 * `compact` renders just the code chip without the description.
 */
export default function PromoBadge({ promo, compact = false, className }) {
  const [copied, setCopied] = useState(false)

  const copy = async (e) => {
    e.stopPropagation()
    e.preventDefault()
    try {
      await navigator.clipboard.writeText(promo.code)
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    } catch {
      /* clipboard unavailable — no-op */
    }
  }

  return (
    <div className={cn('flex flex-wrap items-center gap-2', className)}>
      <button
        type="button"
        onClick={copy}
        title="Copy code"
        className="inline-flex items-center gap-1.5 rounded-md border border-dashed border-success/50 bg-success/10 px-2 py-1 font-mono text-xs font-semibold text-success transition-colors hover:bg-success/20"
      >
        <Tag className="h-3.5 w-3.5" />
        {promo.code}
        {copied ? (
          <Check className="h-3.5 w-3.5" />
        ) : (
          <Copy className="h-3.5 w-3.5 opacity-60" />
        )}
      </button>
      {!compact && promo.description && (
        <span className="text-xs text-muted-foreground">
          {promo.description}
        </span>
      )}
    </div>
  )
}
