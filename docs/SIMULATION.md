# Explainable hypothetical match simulation

`MatchSimulator` implements version 1.0.0 of the architecture's independent Poisson
baseline. It consumes normalized `Match` records and independently reviewed full
roster match counts. It is pure Python and performs no downloads. The API service
resolves teams, checks match-data hashes against coverage evidence, and invokes the
engine. No tactical percentiles are converted into probabilities.

## Evidence requirements

For each competition-season at the reviewed cutoff, require all roster teams and
exactly their expected completed-match counts, unique match IDs, distinct opponents,
and both final scores on every match. The selected team must have at least 10
matches. Reject missing scores, mixed scopes or provenance designations, a zero-goal
season baseline, or incomplete coverage. This is deliberately stricter than tactical
scoring: a selected-club subset is not a defensible league scoring baseline.

Counts and hashes verify consistency with a human-reviewed manifest, not truth or
completeness independently. Review must establish that scores exclude shootout
penalties. Both sides must use the same source and real/sample designation. No
cross-provider calibration or missing-value imputation is implemented. Source
provenance is returned for both season contexts. Event files are unnecessary for
this goals-based version; shot xG is neither required nor silently substituted.

## Strength estimates and season normalization

For each team's own season, define:

- `G`: total goals scored by both sides across all reviewed matches.
- `N`: number of reviewed matches; there are `2N` team-match appearances.
- `g = G / (2N)`: that season's mean goals per team-match.
- `M`, `GF`, `GA`: selected team's matches, goals scored, goals conceded.
- `attack = (GF / M) / g`.
- `concession = (GA / M) / g`.

Ratios equal to 1 represent the season average. An attack ratio of 1.2 means 20%
more scoring per match than that average. A concession ratio of 0.8 means 20% fewer
goals conceded: **a lower concession ratio represents stronger defense**. Using
aggregate totals gives a match-weighted baseline even with unequal team counts.
These descriptive estimates are not opponent-adjusted, time-weighted or fitted by
Poisson regression. They are not the fitted Dixon–Coles model.

For the hypothetical neutral matchup:

```text
g_ref    = (g_A + g_B) / 2
lambda_A = g_ref * attack_A * concession_B
lambda_B = g_ref * attack_B * concession_A
```

This follows the pre-existing architecture. It treats both teams' attacking and
defensive rates symmetrically and expresses each relative to its own season.
Averaging the two baseline rates defines the hypothetical scoring environment;
it is a scenario assumption, not an empirically calibrated league/era conversion.
The same relative strengths in different leagues do not establish equal quality.
Venue is always neutral; there is no invented home-advantage coefficient.

## Poisson outcomes, analytically

Let `X` and `Y` be goals for A and B. Assume independent distributions:

```text
X ~ Poisson(lambda_A), Y ~ Poisson(lambda_B)
P(X = k) = exp(-lambda_A) * lambda_A^k / k!
P(X = i, Y = j) = P(X = i) * P(Y = j)
P(A wins) = sum P(i,j) over i > j
P(draw)   = sum P(i,j) over i = j
P(B wins) = sum P(i,j) over i < j
```

The Poisson model sets both the mean and variance of each team's goals to its
lambda. Instead of randomly sampling 10,000 matches, the implementation calculates
this distribution directly, with a bounded numerical tail. It has no Monte Carlo
sampling error. The exact mean score is `(lambda_A, lambda_B)`, returned under
`average_simulated_score`; it is not a sampled or necessarily integer scoreline.

The PMF uses `p(0) = exp(-lambda)` and `p(k+1) = p(k)*lambda/(k+1)`.
At cutoff `K`, once `K+2 > lambda`, the omitted tail is bounded above by:

```text
p(K+1) / (1 - lambda/(K+2))
```

Subsequent probability ratios only decrease, so this geometric-series bound is
conservative. Increase each cutoff until its bound is at most `5e-9`; joint omitted
mass is at most `1e-8`, apart from floating-point rounding. Return that omitted mass
and both cutoffs. Divide all retained scoreline/outcome probabilities by their
retained total so outcomes sum to one. The five highest-probability positive cells
are returned, or fewer if fewer exist. Ties sort by total goals, then A's goals.
The top five probabilities are not renormalized to sum to one.

Zero lambda is handled as a point mass at zero. If both lambdas are zero, the only
scoreline is 0–0 and draw probability is one. Zero scoring/conceding rates are not
silently smoothed. Nonfinite or negative lambdas and lambdas greater than 100 are
rejected; 100 is a numerical/resource guard, not a football prior or clamped value.
No extra dependencies are needed for the recurrence.

`seed` optionally accepts integers 0 through 4294967295 and is echoed in the result.
Because the method is analytical, it is explicitly unused (`seed_used: false`).
Identical inputs always give identical probabilities, regardless of seed. There
is no hidden RNG and no arbitrary random adjustment to strengths.

## Synthetic worked example

Suppose each of two synthetic teams plays 10 matches against the other, always
finishing A 2–1 B. This is a test fixture, not real results.

- Season baseline: `30 / 20 = 1.5` goals per team-match.
- A attack: `2/1.5 = 4/3`; A concession: `1/1.5 = 2/3`.
- B attack: `2/3`; B concession: `4/3`.
- Expected A goals: `1.5 * (4/3) * (4/3) = 8/3`.
- Expected B goals: `1.5 * (2/3) * (2/3) = 2/3`.

The resulting hypothetical means need not reproduce the observed 2–1 score. They
combine each team's attack and its opponent's defense under a multiplicative model;
this simplistic two-team schedule also illustrates why opponent adjustment matters.

## Limitations and evaluation

- These are model-expected goal counts from observed scores, not event-level xG.
- Independence overlooks score-state changes and low-score correlations. Constant
  means and Poisson variance can misrepresent actual scoring variability.
- No lineup, injuries, transfers, manager changes, home advantage, time decay,
  opponent adjustment or calibrated tactical interaction is included.
- Ten matches is an explicit minimum, not evidence of statistical reliability.
  Finishing variation remains substantial. No shrinkage, parameter uncertainty or
  confidence intervals have been fitted; zeros can produce extreme outcomes.
- Final scores can include extra time; goals/match is not goals/90. This is a
  source-defined match scenario, not a guaranteed regulation-time forecast.
  Penalty shootout goals must be excluded. Duration normalization requires new data.
- Open datasets often contain selected clubs rather than a complete league. Such
  collections cannot supply the full-season baseline and are rejected.
- Cross-season ratios do not estimate league quality or era strength. Historical
  matchups cannot be validated directly against matches that never happened.

Before claiming forecasting accuracy, backtest chronologically held-out actual
matches using only earlier data and independently established counts at each cutoff.
Measure multiclass Brier score, log loss and calibration against simple season-rate
baselines. Parameter selection must use training/validation data only. No such
backtest has been performed; unit tests establish implementation correctness, not
predictive calibration.

Independent Poisson football models and their extensions are discussed in
[Crowder et al., Dynamic Modelling and Prediction of English Football League Matches
for Betting (2002)](https://academic.oup.com/jrsssd/article/51/2/157/7120674).
That literature motivates the model family; it does not validate this project's
specific ratio estimator or hypothetical cross-league assumptions.
