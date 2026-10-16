import { useState } from 'react'
import { dimensionLabels } from '../TacticalScores'
import { comparable, emphasis, metricLabel, number, signed } from './presentation'

export function CategoryTable({ comparison }) {
  return <section className="panel" id="category-comparison" tabIndex="-1">
    <div className="section-heading"><div><p className="eyebrow">Dimension by dimension</p><h2>Relative stylistic emphasis</h2></div></div>
    <p className="muted">A higher score indicates more of a trait, not a stronger team or a predicted winner.</p>
    <div className="comparison-table-scroll" role="region" aria-label="Tactical category table" tabIndex="0"><table className="comparison-table">
      <caption>All scores use 0–100. A and B refer to the team headers above.</caption>
      <thead><tr><th scope="col">Category</th><th scope="col">Team A</th><th scope="col">Team B</th><th scope="col">Emphasis / availability</th></tr></thead>
      <tbody>{Object.entries(dimensionLabels).map(([key, label]) => {
        const item = comparison[key]
        return <tr key={key}><th scope="row">{label}</th><td className="color-a">{number(item?.team_a)}</td><td className="color-b">{number(item?.team_b)}</td>
          <td><span className={`delta-badge ${comparable(item) ? item.difference_a_minus_b > 0 ? 'color-a' : item.difference_a_minus_b < 0 ? 'color-b' : '' : ''}`}>{emphasis(item)}</span>
            {item?.reason && <small className="table-reason">{item.reason}</small>}</td></tr>
      })}</tbody>
    </table></div>
  </section>
}

export function MetricTable({ result }) {
  const [mode, setMode] = useState('normalized')
  const values = mode === 'normalized' ? result.normalized_metric_differences : result.raw_metric_differences
  return <section className="panel">
    <div className="section-heading"><div><p className="eyebrow">Behind the profiles</p><h2>Metric comparison</h2></div>
      <div className="segmented-control" aria-label="Metric display mode">{['normalized', 'raw'].map(value => <button key={value} type="button" aria-pressed={mode === value} onClick={() => setMode(value)}>{value === 'normalized' ? 'Season percentiles' : 'Raw metrics'}</button>)}</div>
    </div>
    <p className="muted">{mode === 'normalized' ? 'Percentiles use independent competition-season cohorts. Some raw metrics have no fitted percentile.' : 'Raw numbers are context only. Different leagues, eras and match coverage can explain differences; higher is not automatically better.'}</p>
    <div className="comparison-table-scroll" role="region" aria-label="Metric comparison table" tabIndex="0"><table className="comparison-table">
      <caption>{mode === 'normalized' ? 'Own-season component percentiles' : 'Unadjusted raw statistics'} · Difference = A minus B</caption>
      <thead><tr><th scope="col">Metric / unit</th><th scope="col">Team A</th><th scope="col">Team B</th><th scope="col">Difference</th></tr></thead>
      <tbody>{Object.entries(values).map(([key, item]) => <tr key={key}><th scope="row">{metricLabel(key)}<small>{item.unit}</small></th><td>{number(item.team_a)}</td><td>{number(item.team_b)}</td><td>{signed(item.difference_a_minus_b)}{item.reason && <small className="table-reason">{item.reason}</small>}</td></tr>)}</tbody>
    </table></div>
    {!Object.keys(values).length && <p className="empty-copy">No metric records are available for this comparison.</p>}
    <details className="metric-coverage"><summary>Inspect source coverage before interpreting differences</summary>
      {['a', 'b'].map(side => <div key={side}><h3>Team {side.toUpperCase()} · {result[`team_${side}`].data_kind} data</h3><ul>
        {Object.entries(result[`team_${side}`].raw_metrics).map(([key, metric]) => <li key={key}>{metricLabel(key)}: {metric.status}, {metric.eligible_match_ids.length} eligible matches, {Object.keys(metric.excluded_matches).length} excluded.{metric.reason ? ` ${metric.reason}` : ''}</li>)}
      </ul></div>)}
    </details>
  </section>
}
