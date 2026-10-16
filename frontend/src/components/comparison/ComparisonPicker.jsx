import { useId, useState } from 'react'
import useCatalog from '../../hooks/useCatalog'
import Feedback from '../Feedback'

export default function ComparisonPicker({ side, onChange }) {
  const id = useId()
  const [competition, setCompetition] = useState('')
  const [season, setSeason] = useState('')
  const [team, setTeam] = useState('')
  const catalog = useCatalog(competition, season)

  function select(field, value) {
    if (field === 'competition') {
      setCompetition(value); setSeason(''); setTeam('')
      onChange(null)
    } else if (field === 'season') {
      setSeason(value); setTeam('')
      onChange(null)
    } else {
      setTeam(value)
      onChange(value ? {
        competition: catalog.competitions.find(item => item.id === competition),
        season: catalog.seasons.find(item => item.id === season),
        team: catalog.teams.find(item => item.id === value),
      } : null)
    }
  }

  const fields = [
    ['competition', competition, catalog.competitions, false],
    ['season', season, catalog.seasons, !competition],
    ['team', team, catalog.teams, !season],
  ]
  const active = !competition ? catalog.competitions : !season ? catalog.seasons : catalog.teams
  return <fieldset className={`panel comparison-picker side-${side.toLowerCase()}`}>
    <legend>Team {side}</legend>
    <div className="picker-heading"><span className="team-letter">{side}</span><div><h2>Select Team {side}</h2><p>Choose any available club-season</p></div></div>
    <div className="comparison-fields">
      {fields.map(([field, value, options, disabled]) => <label key={field} htmlFor={`${id}-${field}`}>
        {field.charAt(0).toUpperCase() + field.slice(1)}
        <select id={`${id}-${field}`} aria-label={`Team ${side} ${field}`} value={value}
          disabled={disabled || catalog.loading} onChange={event => select(field, event.target.value)}>
          <option value="">Choose {field}</option>
          {options.map(item => <option value={item.id} key={item.id}>
            {item.name}{item.provenance?.data_kind === 'sample' ? ' · Sample' : ''}
          </option>)}
        </select>
      </label>)}
    </div>
    {catalog.loading && <p className="inline-status" role="status">Loading Team {side} options…</p>}
    {catalog.error && <Feedback error title={`Team ${side} data unavailable`} onRetry={catalog.retry}>{catalog.error.message}</Feedback>}
    {!catalog.loading && !catalog.error && !active.length && <Feedback title="No available records">Try another competition or season, or prepare data on the backend.</Feedback>}
  </fieldset>
}
