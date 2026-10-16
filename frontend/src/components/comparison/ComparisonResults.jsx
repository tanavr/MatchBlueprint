import ComparisonRadar from './ComparisonRadar'
import { CategoryTable, MetricTable } from './ComparisonTables'
import { dimensionLabels } from '../TacticalScores'
import { number } from './presentation'

function TextList({ items, empty }) {
  return items.length ? <ul className="trait-list">{items.map((item, index) => <li key={index}>{item}</li>)}</ul> : <p className="empty-copy">{empty}</p>
}

export default function ComparisonResults({ result, selections }) {
  const labels = Object.fromEntries(['a', 'b'].map(side => [side, `${selections[side].team.name} · ${selections[side].season.name}`]))
  return <div className="results comparison-results">
    <div className="comparison-team-headers">{['a', 'b'].map(side => {
      const profile = result[`team_${side}`], selected = selections[side]
      return <section key={side} className={`team-summary side-${side}`}><div className="team-summary-top"><span className="team-letter">{side.toUpperCase()}</span><span className="badge">{profile.data_kind === 'sample' ? 'Sample data · not real statistics' : `Source: ${profile.source}`}</span></div>
        <p className="eyebrow">{selected.competition.name} / {selected.season.name}</p><h2>{selected.team.name}</h2><p className="team-identity">{profile.primary_identity}</p>
      </section>
    })}</div>
    <div className="comparison-visual-grid"><ComparisonRadar comparison={result.tactical_score_comparison} labels={labels} />
      <section className="panel difference-panel"><p className="eyebrow">Where they diverge</p><h2>Strongest differences</h2><p className="muted">Largest backend-qualified leads of at least 10 points. These are stylistic advantages, not competitive ones.</p>
        {['a', 'b'].map(side => <div className={`difference-group side-${side}`} key={side}><h3>Team {side.toUpperCase()} emphasis</h3>
          {result[`team_${side}_advantages`].length ? result[`team_${side}_advantages`].map(item => <div className="difference-item" key={item.category}><span>{dimensionLabels[item.category] || item.category}</span><strong>+{number(item.lead_points)}<small> pts</small></strong></div>) : <p className="empty-copy">No supported lead meets the threshold.</p>}
        </div>)}
      </section>
    </div>
    <CategoryTable comparison={result.tactical_score_comparison} />
    <div className="comparison-insights"><section className="panel"><p className="eyebrow">Common ground</p><h2>Similarities</h2><TextList items={result.similarities} empty="No supported similarities were identified." /></section>
      <section className="panel"><p className="eyebrow">Reading the matchup</p><h2>Style meets style</h2><TextList items={result.matchup_observations} empty="No supported matchup observations are available." /></section></div>
    <MetricTable result={result} />
    <details className="panel limitations"><summary>Normalization & comparison limits</summary><TextList items={result.limitations} empty="No additional limitations supplied." /></details>
  </div>
}
