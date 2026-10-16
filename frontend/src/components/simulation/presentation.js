export const percent = value => `${(value * 100).toFixed(1)}%`
export const goals = value => value.toFixed(2)

// Fail explicitly instead of drawing malformed or missing probabilities as zero.
export function validateSimulation(result) {
  const probabilities = [result?.team_a_win_probability, result?.draw_probability, result?.team_b_win_probability]
  const validProbability = value => Number.isFinite(value) && value >= 0 && value <= 1
  const means = [result?.expected_goals_a, result?.expected_goals_b,
    result?.average_simulated_score?.team_a, result?.average_simulated_score?.team_b]
  if (!probabilities.every(validProbability)
    || Math.abs(probabilities.reduce((sum, value) => sum + value, 0) - 1) > 1e-6
    || !means.every(value => Number.isFinite(value) && value >= 0)
    || !Array.isArray(result?.most_likely_scorelines)
    || !result.most_likely_scorelines.every(row => Number.isInteger(row.goals_a) && row.goals_a >= 0
      && Number.isInteger(row.goals_b) && row.goals_b >= 0 && validProbability(row.probability))) {
    throw new Error('The API returned incomplete or invalid simulation probabilities. Please try again.')
  }
  return result
}
