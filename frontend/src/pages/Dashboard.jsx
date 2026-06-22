import { Link } from 'react-router-dom'
import {
  Footprints,
  Store,
  Tag,
  PiggyBank,
  Clock,
  ArrowRight,
} from 'lucide-react'
import PageHeader from '@/components/PageHeader'
import StatCard from '@/components/StatCard'
import DealCard from '@/components/DealCard'
import ScrapeButton from '@/components/ScrapeButton'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { ErrorState, EmptyState, CardSkeletonGrid } from '@/components/StatusViews'
import {
  useDashboardStats,
  useRecentDeals,
  useBestDeals,
} from '@/hooks/useApi'
import { formatCurrency, formatRelativeTime } from '@/lib/utils'

export default function Dashboard() {
  const stats = useDashboardStats()
  const recent = useRecentDeals(6)
  const best = useBestDeals(6)
  const s = stats.data

  return (
    <div className="space-y-8">
      <PageHeader
        title="Dashboard"
        description="Overview of tracked shoes, retailers, and the latest deals."
      >
        <ScrapeButton />
      </PageHeader>

      {stats.isError ? (
        <ErrorState error={stats.error} onRetry={stats.refetch} />
      ) : (
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          <StatCard
            label="Tracked shoes"
            value={s?.total_shoes ?? 0}
            hint={s ? `${s.active_shoes} active` : undefined}
            icon={Footprints}
            loading={stats.isLoading}
          />
          <StatCard
            label="Active deals"
            value={s?.active_deals ?? 0}
            icon={Tag}
            accent="bg-success/10 text-success"
            loading={stats.isLoading}
          />
          <StatCard
            label="Avg. savings"
            value={s?.average_savings != null ? formatCurrency(s.average_savings) : '—'}
            icon={PiggyBank}
            loading={stats.isLoading}
          />
          <StatCard
            label="Retailers"
            value={s?.total_retailers ?? 0}
            hint={s ? `${s.active_retailers} active` : undefined}
            icon={Store}
            loading={stats.isLoading}
          />
        </div>
      )}

      {/* Last scrape banner */}
      {s && (
        <Card>
          <CardContent className="flex flex-col items-start justify-between gap-3 p-5 sm:flex-row sm:items-center">
            <div className="flex items-center gap-3 text-sm">
              <Clock className="h-5 w-5 text-muted-foreground" />
              <div>
                <p className="font-medium">
                  Last scrape: {formatRelativeTime(s.last_scrape)}
                </p>
                <p className="text-muted-foreground">
                  {s.total_price_records} price records collected
                </p>
              </div>
            </div>
            <ScrapeButton variant="outline" />
          </CardContent>
        </Card>
      )}

      {/* Best deals */}
      <DealSection
        title="Best deals"
        query={best}
        to="/deals"
        emptyTitle="No deals yet"
        emptyDescription="Run a scrape to find deals on your tracked shoes."
      />

      {/* Recent deals */}
      <DealSection
        title="Recently detected"
        query={recent}
        to="/deals"
        emptyTitle="Nothing detected recently"
        emptyDescription="New deals will appear here after the next scrape."
      />
    </div>
  )
}

function DealSection({ title, query, to, emptyTitle, emptyDescription }) {
  return (
    <section className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">{title}</h2>
        <Button variant="ghost" size="sm" asChild>
          <Link to={to}>
            View all <ArrowRight className="h-4 w-4" />
          </Link>
        </Button>
      </div>

      {query.isLoading ? (
        <CardSkeletonGrid count={3} />
      ) : query.isError ? (
        <ErrorState error={query.error} onRetry={query.refetch} />
      ) : query.data?.length ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {query.data.map((deal) => (
            <DealCard key={deal.id} deal={deal} />
          ))}
        </div>
      ) : (
        <EmptyState
          icon={Tag}
          title={emptyTitle}
          description={emptyDescription}
        />
      )}
    </section>
  )
}
