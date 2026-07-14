# Anton — Domain Model

**Companion to:** `docs/architecture.md` (system view) and `docs/dependency_graph.md` (import view).
**Generated:** 2026-07-04, post-`canonical_activities` migration.
**Scope:** This document explains the *business domain* — what the entities mean, the rules that govern them, and who owns what. Implementation detail appears only where it encodes a domain decision.

---

## 1. Domain Overview

Anton serves one person — a competitive runner — and models two distinct concerns of that runner's life, plus the interfaces through which they're managed:

1. **Deal watching** — *"Which shoes do I want, and when should I buy them?"* A watchlist of shoe models, monitored across Canadian retailers, that surfaces genuine price opportunities and nothing else.
2. **Rotation & training** — *"What have I run, in what shoes, and what does that mean?"* A canonical history of every run, attribution of runs to owned shoes, the wear/retirement lifecycle of those shoes, and the training picture built on top (volume, personal bests, planned races).

The two subdomains are **deliberately independent**: wanting a shoe and owning a shoe are different facts with different lifecycles, and no hard link exists between them. They meet at exactly one seam — the *replacement deal* concept (§4.3) — which is a heuristic by design.

Cross-cutting the domains is the **assistant surface** (Son of Anton in-app; Claude Desktop externally via MCP), which is a *client* of the domain, never a second implementation of it: every fact the assistant reads and every change it makes flows through the same rules as the web UI.

**Actors:**
- **The runner** (the sole user) — the only human, the final authority on all ambiguous decisions.
- **Retailers** (8 storefronts) — external, unreliable sources of price truth.
- **The COROS watch** — source of new run data, arriving via sync.
- **The Strava archive** — a frozen, one-time historical record (8 years, ~700 runs), now fully absorbed.
- **LLM assistants** — actors that may read broadly but write only through sanctioned, confirmation-gated paths.

---

## 2. Core Entities

### 2.1 Deal-watching subdomain

| Entity | Meaning in the domain |
|---|---|
| **Tracked Shoe** (`shoes`) | A shoe *model* the runner wants — brand + model + an `msrp` ("what it lists for" — **the deal driver**: required for the shoe to produce deals) and an optional `target_price` ("what I'm willing to pay" — a personal threshold, not part of qualification since B9-v2). Deliberately **size-less**: interest is in the model across all sizes, so one out-of-stock size never hides a deal. Carries a `shoe_type` — the runner's own category vocabulary (e.g. `long_distance_racer`) that later powers the bridge to the rotation domain. |
| **Retailer** (`retailers`) | A store worth watching. Its `platform` describes *how it can be scraped* (shopify / algolia / custom) — a domain-relevant fact because it determines whether monitoring is even possible (two retailers are known-unscrapable). |
| **Price Observation** (`price_records`) | One sighting of a price: shoe × retailer × product URL × moment. **Append-only history** — observations are never edited or deleted; they are the evidence base for "best price ever seen" and price-trend judgments. Also carries incidental riches (image, colorway, sizes in stock). |
| **Deal** (`deals`) | A *qualified opportunity* — not merely a low price (see rule 4.1). Active deals are the product of the domain; everything else exists to produce and retire them honestly. |
| **Promo Code** (`promo_codes`) | A retailer-level discount code. Two provenances with different trust: `scraped` (machine-found, may churn) and `manual` (human-entered, protected — a scrape may never overwrite it). |

### 2.2 Rotation & training subdomain

| Entity | Meaning in the domain |
|---|---|
| **Activity** (`activities`) | **The canonical record of one physical activity.** Every run — whether it arrived from the Strava archive, a COROS sync, or a manual log — is exactly one Activity, discriminated by `source`. This is the domain's ground truth for "what happened": date, distance, time, pace (stored as seconds/km), heart rate, and for archive rows the full original record (`raw_json`). Non-run activities from the archive (rides, walks) also live here but sit outside the training feed. |
| **Attribution** (`shoe_runs`) | The answer to one question: *which owned shoe ran this activity?* At most one shoe per activity; an activity may also be unattributed (archive runs in shoes that predate the tracker). Attribution is a separate concept from the run itself — un-attributing a historical run doesn't erase the run. |
| **Owned Shoe** (`owned_shoes`) | A physical pair in the rotation, with a wear ledger: `starting_mileage` (km already on it when tracking began), `current_mileage` (a maintained counter), a self-set `mileage_limit`, and a `status` (`active` / `retired` / `for_sale`). Distinct from Tracked Shoe on purpose — see §5.1. |
| **Journal Note** (`shoe_notes`) | A timestamped observation about a shoe, permanently anchored to the mileage at which it was written ("felt dead at 412 km"). Either volunteered (`manual`) or prompted by a mileage checkpoint (`checkpoint`). The raw material for shoe reviews. |
| **Planned Race** (`planned_races`) | A goal: name, date, distance, target time, optionally the shoe planned for it. Countdown and required pace are always *derived* from today's date — never stored, so they can never go stale. Lifecycle: `planned → completed | skipped`, with actual result recorded on completion. |
| **Gear Mapping** (`strava_gear_mappings`) | Historical: the human-reviewed dictionary from Strava's free-text gear strings to owned shoes, built during the one-time import. Retained as the record of those decisions and for any future re-import. A NULL mapping is itself information: "recognized, and deliberately not mapped." |

