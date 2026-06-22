import { CheckCircle2, AlertTriangle, XCircle, Loader2, HelpCircle } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

/**
 * Turns a /api/shoes/test response into a {status, foundCount, totalCount}
 * triple the badge (and the test modal) can render consistently.
 */
export function getShoeScrapabilityStatus(result) {
  if (!result) return { status: 'untested', foundCount: 0, totalCount: 0 }
  const foundCount = result.retailers_found ?? 0
  const totalCount = result.retailers_tested ?? result.results?.length ?? 0
  if (foundCount >= 2) return { status: 'found', foundCount, totalCount }
  if (foundCount === 1) return { status: 'limited', foundCount, totalCount }
  return { status: 'not_found', foundCount, totalCount }
}

const VARIANTS = {
  found: { variant: 'success', Icon: CheckCircle2, label: 'Found' },
  limited: { variant: 'warning', Icon: AlertTriangle, label: 'Limited' },
  not_found: { variant: 'destructive', Icon: XCircle, label: 'Not found' },
  error: { variant: 'destructive', Icon: XCircle, label: 'Error' },
  loading: { variant: 'secondary', Icon: Loader2, label: 'Checking…' },
  untested: { variant: 'outline', Icon: HelpCircle, label: 'Not tested' },
}

/**
 * Reusable status pill. Pass `status` ('found' | 'limited' | 'not_found' |
 * 'error' | 'loading' | 'untested') plus the retailer counts; clicking opens
 * the detailed breakdown via `onClick`.
 */
export default function ShoeStatusBadge({
  status = 'untested',
  foundCount = 0,
  totalCount = 0,
  onClick,
  className,
}) {
  const { variant, Icon, label } = VARIANTS[status] ?? VARIANTS.untested
  const showCount = status === 'found' || status === 'limited' || status === 'not_found'

  return (
    <Badge
      variant={variant}
      onClick={onClick}
      title={onClick ? 'Click for details' : undefined}
      className={cn(
        'gap-1',
        onClick && 'cursor-pointer hover:opacity-80',
        className
      )}
    >
      <Icon className={cn('h-3 w-3', status === 'loading' && 'animate-spin')} />
      {label}
      {showCount && ` ${foundCount}/${totalCount}`}
    </Badge>
  )
}
