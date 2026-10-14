export const dimensionLabels = {
  possession: 'Possession', pressing: 'Pressing', directness: 'Directness', attacking_intensity: 'Attacking intensity',
  defensive_intensity: 'Defensive activity', counterattacking_tendency: 'Counterattacking', passing_control: 'Passing / control',
}
export default function TacticalScores({ scores = {} }) {
  return <section className="panel score-panel"><div className="section-heading"><div><span className="eyebrow">Relative to season peers</span><h2>Tactical dimensions</h2></div><span className="scale-label">0—100</span></div>
    <p className="muted">Higher means more of a trait, not a better team.</p>
    <div className="score-list">{Object.entries(dimensionLabels).map(([key, label]) => {
      const score = scores[key]
      const available = Number.isFinite(score?.value)
      return <div className="score-row" key={key}>
        <div className="score-label"><span>{label}{score?.proxy && <small>Proxy</small>}</span><strong>{available ? score.value.toFixed(0) : '—'}</strong></div>
        <div className={`score-track ${available ? '' : 'unavailable'}`} aria-hidden="true"><span style={{ width: `${available ? score.value : 0}%` }} /></div>
        <details><summary>{available ? `${score.cohort_team_ids.length} peers · ${score.eligible_match_ids.length} matches` : 'Why unavailable?'}</summary>
          <p>{score?.reason || score?.interpretation || 'No tactical profile is available for this selection.'}</p>
          {!!score?.constant_components?.length && <p>No variation in some reference metrics. A score of 50 is not evidence of balanced tactics.</p>}
        </details>
      </div>
    })}</div>
  </section>
}
