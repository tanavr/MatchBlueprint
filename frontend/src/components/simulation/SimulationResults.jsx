import OutcomeProbabilities from './OutcomeProbabilities'
import { goals, percent } from './presentation'

export default function SimulationResults({ result, selections }) {
  return <div className="results simulation-results">
    <p className="simulation-disclaimer">Statistical hypothetical, not a guaranteed prediction. These probabilities describe the model’s assumptions; they are not validated certainty about a real match.</p>
    <div className="comparison-team-headers">{['a', 'b'].map(side => {
      const selection = selections[side]
      return <section key={side} className={`team-summary side-${side}`}>
        <div className="team-summary-top"><span className="team-letter">{side.toUpperCase()}</span><span className={`badge ${result.data_kind === 'sample' ? 'sample' : ''}`}>{result.data_kind === 'sample' ? 'Sample data · not real statistics' : `Source: ${result[`team_${side}`].provenance[0]?.source || 'Unavailable'}`}</span></div>
        <p className="eyebrow">{selection.competition.name} / {selection.season.name}</p><h2>{selection.team.name}</h2>
        <div className="expected-goals"><strong>{goals(result[`expected_goals_${side}`])}</strong><span>Expected goals<br /><small>Model mean · not shot-based xG</small></span></div>
      </section>
    })}</div>
    <OutcomeProbabilities result={result} selections={selections} />
    <div className="simulation-detail-grid">
      <section className="panel"><p className="eyebrow">Possible scorelines</p><h2>Most likely results</h2><p className="muted">Individual score probabilities, not guarantees. Team A is listed first.</p>
        <table className="scoreline-table"><caption>A: {selections.a.team.name} · B: {selections.b.team.name}</caption>
          <thead><tr><th scope="col">A — B</th><th scope="col">Probability</th></tr></thead>
          <tbody>{result.most_likely_scorelines.map(row => <tr key={`${row.goals_a}-${row.goals_b}`}><th scope="row"><span className="color-a">{row.goals_a}</span><span className="score-separator">—</span><span className="color-b">{row.goals_b}</span></th><td>{percent(row.probability)}</td></tr>)}</tbody>
        </table>
        {!result.most_likely_scorelines.length && <p className="empty-copy">No scorelines were returned.</p>}
        <p className="chart-caption">Only the highest-probability scorelines are listed. Their probabilities need not add to 100%.</p>
      </section>
      <section className="panel"><p className="eyebrow">Why these estimates?</p><h2>Model explanation</h2><ul className="trait-list">{result.explanation.map((text, index) => <li key={index}>{text}</li>)}</ul>
        <div className="average-score"><h3>Average model score · A — B</h3><strong>{goals(result.average_simulated_score.team_a)} — {goals(result.average_simulated_score.team_b)}</strong><p>The analytical average can be fractional. It is not a prediction of an exact final score.</p></div>
      </section>
    </div>
    <section className="panel"><p className="eyebrow">Inputs in context</p><h2>What informed this scenario</h2><p className="muted">Each team’s scoring and conceding rates are measured against its own season. A lower concession ratio represents fewer goals conceded.</p>
      <div className="comparison-table-scroll" role="region" aria-label="Simulation model inputs" tabIndex="0"><table className="comparison-table"><caption>Shared scoring baseline: {goals(result.reference_goals_per_team_match)} goals per team-match</caption>
        <thead><tr><th scope="col">Input</th><th scope="col">Team A</th><th scope="col">Team B</th></tr></thead>
        <tbody>{[
          ['matches', 'Team matches', false], ['season_matches', 'Season matches in baseline', false],
          ['goals_for_per_match', 'Goals scored / match', true], ['goals_against_per_match', 'Goals conceded / match', true],
          ['season_goals_per_team_match', 'Own-season goals / team-match', true], ['attack_ratio', 'Attack ratio', true], ['concession_ratio', 'Concession ratio', true],
        ].map(([key, label, decimal]) => <tr key={key}><th scope="row">{label}</th>{['a', 'b'].map(side => <td key={side}>{decimal ? goals(result[`team_${side}`][key]) : result[`team_${side}`][key]}</td>)}</tr>)}</tbody>
      </table></div>
    </section>
  </div>
}
