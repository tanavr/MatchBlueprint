import { useEffect, useRef, useState } from 'react'
import { api } from '../api'
import Feedback from '../components/Feedback'
import ComparisonPicker from '../components/comparison/ComparisonPicker'
import ComparisonResults from '../components/comparison/ComparisonResults'

export default function Compare() {
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

  async function compare(event) {
    event?.preventDefault()
    if (!selections.a || !selections.b) return
    request.current?.abort()
    const controller = new AbortController()
    request.current = controller
    setBusy(true); setReport(null); setError(null)
    try {
      const result = await api.compare(selections.a, selections.b, controller.signal)
      if (!controller.signal.aborted) setReport({ result, selections })
    } catch (failure) {
      if (!controller.signal.aborted) setError(failure)
    } finally {
      if (!controller.signal.aborted) setBusy(false)
    }
  }

  return <>
    <div className="page-heading"><p className="eyebrow">The comparison room</p><h1>Two teams. Two blueprints.</h1><p>Put playing styles side by side, with each season kept in context.</p></div>
    <form onSubmit={compare}>
      <div className="comparison-pickers"><ComparisonPicker side="A" onChange={selection => select('a', selection)} /><ComparisonPicker side="B" onChange={selection => select('b', selection)} /></div>
      <div className="compare-action"><p>Different clubs, leagues, or eras.<br /><span>One transparent comparison.</span></p><button className="primary-button" disabled={!selections.a || !selections.b || busy}>{busy ? 'Comparing…' : 'Compare teams →'}</button></div>
    </form>
    {busy && <div className="panel loading-panel" role="status"><div className="loading-line" /><h2>Comparing their approaches</h2><p>Building both profiles against their competition-season cohorts…</p></div>}
    {error && <Feedback error title="Comparison unavailable" onRetry={() => compare()}>{error.message} {error.code === 'coverage_not_verified' && 'Both seasons need reviewed coverage before a comparison can be made.'}</Feedback>}
    {!busy && !error && !report && <section className="empty-panel"><p className="eyebrow">Find the contrasts</p><h2>A shared view of different styles.</h2><p>Select both teams to explore their tactical shapes, strongest differences, and common ground.</p></section>}
    {report && <ComparisonResults key={`${report.result.team_a.team_id}-${report.result.team_b.team_id}`} {...report} />}
  </>
}
