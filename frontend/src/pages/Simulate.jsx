import { useEffect, useRef, useState } from 'react'
import { api } from '../api'
import ComparisonPicker from '../components/comparison/ComparisonPicker'
import Feedback from '../components/Feedback'
import SimulationResults from '../components/simulation/SimulationResults'
import { validateSimulation } from '../components/simulation/presentation'

export default function Simulate() {
  const [selections, setSelections] = useState({ a: null, b: null })
  const [report, setReport] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const request = useRef(null)
  useEffect(() => () => request.current?.abort(), [])

  function select(side, selection) {
    request.current?.abort()
    setSelections(current => ({ ...current, [side]: selection }))
    setReport(null); setError(null); setBusy(false)
  }

  async function simulate(event) {
    event?.preventDefault()
    if (!selections.a || !selections.b) return
    request.current?.abort()
    const controller = new AbortController()
    request.current = controller
    setBusy(true); setReport(null); setError(null)
    try {
      const result = validateSimulation(await api.simulate(selections.a, selections.b, controller.signal))
      if (!controller.signal.aborted) setReport({ result, selections })
    } catch (failure) {
      if (!controller.signal.aborted) setError(failure)
    } finally {
      if (!controller.signal.aborted) setBusy(false)
    }
  }

  return <>
    <div className="page-heading"><p className="eyebrow">The hypothetical matchup</p><h1>Explore the possibilities.</h1><p>An explainable statistical scenario, grounded in each team’s season.</p></div>
    <form onSubmit={simulate}><div className="comparison-pickers"><ComparisonPicker side="A" onChange={selection => select('a', selection)} /><ComparisonPicker side="B" onChange={selection => select('b', selection)} /></div>
      <div className="compare-action"><p><span>A statistical hypothetical, not a guaranteed prediction.</span></p><button className="primary-button" disabled={!selections.a || !selections.b || busy}>{busy ? 'Calculating…' : 'Run Simulation'}</button></div>
    </form>
    {busy && <div className="panel loading-panel" role="status"><div className="loading-line" /><h2>Calculating the matchup</h2><p>Checking season coverage and calculating goal probabilities…</p></div>}
    {error && <Feedback error title="Simulation unavailable" onRetry={() => simulate()}>{error.message} {['coverage_not_verified', 'simulation_unavailable'].includes(error.code) && 'The model needs complete reviewed season scores and at least 10 matches for each selected team.'}</Feedback>}
    {!busy && !error && !report && <section className="empty-panel"><p className="eyebrow">From strengths to probabilities</p><h2>What might the matchup look like?</h2><p>Select two club-seasons to estimate goals, explore possible scorelines and see the assumptions behind each probability.</p></section>}
    {report && <SimulationResults {...report} />}
  </>
}
