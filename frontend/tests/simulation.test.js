import test from 'node:test'
import assert from 'node:assert/strict'
import { percent, goals, validateSimulation } from '../src/components/simulation/presentation.js'

// Synthetic transport values, not real football predictions.
const fixture = () => ({
  team_a_win_probability: 0.5, draw_probability: 0.3, team_b_win_probability: 0.2,
  expected_goals_a: 1.5, expected_goals_b: 0.8,
  average_simulated_score: { team_a: 1.5, team_b: 0.8 },
  most_likely_scorelines: [{ goals_a: 1, goals_b: 0, probability: 0.15 }],
})

test('probabilities are displayed as percentages, not already-percent inputs', () => {
  assert.equal(percent(0), '0.0%')
  assert.equal(percent(0.3), '30.0%')
  assert.equal(percent(1), '100.0%')
  assert.equal(goals(1.5), '1.50')
})

test('valid output is preserved without changing model probabilities', () => {
  const data = fixture()
  assert.equal(validateSimulation(data), data)
  assert.equal(data.team_a_win_probability, 0.5)
})

test('zero-goal all-draw outcome is valid', () => {
  const data = { ...fixture(), team_a_win_probability: 0, draw_probability: 1,
    team_b_win_probability: 0, expected_goals_a: 0, expected_goals_b: 0,
    average_simulated_score: { team_a: 0, team_b: 0 },
    most_likely_scorelines: [{ goals_a: 0, goals_b: 0, probability: 1 }] }
  assert.equal(validateSimulation(data), data)
})

test('invalid values and probability totals are rejected instead of normalized', () => {
  for (const value of [null, undefined, -0.1, 1.1, NaN, Infinity, '0.5', 0.7]) {
    assert.throws(() => validateSimulation({ ...fixture(), team_a_win_probability: value }))
  }
  assert.throws(() => validateSimulation(null))
  assert.throws(() => validateSimulation({ ...fixture(), expected_goals_a: -1 }))
  assert.throws(() => validateSimulation({ ...fixture(), average_simulated_score: null }))
})

test('invalid scorelines are not rendered as plausible results', () => {
  for (const row of [{ goals_a: -1, goals_b: 0, probability: 0.2 },
    { goals_a: 1.5, goals_b: 0, probability: 0.2 }, { goals_a: 1, goals_b: 0, probability: 2 }]) {
    assert.throws(() => validateSimulation({ ...fixture(), most_likely_scorelines: [row] }))
  }
})
