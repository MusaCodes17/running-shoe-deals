// Run/activity source → Badge variant + label. Mirrors backend sources
// (coros | strava | manual) and the U1 variant map used on the shoe detail
// run history: coros → primary, strava → orange, manual → grey.
export const RUN_SOURCE_VARIANT = {
  coros: 'default',
  strava: 'strava',
  manual: 'secondary',
}

export const RUN_SOURCE_LABEL = {
  coros: 'COROS',
  strava: 'Strava',
  manual: 'Manual',
}

export const runSourceVariant = (source) => RUN_SOURCE_VARIANT[source] ?? 'secondary'
export const runSourceLabel = (source) => RUN_SOURCE_LABEL[source] ?? source
