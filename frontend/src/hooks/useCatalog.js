import { useEffect, useState } from 'react'
import { api } from '../api'

// Effect cleanup prevents a slow previous selection from overwriting a new one.
export default function useCatalog(competition, season) {
  const [competitions, setCompetitions] = useState([])
  const [seasons, setSeasons] = useState([])
  const [teams, setTeams] = useState([])
  const [status, setStatus] = useState({ loading: true, error: null })
  const [retry, setRetry] = useState(0)
  useEffect(() => {
    const controller = new AbortController()
    setStatus({ loading: true, error: null })
    if (!competition) { setCompetitions([]); setSeasons([]); setTeams([]) }
    else if (!season) { setSeasons([]); setTeams([]) }
    else setTeams([])
    const request = !competition ? api.competitions(controller.signal)
      : !season ? api.seasons(competition, controller.signal) : api.teams(competition, season, controller.signal)
    request.then(data => {
      if (controller.signal.aborted) return
      if (!competition) setCompetitions(data.competitions)
      else if (!season) setSeasons(data.seasons)
      else setTeams(data.teams)
      setStatus({ loading: false, error: null })
    }).catch(error => {
      if (!controller.signal.aborted) setStatus({ loading: false, error })
    })
    return () => controller.abort()
  }, [competition, season, retry])
  return { competitions, seasons, teams, ...status, retry: () => setRetry(n => n + 1) }
}
