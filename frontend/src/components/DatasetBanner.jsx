import { useEffect, useState } from 'react'
import { api } from '../api'

export default function DatasetBanner() {
  const [status, setStatus] = useState(null)
  useEffect(() => {
    const controller = new AbortController()
    api.dataset(controller.signal).then(setStatus).catch(error => {
      if (error.name !== 'AbortError') setStatus({ prepared: false })
    })
    return () => controller.abort()
  }, [])
  if (!status) return null
  return <aside className="dataset-banner" aria-label="Available data">
    {status.prepared ? <><strong>Prepared football data</strong>
      {status.seasons.map(item => <span key={`${item.competition}-${item.season}`}>
        {item.data_kind === 'real' ? 'Real data' : 'Sample data'} · {item.competition} {item.season} · {item.teams} clubs · {item.matches} matches
      </span>)}<a href="https://github.com/statsbomb/open-data" target="_blank" rel="noreferrer">Data: StatsBomb Open Data ↗</a></>
      : <><strong>Real dataset not loaded</strong><span>Start the backend with app.main:app after running python -m app.data.prepare_demo. The fixture server is for tests only.</span></>}
  </aside>
}
