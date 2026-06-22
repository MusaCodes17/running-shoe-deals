import { ExternalLink, Store, Footprints } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import PromoBadge from '@/components/PromoBadge'
import {
  formatCurrency,
  formatPercent,
  formatRelativeTime,
  bestPromo,
} from '@/lib/utils'

/**
 * Renders a single deal. Works with both the rich DealResponse shape
 * (shoe object + retailer object) and the flattened dashboard shape
 * (retailer as a string).
 */
export default function DealCard({ deal, onClick }) {
  const shoe = deal.shoe || {}
  const retailerObj =
    deal.retailer && typeof deal.retailer === 'object' ? deal.retailer : null
  const retailerName =
    typeof deal.retailer === 'string' ? deal.retailer : retailerObj?.name
  const savings = deal.savings_percent
  // Best applicable discount code for this retailer (if the full object is present).
  const promo = bestPromo(deal.current_price, retailerObj?.active_promo_codes)

  return (
    <Card
      className="group cursor-pointer transition-shadow hover:shadow-md"
      onClick={onClick}
    >
      <CardContent className="space-y-3 p-5">
        <div className="relative -mx-5 -mt-5 mb-1 h-32 overflow-hidden bg-muted">
          {deal.image_url ? (
            <img
              src={deal.image_url}
              alt={`${shoe.brand} ${shoe.model}${deal.colorway ? ` — ${deal.colorway}` : ''}`}
              loading="lazy"
              className="h-full w-full object-contain"
            />
          ) : (
            <div className="flex h-full w-full items-center justify-center text-muted-foreground">
              <Footprints className="h-8 w-8" />
            </div>
          )}
        </div>
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0">
            <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
              {shoe.brand}
            </p>
            <h3 className="truncate font-semibold leading-tight">{shoe.model}</h3>
            {deal.colorway && (
              <p className="truncate text-xs text-muted-foreground">{deal.colorway}</p>
            )}
          </div>
          {savings != null && (
            <Badge variant={savings >= 30 ? 'success' : 'secondary'}>
              -{formatPercent(savings)}
            </Badge>
          )}
        </div>

        <div className="flex items-end justify-between">
          <div>
            <p className="text-2xl font-bold">
              {formatCurrency(deal.current_price)}
            </p>
            {deal.target_price != null && (
              <p className="text-xs text-muted-foreground">
                Target {formatCurrency(deal.target_price)}
              </p>
            )}
          </div>
          {deal.in_stock === false ? (
            <Badge variant="outline" className="text-muted-foreground">
              Out of stock
            </Badge>
          ) : (
            <Badge variant="outline" className="border-success/40 text-success">
              In stock
            </Badge>
          )}
        </div>

        {/* Applicable discount code + effective price after the code */}
        {promo && (
          <div className="space-y-1.5 rounded-md bg-success/5 p-2.5">
            <PromoBadge promo={{ ...promo.promo, description: null }} compact />
            <p className="text-xs text-muted-foreground">
              {formatCurrency(promo.finalPrice)} after code
              <span className="font-medium text-success">
                {' '}
                (save {formatCurrency(promo.saved)} more)
              </span>
            </p>
          </div>
        )}

        <div className="flex items-center justify-between border-t pt-3 text-xs text-muted-foreground">
          <span className="flex items-center gap-1">
            <Store className="h-3.5 w-3.5" />
            {retailerName || 'Unknown retailer'}
          </span>
          <span>{formatRelativeTime(deal.detected_at)}</span>
        </div>

        {deal.product_url && (
          <Button
            variant="outline"
            size="sm"
            className="w-full"
            asChild
            onClick={(e) => e.stopPropagation()}
          >
            <a href={deal.product_url} target="_blank" rel="noreferrer">
              View at retailer <ExternalLink className="h-3.5 w-3.5" />
            </a>
          </Button>
        )}
      </CardContent>
    </Card>
  )
}
