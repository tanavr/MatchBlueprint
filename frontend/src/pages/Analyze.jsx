import { useEffect, useRef, useState } from 'react'
import { api } from '../api'
import TeamSelector from '../components/TeamSelector'
import AnalysisResults from '../components/AnalysisResults'
import Feedback from '../components/Feedback'

export default function Analyze() {
  const [result, setResult] = useState(null)
  const [busy, setBusy] = useState(false)
  const request = useRef(null)
  useEffect(() => () => request.current?.abort(), [])
  function clear() { request.current?.abort(); setResult(null); setBusy(false) }
  async function analyze(selection) {
    request.current?.abort()
    const controller = new AbortController()
    request.current = controller
    setBusy(true); setResult(null)
    const responses = await Promise.allSettled([api.metrics(selection, controller.signal), api.tactical(selection, controller.signal)])
    if (controller.signal.aborted) return
    setResult({ selection, metrics: responses[0].status === 'fulfilled' ? responses[0].value : null,
      tactical: responses[1].status === 'fulfilled' ? responses[1].value : null,
      errors: responses.flatMap((response, index) => response.status === 'rejected' ? [{ name: index ? 'Tactical profile' : 'Raw statistics', error: response.reason }] : []) })
    setBusy(false)
  }
  return <>
    <div className="page-heading"><p className="eyebrow">Team intelligence</p><h1>Understand the approach.</h1><p>A statistical view of how a team plays, grounded in its season.</p></div>
    <TeamSelector onAnalyze={analyze} onChange={clear} busy={busy} />
    {busy && <div className="panel loading-panel" role="status"><div className="loading-line" /><h2>Building your team report</h2><p>Checking available metrics and the competition-season cohort…</p></div>}
    {!busy && !result && <section className="empty-panel"><div className="empty-symbol" aria-hidden="true"><i /><i /><i /><i /><i /></div><p className="eyebrow">Your analysis starts here</p><h2>Every team has a way of playing.</h2><p>Select a competition, season, and team to explore its tactical identity and the numbers behind it.</p><div className="empty-features"><span>07 tactical dimensions</span><span>Season-relative context</span><span>Transparent evidence</span></div></section>}
    {result && (result.metrics || result.tactical ? <AnalysisResults result={result} onRetry={() => analyze(result.selection)} /> : <Feedback error title="Unable to build this report" onRetry={() => analyze(result.selection)}>{result.errors.map(e => `${e.name}: ${e.error.message}`).join(' ')}</Feedback>)}
  </>
}
