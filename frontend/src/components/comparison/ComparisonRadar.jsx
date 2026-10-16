import { Legend, PolarAngleAxis, PolarGrid, PolarRadiusAxis, Radar, RadarChart, ResponsiveContainer, Tooltip } from 'recharts'
import { dimensionLabels } from '../TacticalScores'
import { comparable, number } from './presentation'

const shortLabels = {
  possession: 'Possession', pressing: 'Pressing', directness: 'Directness',
  attacking_intensity: 'Attack', defensive_intensity: 'Defense',
  counterattacking_tendency: 'Counters', passing_control: 'Control',
}

function RadarTooltip({ active, payload }) {
  if (!active || !payload?.length) return null
  const row = payload[0].payload
  return <div className="radar-tooltip"><strong>{row.fullLabel}</strong>
    <p className="color-a">A · {number(row.a)} / 100</p>
    <p className="color-b">B · {number(row.b)} / 100</p>
    <small>Relative to each team’s own season</small>
  </div>
}

export default function ComparisonRadar({ comparison, labels }) {
  const rows = Object.entries(dimensionLabels).map(([key, fullLabel]) => ({
    key, label: shortLabels[key], fullLabel, a: comparison[key]?.team_a, b: comparison[key]?.team_b,
  }))
  const unavailable = rows.filter(row => !comparable(comparison[row.key]))
  return <section className="panel comparison-radar" aria-labelledby="radar-title">
    <div className="section-heading"><div><p className="eyebrow">The shape of their game</p><h2 id="radar-title">Tactical overlay</h2></div><span className="badge">Fixed scale · 0–100</span></div>
    <p className="muted">Seven dimensions. Each team measured against its own season peers.</p>
    {unavailable.length ? <div className="radar-unavailable" role="status"><h3>Not enough comparable evidence</h3><p>The radar needs all seven comparable dimensions. Missing values are never drawn as zero.</p><p>Unavailable: {unavailable.map(row => row.fullLabel).join(', ')}.</p><a className="text-link" href="#category-comparison" onClick={event => {
      event.preventDefault(); document.getElementById('category-comparison')?.focus()
    }}>Read the available categories below ↓</a></div> : <>
      <div className="radar-canvas" role="group" aria-label="Team A and Team B tactical radar on a fixed zero to one hundred scale. Exact values follow in the category table.">
        <ResponsiveContainer width="100%" height="100%" minWidth={0}>
          <RadarChart data={rows} outerRadius="64%" margin={{ top: 22, right: 32, bottom: 18, left: 32 }}>
            <PolarGrid stroke="#364552" />
            <PolarAngleAxis dataKey="label" tick={{ fill: '#c6d3df', fontSize: 11 }} />
            <PolarRadiusAxis domain={[0, 100]} ticks={[0, 25, 50, 75, 100]} tick={{ fill: '#9aaebc', fontSize: 10 }} axisLine={false} />
            <Radar name={`A · ${labels.a}`} dataKey="a" stroke="#8cdbaf" strokeWidth={2} fill="#8cdbaf" fillOpacity={0.12} isAnimationActive={false} dot={{ r: 3 }} />
            <Radar name={`B · ${labels.b}`} dataKey="b" stroke="#8fbaff" strokeWidth={2} strokeDasharray="5 4" fill="#8fbaff" fillOpacity={0.07} isAnimationActive={false} dot={{ r: 3 }} />
            <Tooltip content={<RadarTooltip />} />
            <Legend wrapperStyle={{ fontSize: 11, lineHeight: '22px' }} />
          </RadarChart>
        </ResponsiveContainer>
      </div>
      <p className="chart-caption">Solid green: A · Dashed blue: B. Attack = attacking intensity; defense = defensive activity; control = passing/control. Possession and pressing are proxies.</p>
    </>}
  </section>
}
