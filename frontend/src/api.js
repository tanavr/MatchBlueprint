// One place for transport, URL encoding, cancellation, and API error messages.
const BASE = (import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000').replace(/\/$/, '')

export class ApiError extends Error {
  constructor(message, status, code) {
    super(message)
    this.status = status
    this.code = code
  }
}

async function get(path, signal) {
  let response
  try {
    response = await fetch(`${BASE}${path}`, { signal })
  } catch (error) {
    if (error.name === 'AbortError') throw error
    throw new ApiError('Cannot reach the football API. Check that the backend is running and try again.', 0, 'connection')
  }
  let body
  try { body = await response.json() } catch {
    throw new ApiError('The API returned an unreadable response. Please try again.', response.status, 'invalid_response')
  }
  if (!response.ok) throw new ApiError(body.error?.message || `Request failed (${response.status}).`, response.status, body.error?.code)
  return body
}
const scope = (competition, season) => `/competitions/${encodeURIComponent(competition)}/seasons/${encodeURIComponent(season)}`
export const api = {
  competitions: signal => get('/competitions', signal),
  seasons: (competition, signal) => get(`/competitions/${encodeURIComponent(competition)}/seasons`, signal),
  teams: (competition, season, signal) => get(`${scope(competition, season)}/teams`, signal),
  metrics: (selection, signal) => get(`${scope(selection.competition.id, selection.season.id)}/teams/${encodeURIComponent(selection.team.id)}/metrics`, signal),
  tactical: (selection, signal) => get(`${scope(selection.competition.id, selection.season.id)}/teams/${encodeURIComponent(selection.team.id)}/tactical-profile`, signal),
}
