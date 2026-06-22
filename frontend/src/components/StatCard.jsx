import { Card, CardContent } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { cn } from '@/lib/utils'

/** Compact metric tile for the dashboard. */
export default function StatCard({ label, value, icon: Icon, hint, loading, accent }) {
  return (
    <Card>
      <CardContent className="flex items-center gap-4 p-5">
        {Icon && (
          <div
            className={cn(
              'flex h-11 w-11 shrink-0 items-center justify-center rounded-lg',
              accent || 'bg-primary/10 text-primary'
            )}
          >
            <Icon className="h-5 w-5" />
          </div>
        )}
        <div className="min-w-0">
          <p className="text-sm text-muted-foreground">{label}</p>
          {loading ? (
            <Skeleton className="mt-1 h-7 w-16" />
          ) : (
            <p className="truncate text-2xl font-bold">{value}</p>
          )}
          {hint && !loading && (
            <p className="text-xs text-muted-foreground">{hint}</p>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
