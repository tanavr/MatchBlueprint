import Feedback from './Feedback'
import MetricGrid from './MetricGrid'
import TacticalScores from './TacticalScores'

export default function AnalysisResults({ result, onRetry }) {
  const { selection, metrics, tactical, errors } = result
  const sample = tactical?.data_kind === 'sample' || metrics?.provenance.some(p => p.data_kind === 'sample') || selection.team.provenance?.data_kind === 'sample'
  return <div className="results">
    <header className="result-header"><div><p className="eyebrow">Team report / {selection.competition.name}</p><h2>{selection.team.name} <span>{selection.season.name}</span></h2></div><span className={`badge ${sample ? 'sample' : ''}`}>{sample ? 'Sample data · not real statistics' : 'Source: ' + (tactical?.source || metrics?.provenance[0]?.source || 'unavailable')}</span></header>
    {errors.map(({ name, error }) => <Feedback key={name} error title={`${name} unavailable`} onRetry={onRetry}>{error.message}</Feedback>)}
    <section className="identity-card"><span className="eyebrow">Tactical identity</span><h3>{tactical?.primary_identity || 'Awaiting sufficient evidence'}</h3><p>{tactical?.explanation || 'Available raw statistics are shown below. A tactical identity requires reviewed season coverage and a sufficient comparison cohort.'}</p></section>
    <MetricGrid profile={metrics} />
    <div className="analysis-columns"><TacticalScores scores={tactical?.scores} /><div className="insights-column">
      <section className="panel"><span className="eyebrow">Profile interpretation</span><h2>Strengths & tendencies</h2><p className="muted">Stylistic emphasis, not a measure of playing quality.</p>
        {tactical?.secondary_traits.length ? <ul className="trait-list">{tactical.secondary_traits.map(trait => <li key={trait}>{trait}</li>)}</ul> : <p className="empty-copy">No supported secondary traits to display for this profile.</p>}
      </section>
      <section className="panel"><span className="eyebrow">Read with context</span><h2>What the scores mean</h2><p>A 75 places a trait toward the upper end of its eligible season cohort. It does not mean a 75% chance of winning.</p><p>Possession and pressing use event-based proxies. Missing evidence stays unavailable.</p><a className="text-link" href="#about">Explore the model →</a></section>
    </div></div>
    <details className="panel limitations"><summary>Coverage & model limitations</summary><ul>{(tactical?.limitations || metrics?.notes || ['No analytical evidence is available.']).map(note => <li key={note}>{note}</li>)}</ul>{tactical && <p>Model {tactical.model_version} · Minimum {tactical.config.min_matches} matches and {tactical.config.min_teams} eligible teams.</p>}</details>
  </div>
}
