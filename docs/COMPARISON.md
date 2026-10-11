# Cross-season team comparisons

`TeamComparisonEngine.compare(a, b)` accepts two `TacticalProfile` objects. It is
pure, deterministic Python: no provider calls, HTTP, machine learning or LLM.
`FootballService.compare` obtains both profiles through the existing provider and
reviewed coverage pipeline. Teams sharing a competition-season reuse one cohort
and event retrieval within the request. No pair-only normalization is performed.

## Three distinct differences

Every difference uses **A minus B**. Positive means a higher value for A, not that
A is better. Each entry contains `team_a`, `team_b`, `difference_a_minus_b`, `unit`,
`basis`, and a nullable `reason`.

1. **Raw context:** `delta_raw = x_A - x_B`, for available matching-unit metrics.
   Raw metrics and their denominators, eligible matches, exclusions and status are
   retained in each tactical profile's additive `raw_metrics` field. Raw deltas do
   not drive advantages, similarities or matchup observations. Higher shots in one
   season can reflect that environment rather than a stronger relative attacking
   style. Partial metrics remain contextual; inspect their coverage before use.
2. **Normalized components:** reuse the percentiles retained by the tactical model.
   For an eligible competition-season cohort of size `n`, let `r` be the ascending
   average rank (ties receive their mean rank). `P = 100 * (r - 1) / (n - 1)`.
   `delta_percentile = P_A,own_cohort - P_B,own_cohort`. The teams can come from
   different clubs, competitions and seasons. A 90 versus a 60 means a 30
   percentile-point difference in standing against their respective peers. It does
   not measure league strength or an absolute performance gap.
3. **Tactical dimensions:** `delta_score = S_A - S_B`. Each existing score is the
   equal-weight mean of its component percentiles, as specified in
   [TACTICAL_MODEL.md](TACTICAL_MODEL.md). The same seven dimensions and formulas
   are preserved; this stage introduces no scoring weights.

Only components fitted by the tactical model have normalized differences. For
example, goals and xG do not have reference ranks in this model and are explicitly
unavailable in the normalized output. `advanced_defensive_share` is the pressing
component (advanced defensive actions / total defensive actions); its raw inputs
remain separate. The model does not invent distributions for unranked metrics.

## Evidence and compatibility

The existing default requirements remain: at least 10 eligible teams, 80% of the
independently verified roster, 10 eligible matches per team, and 80% of expected
matches. Composite components use compatible within-team match sets and the same
eligible cohort. See the tactical documentation for exact eligibility checks.
Comparison also checks recorded cohort size and target membership. Profiles are
expected to come from the tactical engine; this is not a replacement for its input
validation or coverage review.

Both profiles must share source, real/sample designation, metric/model versions
(currently 1.0.0), and scoring configuration. Incompatible profiles raise
`ComparisonInputError` (HTTP 409). Cross-provider calibration is not implemented.
Same competition-season scores must use the same cohort IDs and roster counts;
otherwise that dimension is unavailable. Profiles from different seasons retain
their own cohorts. The response embeds both profiles so these references and
eligible matches remain inspectable.

Missing metrics never become zero. Missing components, insufficient cohorts or
constant reference components yield null differences with reasons and do not
produce advantages or similarities. A constant component has no discriminatory
information even though the underlying tactical model displays it as 50. A
composite containing such a component is excluded from tactical comparisons;
other nonconstant component differences can still be shown. Older profiles lacking
`raw_metrics` can still provide normalized comparisons but cannot supply raw deltas.

## Explicit interpretation rules

- Return up to three A advantages where `delta_score >= 10`, largest first, and up
  to three B advantages where `delta_score <= -10`, most negative first. Ties sort
  by category name. Report B's lead as a positive magnitude.
- A similarity requires `abs(delta_score) <= 5` on a comparable dimension.
- A possession/transition observation requires one team's possession score >=75
  and lead >=10, and the other's counterattack score >=75 and lead >=10.
- An attacking/defensive observation uses the same thresholds for attacking and
  defensive intensity. Both directional arrangements are checked.
- Otherwise explicitly report no supported contrast; when no dimensions are
  comparable, state insufficient evidence.

These are display thresholds, not statistical significance tests. “Advantage”
means **greater relative stylistic emphasis**, never better play, defensive quality,
a low block, or a prediction of winning. Text is generated from fixed rules only.

## Limitations and synthetic example

Percentiles account for relative environment, not opponent quality, era changes,
league strength, schedule imbalance, incomplete open-data selection or differences
in event annotation. Possession is a pass-share proxy and pressing is an advanced
activity-share proxy. Comparisons inherit all metric and tactical limitations.

In the synthetic tests, a team has 16 shots/match while its counterpart in another
league-season has 116. Both rank highest among their respective 11-team cohorts:
the raw difference is -100, but their shot-percentile difference is 0. These are
invented test numbers illustrating the formula, not real football statistics.

Tests also cover identical profiles, opposing possession/counter styles,
attacking/defensive activity contrasts, swapped order, missing values, constant
references, incompatible versions/sources, small cohorts and endpoint validation.
