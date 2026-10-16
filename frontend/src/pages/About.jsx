export default function About() {
  return <><div className="page-heading"><p className="eyebrow">About the model</p><h1>Evidence before interpretation.</h1><p>Transparent statistics. Explicit assumptions. No hidden predictions.</p></div>
    <div className="about-grid">{[
      ['01', 'Start with the events', 'Match scores and available events produce raw statistics. Missing fields remain unavailable. Sample records are always labeled.'],
      ['02', 'Put the season in context', 'Tactical dimensions use competition-season percentiles. Composite dimensions average their component ranks. Scores describe relative style, not absolute quality.'],
      ['03', 'Require enough evidence', 'Default scoring needs at least 10 eligible teams, 10 matches per team, and 80% coverage of the reviewed roster and expected matches. Constant metrics do not establish a distinctive style.'],
      ['04', 'Respect the limits', 'Pass share estimates possession; advanced defensive activity is a pressing proxy. Neither proves tactical intent. Labels and descriptions follow explicit statistical rules.'],
    ].map(([n, title, text]) => <section className="panel" key={n}><span className="eyebrow">{n} / Method</span><h2>{title}</h2><p>{text}</p></section>)}</div>
    <section className="panel model-note"><h2>Across seasons & hypothetical matches</h2><p>Comparison uses each team’s own season reference. The simulator uses a neutral-venue Poisson model based on relative scoring and conceding rates. These assumptions do not calibrate league strength or guarantee a result.</p><p>Analyze, Compare, and Simulate use the same source-aware backend. Missing data stays unavailable rather than being replaced with invented statistics.</p></section></>
}
