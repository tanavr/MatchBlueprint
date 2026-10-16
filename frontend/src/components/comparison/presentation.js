export const number = value => Number.isFinite(value) ? value.toFixed(1) : '—'
export const signed = value => Number.isFinite(value) ? `${value > 0 ? '+' : ''}${value.toFixed(1)}` : '—'
export const metricLabel = key => key.replaceAll('_', ' ').replace(/\bxg\b/g, 'xG').replace(/\bpct\b/g, '(%)')
export const comparable = item => Number.isFinite(item?.team_a) && Number.isFinite(item?.team_b)
  && Number.isFinite(item?.difference_a_minus_b) && !item?.reason

// Describe the API's delta. This is a display label, not a new strength model.
export function emphasis(item) {
  if (!comparable(item)) return 'Not comparable'
  if (item.difference_a_minus_b === 0) return 'Equal emphasis'
  return `${item.difference_a_minus_b > 0 ? 'A' : 'B'} +${Math.abs(item.difference_a_minus_b).toFixed(1)} pts`
}