### 2.3 Infrastructure

| Entity | Meaning |
|---|---|
| **App Setting** (`app_settings`) | Key/value odds-and-ends that are state, not domain (currently: when COROS last synced). |

---

## 3. Relationships

```
DEAL-WATCHING                                ROTATION & TRAINING
─────────────                                ───────────────────
Retailer 1──* PromoCode                      OwnedShoe 1──* Attribution *──1 Activity
Retailer 1──* PriceObservation                        │            (activity_id UNIQUE:
Shoe     1──* PriceObservation                        │             one shoe per run, max)
Shoe     1──* Deal *──1 Retailer             OwnedShoe 1──* JournalNote
                                             OwnedShoe 0..1──* PlannedRace (planned_shoe)
                                             OwnedShoe 0..1──* GearMapping

           Shoe ~~~~~~ shoe_type string ~~~~~~ OwnedShoe
           (the only cross-domain connection: a matching
            category label, not a foreign key — §4.3)
```

Cardinality facts that carry business meaning:

- **Activity → Attribution is 1 → 0..1.** A run happened whether or not a shoe is credited with it. Unattributed activities are first-class (they count in training volume; they simply don't add shoe wear).
- **Attribution → Activity is unique.** A run cannot wear two shoes. (Doubles like swapping shoes mid-run are out of scope by decision.)
- **Deal is per (shoe × retailer × product URL).** The same model on sale at two stores is two deals; two colorway URLs at one store are two deals.
- **Price observations never aggregate away.** "Best ever" and "last seen" are computed over the full observation history, per retailer.
- **Tracked Shoe ↔ Owned Shoe: no relationship.** See §5.1 — this absence is a load-bearing design decision, not an omission.

---

## 4. Business Rules

The rules below are the domain's constitution. Each is enforced in exactly one place in code (see Ownership, §5).

### 4.1 Deal qualification — *"a deal is any price below list"* (B9-v2, 2026-07-06)
A Deal exists **iff** the scraped price is **strictly below the shoe's MSRP** (`price < msrp`). Savings are measured against MSRP: `savings = msrp − price`.

Corollaries: a shoe **without an MSRP cannot produce deals** — there is nothing to measure against; the retailer's own compare-at/"original" price is **no longer consulted** for qualification (it survives on the price record as an observation). MSRP is read fresh at every evaluation, so editing it immediately changes what qualifies and re-scores savings. `target_price` is an **optional personal threshold** — a note-to-self, not part of qualification or savings.

*Historical note:* until 2026-07-06 the rule was "genuinely discounting (`original_price > price`) AND ≤ current target price." See design_decisions B9 (superseded) → B9-v2 and the changelog entry of that date.

### 4.2 Deal retirement — *"deals die honestly"*
Two mechanisms, both automatic:
- **Requalification failure**: a re-observed URL whose price no longer qualifies deactivates that deal.
- **Orphaning**: a URL that stops appearing in a *successful, non-empty* search is retired — catching renamed/delisted products. The non-empty guard means a transient scrape failure can never mass-extinguish deals.
Deactivated deals are kept as history, not deleted.

### 4.3 The replacement-deal bridge — *"the only place the domains touch"*
An owned shoe nearing retirement gets a hint: the count of active deals on tracked shoes of the **same `shoe_type`**. This is a *category-label match, explicitly heuristic* — the domains stay independent, and the bridge degrades silently (a typo'd type simply yields zero hints). The `shoe_type` vocabulary is therefore the single most load-bearing set of strings in the system.

The value set — **backend-owned since R2.4 (2026-07-08)**: the single source is `app/utils/shoe_types.py` (`SHOE_TYPES`), served at `GET /api/shoe-types` and validated on the write schemas (an off-vocabulary value is now a **422**, not a silent typo). The frontend no longer keeps a copy — `lib/shoeTypes.js` holds only presentation (badge colours + a title-case label formatter). A one-time migration (`c9d0e1f2a3b4`) normalized nine legacy `owned_shoes` free-text values to this vocabulary. The current values:

| Value | Meaning |
|---|---|
| `daily_trainer` | Everyday easy-mileage shoe — the rotation's workhorse. |
| `tempo` | Uptempo / threshold-workout shoe. |
| `intervals` | Track and interval-session shoe. |
| `long_run` | Cushioned shoe for the weekly long run. |
| `recovery` | Max-cushion shoe for recovery days. |
| `trail` | Off-road / trail shoe. |
| `long_distance_racer` | Race-day shoe for marathon / half-marathon (carbon-plate class). |
| `short_distance_racer` | Race-day shoe for 5K–10K. |

### 4.4 Catalog hygiene
- **Kids/junior products are filtered at the source** — they never enter observations or deals, for every retailer uniformly.
- **Manual promo codes outrank scraped ones**: human knowledge is never overwritten by a crawl.

### 4.5 The mileage ledger — *"the counter is the truth the runner sees"*
`current_mileage = starting_mileage + Σ(distance of attributed activities)`. This identity is maintained, not recomputed: every attribution write increments the counter; every attribution removal decrements it (floored at 0). The Phase-5 storage restructure was executed under an explicit *"counters untouched"* guarantee — displayed totals are a promise to the user.

### 4.6 One write path for runs
Every run enters the system — regardless of origin — through the single sanctioned operation (`rotation.log_run`): create the canonical Activity, create its Attribution, update the ledger, detect checkpoints. There is no second way to log a run. This is the domain's strongest integrity guarantee.

### 4.7 Deduplication — *"never count a run twice"*
- Strava: `strava_activity_id` is globally unique — re-importing an export updates in place, never duplicates.
- COROS: primary key is `coros_activity_id`; fallback is *same date + distance within 0.1 km* (catching runs hand-logged before sync existed). Confirming an already-logged run is a silent no-op (idempotent).

### 4.8 The frozen archive — *"history is not editable"*
Activities with `source='strava'` are the immutable historical record. Deleting a run attribution normally deletes the underlying activity too — **except** for archive rows, where only the attribution is removed and the run itself survives. The 8-year history can be re-attributed but never destroyed through normal operations.

### 4.9 Human confirmation gates all synced writes
No externally-sourced run is ever auto-logged. The COROS flow (both the server path and the Claude Desktop agent protocol) must *present suggested shoe assignments and wait for explicit confirmation* before writing. Shoe suggestions rank by pace first, distance second, active shoes only, lower mileage breaking ties — but suggestions are advice, not decisions.

### 4.10 Wear milestones
- **Checkpoints**: every 100 km crossing flags a moment to journal ("how does it feel at 300?"). The prompt is an invitation, shown once; the note is optional.
- **Retirement pipeline**: an active shoe at ≥ 75% of its mileage limit enters the attention list, worst first — the shared definition behind both Home alerts and the Shoes page, so they cannot disagree. Advisory nudges also fire at 600/700/800 km absolute.
- Retirement is a **status change, never a deletion**: a retired shoe keeps its full run, note, and cost history. (`for_sale` is a parallel terminal status.) Deleting an owned shoe outright destroys its attributions and is treated as a destructive last resort.

### 4.11 Derived numbers are never stored
Cost-per-km, lifetime pace, retirement percentage, race countdowns, required race pace, weekly volume — all computed from primitives at read time, server-side, identically for every client. The two exceptions are deliberate: the mileage counter (§4.5, a ledger with an invariant) and the deal's qualifying-savings snapshot (MSRP-based since B9-v2; the deal's `target_price` column survives as a nullable reference only, refreshed on change).

### 4.12 Training semantics
- **Personal bests are whole-activity bests** within distance bands (fastest average pace for a run of ~5 km, ~10 km, …) — *not* segment PBs, and the domain insists this never be misrepresented.
- **Weekly/monthly pace is distance-weighted** (total distance over total moving time), not an average of averages.
- Pace below 0.5 km of distance is meaningless and left null rather than computed.
- **America/Toronto is the calendar**: a run's date is its local date, and getting this wrong is known to shift 145 historical evening runs across day boundaries.

---

## 5. Ownership Boundaries

Who is allowed to change what — the domain's permission structure:

### 5.1 Wanting ≠ owning
`Shoe` (watchlist) and `OwnedShoe` (rotation) are separate entities with no link, because the facts have independent lifecycles: you can want a shoe you'll never buy, own a shoe you never tracked, and buy a tracked shoe without the systems needing to reconcile. Purchases are not modeled as a transition between them — buying a deal and adding an owned shoe are two unrelated acts. Any future linkage must respect that independence (the roadmap's answer is the shared `shoe_type` vocabulary, not a foreign key).

