import { clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

/** Merge conditional class names, resolving Tailwind conflicts. */
export function cn(...inputs) {
  return twMerge(clsx(inputs))
}

/** Format a number as CAD currency. Returns a dash for nullish values. */
export function formatCurrency(value) {
  if (value === null || value === undefined || Number.isNaN(value)) return '—'
  return new Intl.NumberFormat('en-CA', {
    style: 'currency',
    currency: 'CAD',
  }).format(value)
}

/** Format a percentage with no decimals (e.g. 23.7 -> "24%"). */
export function formatPercent(value) {
  if (value === null || value === undefined || Number.isNaN(value)) return '—'
  return `${Math.round(value)}%`
}

/** Format an ISO datetime into a short, human-friendly local string. */
export function formatDate(value, opts = {}) {
  if (!value) return '—'
  // A bare calendar date ("2026-07-02") is parsed by Date as UTC midnight,
  // which then renders as the previous day in western timezones. Treat those
  // as local dates so a run's date shows the day it actually happened.
  const date =
    typeof value === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(value)
      ? new Date(`${value}T00:00:00`)
      : new Date(value)
  if (Number.isNaN(date.getTime())) return '—'
  return date.toLocaleDateString('en-CA', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    ...opts,
  })
}

/**
 * Pick the best promo code for a price (highest effective discount) and return
 * { promo, finalPrice, saved } — or null if no promo applies.
 */
export function bestPromo(price, promos) {
  if (!price || !promos?.length) return null
  let best = null
  for (const promo of promos) {
    let final = price
    if (promo.discount_percent) final *= 1 - promo.discount_percent / 100
    if (promo.discount_amount) final -= promo.discount_amount
    final = Math.max(0, final)
    if (final < price && (!best || final < best.finalPrice)) {
      best = { promo, finalPrice: final, saved: price - final }
    }
  }
  return best
}

/** Format an ISO datetime as a relative "time ago" string. */
export function formatRelativeTime(value) {
  if (!value) return 'never'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return 'never'
  const seconds = Math.round((Date.now() - date.getTime()) / 1000)
  if (seconds < 60) return 'just now'
  const minutes = Math.round(seconds / 60)
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.round(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.round(hours / 24)
  if (days < 30) return `${days}d ago`
  return formatDate(value)
}
