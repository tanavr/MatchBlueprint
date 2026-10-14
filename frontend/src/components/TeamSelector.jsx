import { useState } from 'react'
import useCatalog from '../hooks/useCatalog'
import Feedback from './Feedback'

export default function TeamSelector({ onAnalyze, onChange, busy }) {
  const [competition, setCompetition] = useState('')
  const [season, setSeason] = useState('')
  const [team, setTeam] = useState('')
  const catalog = useCatalog(competition, season)
  const select = (kind, value) => {
    onChange()
    if (kind === 'competition') { setCompetition(value); setSeason(''); setTeam('') }
    if (kind === 'season') { setSeason(value); setTeam('') }
    if (kind === 'team') setTeam(value)
  }
  const fields = [
    ['competition', 'Competition', competition, catalog.competitions, false],
    ['season', 'Season', season, catalog.seasons, !competition],
    ['team', 'Team', team, catalog.teams, !season],
  ]
  const submit = event => {
    event.preventDefault()
    onAnalyze({ competition: catalog.competitions.find(c => c.id === competition),
      season: catalog.seasons.find(s => s.id === season), team: catalog.teams.find(t => t.id === team) })
  }
  const activeList = !competition ? catalog.competitions : !season ? catalog.seasons : catalog.teams
  return <section className="panel selector-panel" aria-labelledby="selection-title">
    <div className="section-heading"><div><span className="eyebrow">Select your context</span><h2 id="selection-title">One team. One season.</h2></div><span className="muted">Source-driven selection</span></div>
    <form onSubmit={submit} className="selector-form">
      {fields.map(([key, label, value, options, disabled]) => <label key={key} htmlFor={`select-${key}`}>{label}
        <select id={`select-${key}`} value={value} disabled={disabled || catalog.loading} onChange={e => select(key, e.target.value)}>
          <option value="">Choose {label.toLowerCase()}</option>
          {options.map(item => <option key={item.id} value={item.id}>{item.name}{item.provenance?.data_kind === 'sample' ? ' · Sample' : ''}</option>)}
        </select>
      </label>)}
      <button className="primary-button" disabled={!team || busy || catalog.loading || !!catalog.error}>{busy ? 'Analyzing…' : 'Analyze team →'}</button>
    </form>
    {catalog.loading && <p className="inline-status" role="status">Loading {competition ? season ? 'teams' : 'seasons' : 'competitions'}…</p>}
    {catalog.error && <Feedback error title="Data unavailable" onRetry={catalog.retry}>{catalog.error.message}{catalog.error.code === 'data_not_prepared' ? ' The server needs a prepared local dataset.' : ''}</Feedback>}
    {!catalog.loading && !catalog.error && !activeList.length && <Feedback title="No records available">There are no available {competition ? season ? 'teams in this season' : 'seasons in this competition' : 'competitions in this dataset'}. Try another selection or prepare data on the backend.</Feedback>}
  </section>
}
