const metrics = [
  ['goals_for_per_match', 'Goals for', 'per match'], ['goals_against_per_match', 'Goals against', 'per match'],
  ['shots_per_match', 'Shots', 'per match'], ['xg_per_match', 'Expected goals', 'shot-based xG / match'],
  ['possession_pass_share_pct', 'Pass share', '% · possession proxy'], ['pass_completion_pct', 'Pass completion', '%'],
]
export default function MetricGrid({ profile }) {
  return <section aria-labelledby="raw-title"><div className="section-heading"><div><span className="eyebrow">The underlying numbers</span><h2 id="raw-title">Season statistics</h2></div><span className="muted">{profile ? `${profile.matches_played} recorded matches` : 'Coverage unavailable'}</span></div>
    <div className="metric-grid">{metrics.map(([key, label, unit]) => {
      const metric = profile?.metrics[key]
      const available = metric?.status !== 'unavailable' && Number.isFinite(metric?.value)
      return <article className="metric-card" key={key}><h3>{label}</h3><div className="metric-value">{available ? metric.value.toFixed(1) : '—'}</div><p>{unit}</p>
        <details><summary>{available ? `${metric.eligible_match_ids.length} matches${metric.status === 'partial' ? ' · Partial' : ''}` : 'Unavailable'}</summary>
          <p>{metric?.reason || (available ? `Calculated using ${metric.eligible_match_ids.length} eligible matches; ${Object.keys(metric.excluded_matches).length} excluded.` : 'Required data is missing or not reviewed.')}</p>
        </details></article>
    })}</div>
  </section>
}