### 5.2 Write authority per aggregate
| Aggregate | Sole writer | Everyone else |
|---|---|---|
| Price observations, deals, promo codes | The scrape pipeline's persistence layer (`DealStore`) applying rules 4.1–4.4 | Read-only. The UI may *deactivate* a deal and edit targets/watchlist entries; nobody else fabricates deals. |
| Activities + attributions + mileage ledger | The single run write path (rule 4.6) and its inverse | Read-only. MCP tools, REST, COROS confirm are all callers of the same operation, never parallel implementations. |
| Journal notes | The note operation (which stamps `mileage_at_note` server-side — callers may not supply it) | Read-only. |
| Planned races | Race CRUD (derivations attached at read) | Read-only. |
| Owned-shoe lifecycle (status, limits) | Direct CRUD by the runner | Automated actors may *recommend* retirement, never enact it. |

### 5.3 The assistant is a client, not an authority
LLM surfaces (Son of Anton, Claude Desktop) operate under the same rules as any UI: they read through the same feeds, write through the same gated operations, and are bound by rule 4.9's confirmation protocol. The `sync_coros_runs` agent script encodes "present, wait, then log" as instructions precisely because the assistant has no bypass. The one assistant-specific capability — drafting a shoe review — is generative, built *from* journal notes, and produces text for the human, not database writes.

