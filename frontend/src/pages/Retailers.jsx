import { useState } from 'react'
import { Store, ExternalLink, Plus, Pencil, Trash2, Tag } from 'lucide-react'
import PageHeader from '@/components/PageHeader'
import RetailerForm from '@/components/RetailerForm'
import PromoBadge from '@/components/PromoBadge'
import PromoManagerDialog from '@/components/PromoManagerDialog'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Switch } from '@/components/ui/switch'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog'
import { ErrorState, EmptyState, CardSkeletonGrid } from '@/components/StatusViews'
import { useToast } from '@/components/ui/toast'
import {
  useRetailers,
  useCreateRetailer,
  useUpdateRetailer,
  useDeleteRetailer,
} from '@/hooks/useApi'
import { formatRelativeTime } from '@/lib/utils'

export default function Retailers() {
  const retailers = useRetailers()
  const create = useCreateRetailer()
  const update = useUpdateRetailer()
  const remove = useDeleteRetailer()
  const { toast } = useToast()

  const [formState, setFormState] = useState(null) // null | { retailer?: r }
  const [deleting, setDeleting] = useState(null)
  const [promosFor, setPromosFor] = useState(null)

  const toggleScraping = (retailer, enabled) => {
    update.mutate(
      { id: retailer.id, data: { scraping_enabled: enabled } },
      {
        onSuccess: () =>
          toast({
            variant: 'success',
            title: enabled ? 'Scraping enabled' : 'Scraping disabled',
            description: retailer.name,
          }),
        onError: (err) =>
          toast({ variant: 'destructive', title: 'Update failed', description: err.message }),
      }
    )
  }

  const handleSubmit = (payload) => {
    const editing = formState?.retailer
    const mutation = editing ? update : create
    const args = editing ? { id: editing.id, data: payload } : payload
    mutation.mutate(args, {
      onSuccess: () => {
        toast({
          variant: 'success',
          title: editing ? 'Retailer updated' : 'Retailer added',
        })
        setFormState(null)
      },
      onError: (err) =>
        toast({ variant: 'destructive', title: 'Save failed', description: err.message }),
    })
  }

  const confirmDelete = () => {
    remove.mutate(deleting.id, {
      onSuccess: () => {
        toast({ variant: 'success', title: 'Retailer deleted' })
        setDeleting(null)
      },
      onError: (err) =>
        toast({ variant: 'destructive', title: 'Delete failed', description: err.message }),
    })
  }

  // Keep the open promo dialog's data fresh as the retailers query refetches.
  const promoRetailer =
    promosFor && (retailers.data || []).find((r) => r.id === promosFor.id)

  return (
    <div className="space-y-6">
      <PageHeader
        title="Retailers"
        description="Sources scraped for deals and discount codes."
      >
        <Button onClick={() => setFormState({})}>
          <Plus className="h-4 w-4" /> Add retailer
        </Button>
      </PageHeader>

      {retailers.isLoading ? (
        <CardSkeletonGrid count={6} />
      ) : retailers.isError ? (
        <ErrorState error={retailers.error} onRetry={retailers.refetch} />
      ) : retailers.data?.length ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {retailers.data.map((retailer) => {
            const promos = retailer.active_promo_codes || []
            return (
              <Card key={retailer.id} className="flex flex-col">
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10 text-primary">
                        <Store className="h-4 w-4" />
                      </div>
                      <CardTitle className="text-base">{retailer.name}</CardTitle>
                    </div>
                    {retailer.is_active ? (
                      <Badge variant="success">Active</Badge>
                    ) : (
                      <Badge variant="secondary">Inactive</Badge>
                    )}
                  </div>
                </CardHeader>
                <CardContent className="flex flex-1 flex-col gap-4">
                  {retailer.base_url && (
                    <a
                      href={retailer.base_url}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center gap-1 truncate text-sm text-muted-foreground hover:text-primary"
                    >
                      {retailer.base_url.replace(/^https?:\/\//, '')}
                      <ExternalLink className="h-3.5 w-3.5 shrink-0" />
                    </a>
                  )}

                  {/* Discount codes */}
                  <div className="space-y-2">
                    <div className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground">
                      <Tag className="h-3.5 w-3.5" />
                      Discount codes
                    </div>
                    {promos.length ? (
                      <div className="space-y-1.5">
                        {promos.slice(0, 2).map((promo) => (
                          <PromoBadge key={promo.id} promo={promo} />
                        ))}
                        {promos.length > 2 && (
                          <p className="text-xs text-muted-foreground">
                            +{promos.length - 2} more
                          </p>
                        )}
                      </div>
                    ) : (
                      <p className="text-xs text-muted-foreground">
                        None yet — detect or add in Manage codes.
                      </p>
                    )}
                  </div>

                  <div className="text-xs text-muted-foreground">
                    Last scraped: {formatRelativeTime(retailer.last_scraped_at)}
                  </div>

                  <div className="flex items-center justify-between rounded-md border p-3">
                    <Label
                      htmlFor={`scrape-${retailer.id}`}
                      className="text-sm font-medium"
                    >
                      Scraping enabled
                    </Label>
                    <Switch
                      id={`scrape-${retailer.id}`}
                      checked={retailer.scraping_enabled}
                      disabled={update.isPending}
                      onCheckedChange={(checked) => toggleScraping(retailer, checked)}
                    />
                  </div>

                  <div className="mt-auto flex flex-wrap gap-2 border-t pt-3">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setPromosFor(retailer)}
                    >
                      <Tag className="h-4 w-4" /> Manage codes
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      title="Edit"
                      onClick={() => setFormState({ retailer })}
                    >
                      <Pencil className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      title="Delete"
                      className="text-destructive hover:text-destructive"
                      onClick={() => setDeleting(retailer)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </div>
      ) : (
        <EmptyState
          icon={Store}
          title="No retailers yet"
          description="Add a retailer to start tracking prices and discount codes."
          action={
            <Button onClick={() => setFormState({})}>
              <Plus className="h-4 w-4" /> Add retailer
            </Button>
          }
        />
      )}

      {/* Create / edit dialog */}
      <Dialog open={!!formState} onOpenChange={(o) => !o && setFormState(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {formState?.retailer ? 'Edit retailer' : 'Add a retailer'}
            </DialogTitle>
            <DialogDescription>
              {formState?.retailer
                ? 'Update this retailer’s details.'
                : 'Add a new retailer to track. A matching scraper is required for automated scraping.'}
            </DialogDescription>
          </DialogHeader>
          {formState && (
            <RetailerForm
              initial={formState.retailer}
              submitting={create.isPending || update.isPending}
              onSubmit={handleSubmit}
              onCancel={() => setFormState(null)}
            />
          )}
        </DialogContent>
      </Dialog>

      {/* Promo manager */}
      <PromoManagerDialog
        retailer={promoRetailer}
        open={!!promosFor}
        onOpenChange={(o) => !o && setPromosFor(null)}
      />

      {/* Delete confirmation */}
      <Dialog open={!!deleting} onOpenChange={(o) => !o && setDeleting(null)}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Delete retailer?</DialogTitle>
            <DialogDescription>
              {deleting &&
                `This removes "${deleting.name}" along with its price records, deals, and codes. This cannot be undone.`}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleting(null)}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={confirmDelete}
              disabled={remove.isPending}
            >
              {remove.isPending ? 'Deleting…' : 'Delete'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
