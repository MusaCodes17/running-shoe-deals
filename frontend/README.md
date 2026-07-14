# Anton — Frontend

React + Vite dashboard for the Anton API (Phase 3).

## Stack

- **React 18** + **Vite 5**
- **Tailwind CSS** with shadcn/ui-style components (`src/components/ui`)
- **TanStack Query v5** for data fetching/caching (`src/hooks/useApi.js`)
- **React Router v6** for routing
- **Axios** API wrapper (`src/services/api.js`)
- **Recharts** for price-history charts
- **lucide-react** icons

## Getting started

The backend must be running on `http://localhost:8000` (see `../backend`).

```bash
npm install
npm run dev      # http://localhost:5173
```

In dev, Vite proxies `/api/*` to the backend (target `127.0.0.1:8000` — using
`127.0.0.1` rather than `localhost` avoids Node's IPv6 `::1` resolution, which
the IPv4-only backend refuses).

```bash
npm run build    # production bundle in dist/
npm run preview  # serve the built bundle
```

When serving the built bundle separately from the backend, set `VITE_API_URL`
to the backend origin (see `.env.example`).

## Structure

```
src/
  services/api.js     Axios client + typed endpoint helpers
  hooks/useApi.js     React Query hooks + mutation cache invalidation
  components/
    ui/               shadcn-style primitives (button, card, dialog, …)
    layout/Layout.jsx responsive sidebar + mobile nav
    DealCard, DealDetailModal, ShoeForm, PriceChart, StatCard, ScrapeButton
  pages/
    Dashboard.jsx     stats, last-scrape banner, best/recent deals, Scrape Now
    Deals.jsx         filters (brand/retailer/min savings), sort, detail modal
    Shoes.jsx         CRUD table, target price, price-history chart
    Retailers.jsx     list + per-retailer scraping toggle
```

## Pages

- **Dashboard** — totals, average savings, last scrape time, best & recent
  deals, and a **Scrape Now** button (`POST /api/scrape/all`).
- **Deals** — filter by brand, retailer, and minimum savings %; sort by
  savings/price/recency; click a card for a detail modal with price history.
- **Shoes** — add/edit/delete tracked shoes, set target price, view price
  history per shoe.
- **Retailers** — add/edit/delete retailers, enable/disable scraping, see last
  scrape time, and **manage discount codes** (auto-detect from the retailer's
  site or add manually).

## Extra features

- **Dark mode** — toggle in the sidebar/header, persisted to `localStorage`,
  with a no-flash init script in `index.html` (respects system preference).
- **Discount codes** — codes are auto-detected from each retailer's homepage
  during a scrape (heuristic match on "code"/"% off" text), stored per retailer,
  and can also be added manually. Deal cards and the deal detail modal show the
  best applicable code and the **effective price after the code**.

  Backend pieces: `PromoCode` model, `GET/POST /api/retailers/{id}/promos`,
  `DELETE /api/retailers/promos/{id}`, `POST /api/scrape/promos[/{retailer_id}]`,
  and `active_promo_codes` embedded in each retailer response.
