import { useState } from 'react'
import {
  Plus,
  Pencil,
  Trash2,
  LineChart as LineChartIcon,
  Footprints,
  Search,
  Download,
  FlaskConical,
} from 'lucide-react'
import PageHeader from '@/components/PageHeader'
import ShoeForm from '@/components/ShoeForm'
import PriceChart from '@/components/PriceChart'
import ScrapabilityTestModal from '@/components/ScrapabilityTestModal'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog'
import { ErrorState, EmptyState, RowSkeleton } from '@/components/StatusViews'
import { useToast } from '@/components/ui/toast'
import {
  useShoes,
  useShoePrices,
  useCreateShoe,
  useUpdateShoe,
  useDeleteShoe,
} from '@/hooks/useApi'
import { exportApi, shoesApi, scrapeApi } from '@/services/api'
import { formatCurrency } from '@/lib/utils'

export default function Shoes() {
  const [search, setSearch] = useState('')
  const [formState, setFormState] = useState(null) // null | { shoe?: shoe }
  const [deleting, setDeleting] = useState(null) // shoe pending delete
  const [historyShoe, setHistoryShoe] = useState(null)

  const shoes = useShoes()
  const create = useCreateShoe()
  const update = useUpdateShoe()
  const remove = useDeleteShoe()
  const { toast } = useToast()

  // On-demand "Test" button per row — never runs automatically, only when clicked.
  const [testShoe, setTestShoe] = useState(null) // shoe being tested from the list
  const [testState, setTestState] = useState(null) // { loading, error, result }

  const runTest = (shoe) => {
    setTestShoe(shoe)
    setTestState({ loading: true, error: null, result: null })
    shoesApi
      .testScrapability(shoe.brand, shoe.model)
      .then((result) => setTestState({ loading: false, error: null, result }))
      .catch((err) => setTestState({ loading: false, error: err.message, result: null }))
  }

  const filtered = (shoes.data || []).filter((s) => {
    const q = search.trim().toLowerCase()
    if (!q) return true
    return (
      s.brand.toLowerCase().includes(q) || s.model.toLowerCase().includes(q)
    )
  })

  const handleSubmit = (payload, opts = {}) => {
    const editing = formState?.shoe
    const mutation = editing ? update : create
    const args = editing ? { id: editing.id, data: payload } : payload
    mutation.mutate(args, {
      onSuccess: (savedShoe) => {
        toast({
          variant: 'success',
          title: editing ? 'Shoe updated' : 'Shoe added',
        })
        setFormState(null)
        if (opts.scrapeAfterSave) {
          scrapeApi
            .shoe(savedShoe.id)
            .then((res) =>
              toast({
                variant: 'success',
                title: 'Scrape complete',
                description: `${res.results?.deals_found ?? 0} deal(s) found.`,
              })
            )
            .catch((err) =>
              toast({ variant: 'destructive', title: 'Scrape failed', description: err.message })
            )
        }
      },
      onError: (err) =>
        toast({ variant: 'destructive', title: 'Save failed', description: err.message }),
    })
  }

  const [exporting, setExporting] = useState(false)
  const handleExport = async () => {
    setExporting(true)
    try {
      const source = await exportApi.seedData()
      const blob = new Blob([source], { type: 'text/x-python' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'seed_data.py'
      a.click()
      URL.revokeObjectURL(url)
      toast({ variant: 'success', title: 'Exported seed_data.py' })
    } catch (err) {
      toast({ variant: 'destructive', title: 'Export failed', description: err.message })
    } finally {
      setExporting(false)
    }
  }

  const confirmDelete = () => {
    remove.mutate(deleting.id, {
      onSuccess: () => {
        toast({ variant: 'success', title: 'Shoe deleted' })
        setDeleting(null)
      },
      onError: (err) =>
        toast({ variant: 'destructive', title: 'Delete failed', description: err.message }),
    })
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Shoes"
        description="Manage the shoes you want to track and their target prices."
      >
        <Button variant="outline" onClick={handleExport} disabled={exporting}>
          <Download className="h-4 w-4" /> {exporting ? 'Exporting…' : 'Export seed data'}
        </Button>
        <Button onClick={() => setFormState({})}>
          <Plus className="h-4 w-4" /> Add shoe
        </Button>
      </PageHeader>

      <div className="relative max-w-sm">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          className="pl-9"
          placeholder="Search by brand or model…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      {shoes.isLoading ? (
        <RowSkeleton count={6} />
      ) : shoes.isError ? (
        <ErrorState error={shoes.error} onRetry={shoes.refetch} />
      ) : filtered.length ? (
        <Card>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Brand</TableHead>
                  <TableHead>Model</TableHead>
                  <TableHead>Target</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filtered.map((shoe) => {
                  return (
                  <TableRow key={shoe.id}>
                    <TableCell className="font-medium">{shoe.brand}</TableCell>
                    <TableCell>{shoe.model}</TableCell>
                    <TableCell>{formatCurrency(shoe.target_price)}</TableCell>
                    <TableCell>
                      {shoe.is_active ? (
                        <Badge variant="success">Active</Badge>
                      ) : (
                        <Badge variant="secondary">Paused</Badge>
                      )}
                    </TableCell>
                    <TableCell>
                      <div className="flex justify-end gap-1">
                        <Button
                          variant="ghost"
                          size="icon"
                          title="Test scrapability"
                          onClick={() => runTest(shoe)}
                        >
                          <FlaskConical className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          title="Price history"
                          onClick={() => setHistoryShoe(shoe)}
                        >
                          <LineChartIcon className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          title="Edit"
                          onClick={() => setFormState({ shoe })}
                        >
                          <Pencil className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          title="Delete"
                          className="text-destructive hover:text-destructive"
                          onClick={() => setDeleting(shoe)}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                  )
                })}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      ) : (
        <EmptyState
          icon={Footprints}
          title={search ? 'No matching shoes' : 'No shoes tracked yet'}
          description={
            search
              ? 'Try a different search.'
              : 'Add a shoe to start tracking prices and deals.'
          }
          action={
            !search && (
              <Button onClick={() => setFormState({})}>
                <Plus className="h-4 w-4" /> Add shoe
              </Button>
            )
          }
        />
      )}

      {/* Create / edit dialog */}
      <Dialog open={!!formState} onOpenChange={(o) => !o && setFormState(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {formState?.shoe ? 'Edit shoe' : 'Add a shoe'}
            </DialogTitle>
            <DialogDescription>
              {formState?.shoe
                ? 'Update the details for this tracked shoe.'
                : 'Track a new shoe and set the price you want to pay.'}
            </DialogDescription>
          </DialogHeader>
          {formState && (
            <ShoeForm
              initial={formState.shoe}
              submitting={create.isPending || update.isPending}
              onSubmit={handleSubmit}
              onCancel={() => setFormState(null)}
            />
          )}
        </DialogContent>
      </Dialog>

      {/* Price history dialog */}
      <PriceHistoryDialog
        shoe={historyShoe}
        onOpenChange={(o) => !o && setHistoryShoe(null)}
      />

      {/* On-demand scrapability test dialog (opened via the row "Test" button) */}
      <ScrapabilityTestModal
        open={!!testShoe}
        onOpenChange={(o) => !o && setTestShoe(null)}
        shoeLabel={testShoe && `${testShoe.brand} ${testShoe.model}`}
        loading={!!testState?.loading}
        error={testState?.error}
        result={testState?.result}
        onRetest={() => testShoe && runTest(testShoe)}
      />

      {/* Delete confirmation */}
      <Dialog open={!!deleting} onOpenChange={(o) => !o && setDeleting(null)}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Delete shoe?</DialogTitle>
            <DialogDescription>
              {deleting && `This removes "${deleting.brand} ${deleting.model}" and its price history. This cannot be undone.`}
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

function PriceHistoryDialog({ shoe, onOpenChange }) {
  const prices = useShoePrices(shoe?.id)
  return (
    <Dialog open={!!shoe} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>
            Price history{shoe ? ` — ${shoe.brand} ${shoe.model}` : ''}
          </DialogTitle>
          <DialogDescription>
            {shoe && `Target ${formatCurrency(shoe.target_price)}`}
          </DialogDescription>
        </DialogHeader>
        {prices.isError ? (
          <ErrorState error={prices.error} onRetry={prices.refetch} />
        ) : prices.isLoading ? (
          <div className="h-[300px] animate-pulse rounded-md bg-muted" />
        ) : (
          <PriceChart records={prices.data} targetPrice={shoe?.target_price} />
        )}
      </DialogContent>
    </Dialog>
  )
}
