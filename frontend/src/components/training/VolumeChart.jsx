import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'

function VolumeTooltip({ active, payload }) {
  if (!active || !payload?.length) return null
  const d = payload[0].payload
  return (
    <div className="rounded-[10px] border border-border bg-popover px-3 py-2 text-xs tabular-nums">
      <div className="font-semibold text-foreground">{d.fullLabel}</div>
      <div className="text-muted-foreground">
        {d.total_km.toFixed(1)} km · {d.run_count} run{d.run_count === 1 ? '' : 's'}
      </div>
    </div>
  )
}

/**
 * Presentational volume bar chart (km per period). Data is expected already
 * chronological with { label, fullLabel, total_km, run_count }. Kept legible
 * at ~340px: ≤12 bars, abbreviated x labels, no fixed pixel widths.
 */
export default function VolumeChart({ data, height = 220 }) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} margin={{ top: 6, right: 8, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#1E2126" vertical={false} />
        <XAxis
          dataKey="label"
          tick={{ fontSize: 11, fill: '#6A6F76' }}
          stroke="#1E2126"
          fontFamily="JetBrains Mono, monospace"
          interval="preserveStartEnd"
        />
        <YAxis
          tick={{ fontSize: 11, fill: '#6A6F76' }}
          stroke="#1E2126"
          fontFamily="JetBrains Mono, monospace"
          tickFormatter={(v) => `${v}`}
          width={38}
        />
        <Tooltip cursor={{ fill: 'oklch(0.74 0.17 153 / 0.08)' }} content={<VolumeTooltip />} />
        <Bar dataKey="total_km" fill="oklch(0.74 0.17 153)" radius={[4, 4, 0, 0]} maxBarSize={44} />
      </BarChart>
    </ResponsiveContainer>
  )
}
