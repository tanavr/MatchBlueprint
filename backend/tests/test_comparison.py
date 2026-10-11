"""Known synthetic contrasts; no real football claims or network access."""

import pytest

from app.analytics.comparison import ComparisonInputError, TeamComparisonEngine
from test_tactical import synthetic_cohort, result, change


def test_identical_profiles_and_determinism() -> None:
    profile = result(synthetic_cohort())
    before = profile.model_dump()
    comparison = TeamComparisonEngine.compare(profile, profile)
    assert all(d.difference_a_minus_b == 0 for d in comparison.raw_metric_differences.values())
    assert all(d.difference_a_minus_b == 0 for d in comparison.tactical_score_comparison.values())
    assert len(comparison.similarities) == 7
    assert not comparison.team_a_advantages and not comparison.team_b_advantages
    assert comparison == TeamComparisonEngine.compare(profile, profile)
    assert profile.model_dump() == before


def test_possession_vs_counterattacking_and_swapped_order() -> None:
    cohort = synthetic_cohort()
    a, b = result(cohort), result(cohort, "team-0")
    comparison = TeamComparisonEngine.compare(a, b)
    assert comparison.tactical_score_comparison["possession"].difference_a_minus_b == 100
    assert comparison.tactical_score_comparison["counterattacking_tendency"].difference_a_minus_b == -100
    assert any("possession/transition" in text for text in comparison.matchup_observations)
    reverse = TeamComparisonEngine.compare(b, a)
    assert reverse.team_a_advantages == comparison.team_b_advantages
    assert reverse.team_b_advantages == comparison.team_a_advantages
    for key, item in comparison.tactical_score_comparison.items():
        assert reverse.tactical_score_comparison[key].difference_a_minus_b == -item.difference_a_minus_b


def test_attacking_vs_defensive_activity() -> None:
    cohort = synthetic_cohort()
    change(cohort[-1], "defensive_actions_per_match", 10)
    change(cohort[0], "defensive_actions_per_match", 100)
    change(cohort[0], "advanced_defensive_actions_per_match", 5)
    comparison = TeamComparisonEngine.compare(result(cohort), result(cohort, "team-0"))
    assert comparison.tactical_score_comparison["attacking_intensity"].difference_a_minus_b == 100
    assert comparison.tactical_score_comparison["defensive_intensity"].difference_a_minus_b == -100
    assert any("does not establish defensive quality" in text for text in comparison.matchup_observations)


def test_cross_league_season_raw_shift_is_not_a_relative_advantage() -> None:
    original, shifted = synthetic_cohort(), synthetic_cohort()
    shifted = [p.model_copy(update={"competition_id": "other-league", "season_id": "other-season"})
               for p in shifted]
    for p in shifted:
        change(p, "shots_per_match", p.metrics["shots_per_match"].value + 100)
    comparison = TeamComparisonEngine.compare(result(original), result(shifted))
    assert comparison.raw_metric_differences["shots_per_match"].difference_a_minus_b == -100
    assert comparison.normalized_metric_differences["shots_per_match"].difference_a_minus_b == 0
    assert comparison.tactical_score_comparison["attacking_intensity"].difference_a_minus_b == 0
    assert not comparison.team_a_advantages and not comparison.team_b_advantages


def test_missing_metrics_are_not_zero_or_advantages() -> None:
    cohort = synthetic_cohort()
    del cohort[-1].metrics["pass_completion_pct"]
    comparison = TeamComparisonEngine.compare(result(cohort), result(cohort, "team-0"))
    for mapping, key in ((comparison.raw_metric_differences, "pass_completion_pct"),
                         (comparison.normalized_metric_differences, "pass_completion_pct"),
                         (comparison.tactical_score_comparison, "passing_control")):
        assert mapping[key].difference_a_minus_b is None
        assert mapping[key].reason
    assert all(a.category != "passing_control" for a in comparison.team_b_advantages)
    assert comparison.normalized_metric_differences["advanced_defensive_actions_per_match"].difference_a_minus_b is None


def test_constant_reference_does_not_create_similarity() -> None:
    cohort = synthetic_cohort()
    for p in cohort:
        change(p, "shots_per_match", 10)
    comparison = TeamComparisonEngine.compare(result(cohort), result(cohort, "team-0"))
    assert comparison.tactical_score_comparison["attacking_intensity"].difference_a_minus_b is None
    assert comparison.normalized_metric_differences["shots_per_match"].difference_a_minus_b is None
    assert not any("attacking intensity" in text for text in comparison.similarities)


def test_same_season_different_reference_sets_are_not_comparable() -> None:
    a = result(synthetic_cohort())
    b = a.model_copy(deep=True)
    b.scores["possession"].cohort_team_ids.remove("team-0")
    comparison = TeamComparisonEngine.compare(a, b)
    assert comparison.tactical_score_comparison["possession"].difference_a_minus_b is None


@pytest.mark.parametrize("field,value", [("source", "other"), ("data_kind", "real"),
                                         ("model_version", "2.0.0"), ("metrics_version", "2.0.0")])
def test_incompatible_profiles_rejected(field: str, value: str) -> None:
    a = result(synthetic_cohort())
    with pytest.raises(ComparisonInputError):
        TeamComparisonEngine.compare(a, a.model_copy(update={field: value}))


def test_insufficient_cohort_has_no_claims() -> None:
    a = result(synthetic_cohort()[:9], "team-5")
    comparison = TeamComparisonEngine.compare(a, a)
    assert not comparison.similarities
    assert not comparison.team_a_advantages and not comparison.team_b_advantages
    assert all(d.difference_a_minus_b is None for d in comparison.tactical_score_comparison.values())


def test_raw_unit_mismatch_and_nonfinite_values_are_unavailable() -> None:
    a = result(synthetic_cohort())
    b = a.model_copy(deep=True)
    for name, updates in (("shots_per_match", {"unit": "shots/90"}),
                          ("passes_per_possession", {"value": float("nan")})):
        b.raw_metrics[name] = b.raw_metrics[name].model_copy(update=updates)
    comparison = TeamComparisonEngine.compare(a, b)
    assert comparison.raw_metric_differences["shots_per_match"].reason == "Raw metric units differ"
    assert comparison.raw_metric_differences["shots_per_match"].difference_a_minus_b is None
    assert comparison.raw_metric_differences["passes_per_possession"].team_b is None


def test_different_scoring_settings_rejected() -> None:
    a = result(synthetic_cohort())
    b = a.model_copy(update={"config": a.config.model_copy(update={"min_matches": 5})})
    with pytest.raises(ComparisonInputError):
        TeamComparisonEngine.compare(a, b)


def test_advantage_and_similarity_boundaries() -> None:
    a = result(synthetic_cohort(), "team-5")
    b = a.model_copy(deep=True)
    # Isolate the interpretation rules using controlled score differences.
    b.scores["possession"] = b.scores["possession"].model_copy(update={"value": 40})
    b.scores["directness"] = b.scores["directness"].model_copy(update={"value": 40.01})
    b.scores["passing_control"] = b.scores["passing_control"].model_copy(update={"value": 45})
    comparison = TeamComparisonEngine.compare(a, b)
    assert [adv.category for adv in comparison.team_a_advantages] == ["possession"]
    assert any("passing control" in text for text in comparison.similarities)
    assert not any("directness" in text for text in comparison.similarities)
