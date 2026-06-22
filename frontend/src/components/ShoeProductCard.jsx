import { useState } from 'react'
import { ExternalLink, Store, Footprints } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import PromoBadge from '@/components/PromoBadge'
import ColorwaySelector from '@/components/ColorwaySelector'
import { formatCurrency, formatPercent, bestPromo } from '@/lib/utils'

/**
 * One card per tracked shoe model. Consolidates every active deal for the model
 * (across colorways and retailers) into a single card with a large primary
 * image and a colorway/retailer selector. Selecting a colorway updates the
 * image, price, retailer, and buy link.
 *
 * Props: group = { shoeId, shoe: { brand, model }, deals: DealResponse[] }
 *        onViewDetails(deal) — optional, opens the detail modal.
 */
export default function ShoeProductCard({ group, onViewDetails }) {
  const { shoe, deals } = group
  // Deals arrive pre-sorted (best per the page's sort first), so default to the first.
  const [selectedId, setSelectedId] = useState(deals[0]?.id)
  const selected = deals.find((d) => d.id === selectedId) || deals[0]

  const retailerObj =
    selected.retailer && typeof selected.retailer === 'object' ? selected.retailer : null
  const retailerName =
    typeof selected.retailer === 'string' ? selected.retailer : retailerObj?.name
  const savings = selected.savings_percent
  const promo = bestPromo(selected.current_price, retailerObj?.active_promo_codes)

  return (
    <Card className="flex flex-col overflow-hidden">
      {/* Primary image */}
      <button
        type="button"
        onClick={() => onViewDetails?.(selected)}
        className="group relative block aspect-square w-full overflow-hidden bg-muted"
        title="View details"
      >
        {selected.image_url ? (
          <img
            src={selected.image_url}
            alt={`${shoe.brand} ${shoe.model}${selected.colorway ? ` — ${selected.colorway}` : ''}`}
            className="h-full w-full object-contain transition-transform group-hover:scale-105"
          />
        ) : (
          <div className="flex h-full w-full items-center justify-center text-muted-foreground">
            <Footprints className="h-12 w-12" />
          </div>
        )}
        {savings != null && (
          <Badge
            variant={savings >= 30 ? 'success' : 'secondary'}
            className="absolute right-2 top-2"
          >
            -{formatPercent(savings)}
          </Badge>
        )}
      </button>

      <CardContent className="flex flex-1 flex-col gap-3 p-4">
        <div className="min-w-0">
          <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
            {shoe.brand}
          </p>
          <h3 className="truncate font-semibold leading-tight">{shoe.model}</h3>
          {selected.colorway && (
            <p className="truncate text-xs text-muted-foreground">{selected.colorway}</p>
          )}
        </div>

        <div className="flex items-end justify-between">
          <div>
            <p className="text-2xl font-bold">{formatCurrency(selected.current_price)}</p>
            {selected.target_price != null && (
              <p className="text-xs text-muted-foreground">
                Target {formatCurrency(selected.target_price)}
              </p>
            )}
          </div>
          {selected.in_stock === false ? (
            <Badge variant="outline" className="text-muted-foreground">
              Out of stock
            </Badge>
          ) : (
            <Badge variant="outline" className="border-success/40 text-success">
              In stock
            </Badge>
          )}
        </div>

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

        {selected.sizes_available?.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {selected.sizes_available.map((s) => (
              <Badge key={s} variant="outline" className="text-xs">
                {s}
              </Badge>
            ))}
          </div>
        )}

        {/* Colorway / retailer options */}
        <ColorwaySelector
          options={deals}
          selectedId={selected.id}
          onSelect={setSelectedId}
        />

        <div className="mt-auto flex items-center gap-1 border-t pt-3 text-xs text-muted-foreground">
          <Store className="h-3.5 w-3.5" />
          {retailerName || 'Unknown retailer'}
          {deals.length > 1 && (
            <span className="ml-auto">{deals.length} options</span>
          )}
        </div>

        {selected.product_url && (
          <Button variant="outline" size="sm" className="w-full" asChild>
            <a href={selected.product_url} target="_blank" rel="noreferrer">
              View at retailer <ExternalLink className="h-3.5 w-3.5" />
            </a>
          </Button>
        )}
      </CardContent>
    </Card>
  )
}
