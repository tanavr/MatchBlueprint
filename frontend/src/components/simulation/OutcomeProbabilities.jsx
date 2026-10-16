import { percent } from './presentation'

export default function OutcomeProbabilities({ result, selections }) {
  const outcomes = [
    { key: 'a', label: 'Team A win', name: selections.a.team.name, value: result.team_a_win_probability },
    { key: 'draw', label: 'Draw', name: 'Level score', value: result.draw_probability },
    { key: 'b', label: 'Team B win', name: selections.b.team.name, value: result.team_b_win_probability },
  ]
  return <section className="panel outcome-panel" aria-labelledby="outcome-heading">
    <div className="section-heading"><div><p className="eyebrow">A distribution, not a verdict</p><h2 id="outcome-heading">Match outcome probabilities</h2></div><span className="badge">Neutral venue</span></div>
    <div className="outcome-cards">{outcomes.map(outcome => <div className={`outcome-card outcome-${outcome.key}`} key={outcome.key}>
      <h3>{outcome.label}</h3><strong>{percent(outcome.value)}</strong><p>{outcome.name}</p>
    </div>)}</div>
    <div className="probability-bar" role="img" aria-label={outcomes.map(o => `${o.label}: ${percent(o.value)}`).join('; ')}>
      {outcomes.map(outcome => <span key={outcome.key} className={`outcome-${outcome.key}`} style={{ width: `${outcome.value * 100}%` }} title={`${outcome.label}: ${percent(outcome.value)}`} />)}
    </div>
    <div className="probability-scale" aria-hidden="true"><span>0%</span><span>50%</span><span>100%</span></div>
    <p className="chart-caption">Green: A win · Gray: draw · Blue: B win. Segment widths use the API probabilities on a fixed 0–100% scale. Display rounding may affect the total shown.</p>
  </section>
}
