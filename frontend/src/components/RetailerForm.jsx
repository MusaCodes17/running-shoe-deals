import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { DialogFooter } from '@/components/ui/dialog'

const empty = {
  name: '',
  base_url: '',
  is_active: true,
  scraping_enabled: true,
}

/** Controlled form for creating/editing a retailer. */
export default function RetailerForm({ initial, onSubmit, onCancel, submitting }) {
  const [values, setValues] = useState(() => ({
    ...empty,
    ...(initial
      ? {
          name: initial.name ?? '',
          base_url: initial.base_url ?? '',
          is_active: initial.is_active ?? true,
          scraping_enabled: initial.scraping_enabled ?? true,
        }
      : {}),
  }))
  const [errors, setErrors] = useState({})

  const set = (key) => (e) =>
    setValues((v) => ({ ...v, [key]: e.target.value }))

  const validate = () => {
    const next = {}
    if (!values.name.trim()) next.name = 'Name is required'
    const url = values.base_url.trim()
    if (!url) next.base_url = 'Base URL is required'
    else if (!/^https?:\/\/.+/i.test(url))
      next.base_url = 'Must start with http:// or https://'
    setErrors(next)
    return Object.keys(next).length === 0
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!validate()) return
    onSubmit({
      name: values.name.trim(),
      base_url: values.base_url.trim(),
      is_active: values.is_active,
      scraping_enabled: values.scraping_enabled,
    })
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-1.5">
        <Label>Name</Label>
        <Input
          value={values.name}
          onChange={set('name')}
          placeholder="The Last Hunt"
        />
        {errors.name && <p className="text-xs text-destructive">{errors.name}</p>}
      </div>

      <div className="space-y-1.5">
        <Label>Base URL</Label>
        <Input
          value={values.base_url}
          onChange={set('base_url')}
          placeholder="https://www.thelasthunt.com"
        />
        {errors.base_url && (
          <p className="text-xs text-destructive">{errors.base_url}</p>
        )}
      </div>

      <div className="flex items-center justify-between rounded-md border p-3">
        <div>
          <Label className="text-sm font-medium">Active</Label>
          <p className="text-xs text-muted-foreground">
            Include this retailer in the app.
          </p>
        </div>
        <Switch
          checked={values.is_active}
          onCheckedChange={(checked) =>
            setValues((v) => ({ ...v, is_active: checked }))
          }
        />
      </div>

      <div className="flex items-center justify-between rounded-md border p-3">
        <div>
          <Label className="text-sm font-medium">Scraping enabled</Label>
          <p className="text-xs text-muted-foreground">
            Scrape this retailer for prices and promo codes.
          </p>
        </div>
        <Switch
          checked={values.scraping_enabled}
          onCheckedChange={(checked) =>
            setValues((v) => ({ ...v, scraping_enabled: checked }))
          }
        />
      </div>

      <DialogFooter>
        <Button type="button" variant="outline" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit" disabled={submitting}>
          {submitting ? 'Saving…' : initial ? 'Save changes' : 'Add retailer'}
        </Button>
      </DialogFooter>
    </form>
  )
}