### 5.4 The scraper never crosses domains
The scrape pipeline reads the watchlist and writes the deal-watching aggregate. It has no knowledge of owned shoes, runs, or training — the rotation domain is invisible to it, and vice versa.

### 5.5 The runner is the tiebreaker
Every ambiguity in the domain resolves to the human: ambiguous gear mappings were left for review rather than fuzzy-matched; ±1-day near-matches during the historical import were flagged, never auto-linked; synced runs wait for confirmation; retirement is advised, not automated. Anton's automation posture is *prepare and propose; the runner disposes*.

---

## 6. Data Lifecycle

### Deal-watching
```
Tracked Shoe:   added (UI/seed) → active (monitored) ⇄ deactivated → deleted
                                                        (deletion cascades its observations/deals — history dies with the interest)
Price Obs.:     appended at each scrape → permanent (never edited/deleted while the shoe lives)
Deal:           detected (rules 4.1) → refreshed (price/target/image changes) → deactivated (4.2) → kept as history
Promo Code:     scraped: appears/updates/churns freely   manual: persists until the human removes it
Retailer:       added (platform auto-detected) → active ⇄ scraping-disabled; last_scraped_at heartbeats
```

### Rotation & training
```
Activity:       born via  (a) one-time archive import [frozen thereafter — rule 4.8]
                          (b) COROS sync + confirmation
                          (c) manual log
                → permanent. Deleted only when a non-archive run's attribution is deleted.
Attribution:    created with the activity (or minted onto an archive run) → deleted on un-log,
                reversing its mileage contribution (4.5)
Owned Shoe:     acquired (starting_mileage honors pre-tracking wear) → active
                → [≥75% limit] retirement pipeline (attention state, not a status)
                → retired | for_sale  (terminal but fully preserved)
                → deletion = destructive exception, not a lifecycle stage
Journal Note:   appended (manual or checkpoint-prompted) → permanent, mileage-anchored
Planned Race:   planned → completed (result recorded) | skipped   — derived countdowns never persist
Gear Mapping:   built once during import (human-reviewed) → dormant reference
```

### Assistant context
```
Chat conversation:  lives in the runner's browser only (localStorage, capped at 50) —
                    currently outside the platform's custody; a known boundary decision
                    slated for revisit (architecture.md §16.7)
```

The asymmetry is deliberate and worth stating: **the deal domain forgets on command** (delete a tracked shoe, its history goes), while **the training domain is engineered never to forget** (append-only notes, frozen archive, retirement-not-deletion, ledger reversibility). One records shopping interest; the other records a runner's life.

