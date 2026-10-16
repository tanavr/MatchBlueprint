import test from 'node:test'
import assert from 'node:assert/strict'
import { comparable, emphasis, number, signed } from '../src/components/comparison/presentation.js'

test('missing data is never rendered as zero or an advantage', () => {
  for (const value of [null, undefined, NaN]) assert.equal(number(value), '—')
  assert.equal(number(0), '0.0')
  assert.equal(comparable({ team_a: 75, team_b: null, difference_a_minus_b: null }), false)
  assert.equal(emphasis({ team_a: 75, team_b: null, difference_a_minus_b: null }), 'Not comparable')
})

test('reference exclusions override numeric scores', () => {
  assert.equal(comparable({ team_a: 50, team_b: 50, difference_a_minus_b: null, reason: 'Constant cohort' }), false)
  assert.equal(comparable({ team_a: 50, team_b: 50, difference_a_minus_b: 0, reason: 'Incompatible cohorts' }), false)
})

test('delta signs preserve A minus B and equal profiles', () => {
  assert.equal(emphasis({ team_a: 80, team_b: 20, difference_a_minus_b: 60 }), 'A +60.0 pts')
  assert.equal(emphasis({ team_a: 20, team_b: 80, difference_a_minus_b: -60 }), 'B +60.0 pts')
  assert.equal(emphasis({ team_a: 20, team_b: 20, difference_a_minus_b: 0 }), 'Equal emphasis')
  assert.equal(signed(-60), '-60.0')
  assert.equal(signed(60), '+60.0')
})