---

## 7. Naming Conventions

### 7.1 The vocabulary (glossary)
| Term | Precise meaning | Beware |
|---|---|---|
| **shoe** | Ambiguous alone — always qualify. **Tracked shoe** = watchlist entry (`shoes`); **owned shoe** = physical pair (`owned_shoes`). | The single most common source of confusion in the domain. |
| **activity** | A canonical physical activity (`activities`), any type, any source. | Not everything in `activities` is a run; the training feed filters to `activity_type == "Run"`. |
| **run** | Colloquially, a running activity. | Post-Phase-5, "a run" is an Activity; a **shoe run** (`shoe_runs`) is only the *attribution* of one to a shoe. Legacy names keep the old word — read them as "attribution." |
| **attribution** | The shoe-credit link for an activity. | |
| **source** | Where a run came from: `strava` (frozen archive) \| `coros` (watch sync) \| `manual`. | Drives the archive-preservation rule (4.8). |
| **watchlist** | The set of tracked shoes, as presented with best/last prices. | |
| **rotation** | The set of active owned shoes. | Also the name of the service that owns the whole subdomain's rules. |
| **deal** | A *qualified* opportunity per rule 4.1 (`price < msrp`) — never merely "a price." | Savings are measured against MSRP, not the retailer's markdown. |
| **msrp** | The shoe's list price — **the deal driver** (4.1). Required for a shoe to produce deals; read fresh at every evaluation. | |
| **target price** | The runner's optional willingness-to-pay note — a personal threshold, **not part of qualification or savings** since B9-v2 (2026-07-06). | Pre-B9-v2 text describing it as the deal driver is historical. |
| **checkpoint** | A 100 km wear milestone inviting a journal note. | |
| **retirement pipeline** | Attention state for shoes ≥ 75% of mileage limit. Not a status. | |
| **replacement deal** | Active deal on a tracked shoe whose `shoe_type` matches an owned shoe's — the heuristic bridge (4.3). | |
| **shoe_type** | The runner's category vocabulary — the cross-domain join key. **Backend-owned since R2.4** (`app/utils/shoe_types.py`, served at `GET /api/shoe-types`, validated on write); values enumerated in the §4.3 table. | Was free strings in four unvalidated copies (tech_debt P1-5, the `shoe_type` half now resolved); still treat vocabulary edits as schema-grade — both domains must agree. Owned-shoe `status` remains unvalidated (M2). |
| **personal best** | Whole-activity best within a distance band (4.12). | Never present as a segment PB. |
| **Anton** | The platform. **Son of Anton** — the embedded assistant. | In-code strings now say "Anton" (R1, 2026-07-14); the **repo name, folder path, and DB filename** still carry "running-shoe-deals" (retained pending R2/R3 — E6). |

### 7.2 Conventions in the schema and code
- **Units in names**: `distance_km`, `moving_time_s`, `avg_pace_s_per_km`, `elevation_gain_m`, `mileage_at_note` — a value's unit is in its name; unlabeled numbers are a smell.
- **Pace**: persisted as integer seconds-per-km; rendered as `"M:SS/km"` strings only at presentation boundaries. Any string pace in storage is legacy.
- **Timestamps**: `*_at` for moments (`created_at`, `detected_at`, `last_scraped_at`); `run_date` / `race_date` for calendar dates (local, America/Toronto). UTC and local are stored under explicit names (`started_at_utc`, `started_at_local`), never implied.
- **Status enums as lowercase strings**: `active | retired | for_sale`; `planned | completed | skipped`; `manual | checkpoint`; `scraped | manual`. Small closed sets, one owner each.
- **External identity**: `<system>_activity_id` columns are the idempotency keys for their systems; uniqueness on them *is* the dedup rule.
- **Tables**: plural snake_case; join/attribution tables named for their historical role (`shoe_runs`) rather than renamed mid-flight — continuity of meaning beats naming purity here, by explicit decision.
- **Section references**: comments citing `§N` point at the planning documents in the repo root; `P3.4`-style tags point at redesign-plan items. These are part of the project's citation system, not noise.

---

*Maintenance note: update this document when a business rule in §4 changes, when a new entity or status value is introduced, or when the `shoe_type` vocabulary is formalized. The rules here should always be checkable against `rotation.py`, the scrape orchestrator, and the migration history — if a rule can't be pointed at its single owner in code, either the code or this document is wrong.*
