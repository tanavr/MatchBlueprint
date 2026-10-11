"""Synthetic score datasets with known strengths and probability invariants."""
from math import exp, factorial, fsum

import pytest
from fastapi.testclient import TestClient

from app.analytics.simulation import MatchSimulator, SimulationInputError, poisson_probabilities, team_strength
from app.data.fixture import FixtureFootballDataProvider
from app.main import create_app
from app.models.football import Event, Match, Season
from app.models.simulation import MatchSimulation
from test_api import comparison_params, coverage


def schedule(home: int = 2, away: int = 1, season: str = "fixture:season:1") -> list[Match]:
    base = FixtureFootballDataProvider()._match
    return [base.model_copy(update={"id": f"fixture:match:{i}", "home_score": home,
                                    "away_score": away, "season_id": season}) for i in range(10)]


ROSTER = {"fixture:team:1": 10, "fixture:team:2": 10}


def simulate(a: list[Match], b: list[Match], seed: int = 42) -> MatchSimulation:
    return MatchSimulator.simulate("fixture:team:1", a, ROSTER, "fixture:team:2", b, ROSTER, seed)


def test_known_strengths_and_expected_goals() -> None:
    result = simulate(schedule(), schedule())
    assert result.team_a.season_goals_per_team_match == 1.5
    assert result.team_a.attack_ratio == pytest.approx(4 / 3)
    assert result.team_a.concession_ratio == pytest.approx(2 / 3)
    assert result.expected_goals_a == pytest.approx(8 / 3)
    assert result.expected_goals_b == pytest.approx(2 / 3)
    assert result.team_a_win_probability > result.team_b_win_probability
    assert result.average_simulated_score.team_a == result.expected_goals_a
    assert result.average_simulated_score.team_b == result.expected_goals_b


def test_equal_teams_symmetry_and_reproducibility() -> None:
    first = simulate(schedule(1, 1), schedule(1, 1))
    assert first == simulate(schedule(1, 1), schedule(1, 1))
    assert first.team_a_win_probability == pytest.approx(first.team_b_win_probability)
    changed_seed = simulate(schedule(1, 1), schedule(1, 1), seed=123)
    assert first.model_dump(exclude={"seed"}) == changed_seed.model_dump(exclude={"seed"})
    assert not first.seed_used


def test_swap_symmetry() -> None:
    a, b = schedule(3, 2), schedule(1, 2, "other")
    forward = simulate(a, b)
    reverse = MatchSimulator.simulate("fixture:team:2", b, ROSTER, "fixture:team:1", a, ROSTER)
    assert forward.expected_goals_a == reverse.expected_goals_b
    assert forward.team_a_win_probability == pytest.approx(reverse.team_b_win_probability)
    assert forward.draw_probability == pytest.approx(reverse.draw_probability)


def test_cross_season_context_uses_own_baselines() -> None:
    result = simulate(schedule(1, 1), schedule(3, 3, "other"))
    assert result.team_a.attack_ratio == result.team_b.attack_ratio == 1
    assert result.reference_goals_per_team_match == 2
    assert result.expected_goals_a == result.expected_goals_b == 2


@pytest.mark.parametrize("mean", [0, .001, .5, 1, 3, 10, 100])
def test_poisson_pmf_and_tail(mean: float) -> None:
    probabilities = poisson_probabilities(mean)
    assert all(p >= 0 for p in probabilities)
    assert 0 <= 1 - fsum(probabilities) <= 5e-9 + 1e-14
    for k, actual in enumerate(probabilities[:20]):
        assert actual == pytest.approx(exp(-mean) * mean**k / factorial(k))


def test_probability_mass_scorelines_and_analytic_reference() -> None:
    result = simulate(schedule(1, 1), schedule(1, 1))
    assert fsum([result.team_a_win_probability, result.draw_probability, result.team_b_win_probability]) == pytest.approx(1)
    exact_draw = fsum(exp(-2) / factorial(k)**2 for k in range(25))
    assert result.draw_probability == pytest.approx(exact_draw, abs=1e-8)
    assert result.omitted_probability_mass <= 1e-8
    probs = [s.probability for s in result.most_likely_scorelines]
    assert probs == sorted(probs, reverse=True)
    assert len(probs) == 5
    assert all(0 <= p <= 1 for p in probs)


def test_zero_means_yield_certain_nil_nil() -> None:
    # Positive league baselines; each selected team has scored no goals.
    result = simulate(schedule(0, 1), schedule(1, 0, "other"))
    assert result.expected_goals_a == result.expected_goals_b == 0
    assert result.draw_probability == 1
    assert result.team_a_win_probability == result.team_b_win_probability == 0
    assert len(result.most_likely_scorelines) == 1
    assert result.most_likely_scorelines[0].goals_a == 0


@pytest.mark.parametrize("case", ["missing", "duplicate", "incomplete", "zero_baseline", "mixed_scope", "same_team"])
def test_bad_season_evidence_rejected(case: str) -> None:
    matches = schedule()
    if case == "missing":
        matches[0] = matches[0].model_copy(update={"home_score": None})
    elif case == "duplicate":
        matches[1] = matches[0]
    elif case == "incomplete":
        matches.pop()
    elif case == "zero_baseline":
        matches = schedule(0, 0)
    elif case == "mixed_scope":
        matches[0] = matches[0].model_copy(update={"season_id": "other"})
    else:
        matches[0] = matches[0].model_copy(update={"away_team": matches[0].home_team})
    with pytest.raises(SimulationInputError):
        simulate(matches, schedule())


def test_small_sample_and_unobserved_roster_rejected() -> None:
    with pytest.raises(SimulationInputError, match="10 scored"):
        team_strength("fixture:team:1", schedule()[:9], {k: 9 for k in ROSTER})
    with pytest.raises(SimulationInputError, match="full roster"):
        team_strength("fixture:team:1", schedule(), {**ROSTER, "unseen": 10})


def test_mixed_source_or_data_kind_rejected() -> None:
    for updates in ({"source": "other"}, {"data_kind": "real"}):
        matches = [m.model_copy(update={"provenance": m.provenance.model_copy(update=updates)}) for m in schedule()]
        with pytest.raises(SimulationInputError):
            simulate(schedule(), matches)


@pytest.mark.parametrize("mean", [-1, float("nan"), float("inf"), 101])
def test_invalid_poisson_means(mean: float) -> None:
    with pytest.raises(SimulationInputError):
        poisson_probabilities(mean)


class ScoredSeasonProvider(FixtureFootballDataProvider):
    def get_matches(self, competition: str, season: Season) -> list[Match]:
        self.validate_season(competition, season)
        return schedule()

    def get_match_events(self, match_id: str) -> list[Event]:
        pytest.fail("Simulation must not fetch events")


def test_simulation_api_and_openapi() -> None:
    manifest = coverage().model_copy(update={"expected_matches": ROSTER})
    with TestClient(create_app(ScoredSeasonProvider(), [manifest])) as client:
        params = {**comparison_params(), "seed": 42}
        response = client.get("/simulate", params=params)
        assert response.status_code == 200
        body = response.json()
        assert body["expected_goals_a"] == pytest.approx(8 / 3)
        assert body["data_kind"] == "sample"
        assert body["seed"] == 42
        assert response.json() == client.get("/simulate", params=params).json()
        schema = client.get("/openapi.json").json()
        assert schema["paths"]["/simulate"]["get"]["responses"]["200"]["content"]["application/json"]["schema"]["$ref"].endswith("MatchSimulation")
        for field, value, status in [("seed", -1, 422), ("seed", 2**32, 422), ("team_b", "unknown", 404),
                                     ("season_b", "unknown", 404), ("team_a", "bad id", 422)]:
            assert client.get("/simulate", params={**params, field: value}).status_code == status
        assert client.get("/simulate").status_code == 422


def test_api_incomplete_or_unreviewed_data() -> None:
    with TestClient(create_app(FixtureFootballDataProvider(), [coverage()])) as client:
        response = client.get("/simulate", params=comparison_params())
        assert response.status_code == 409
        assert response.json()["error"]["code"] == "simulation_unavailable"
    with TestClient(create_app(ScoredSeasonProvider())) as client:
        response = client.get("/simulate", params=comparison_params())
        assert response.status_code == 409
        assert response.json()["error"]["code"] == "coverage_not_verified"


def test_one_zero_mean_has_closed_form_outcomes() -> None:
    result = simulate(schedule(0, 1), schedule(0, 1, "other"))
    assert result.expected_goals_a == 0
    assert result.expected_goals_b == 2
    assert result.team_a_win_probability == 0
    assert result.draw_probability == pytest.approx(exp(-2), abs=1e-8)
    assert result.team_b_win_probability == pytest.approx(1 - exp(-2), abs=1e-8)


def test_input_order_does_not_change_result() -> None:
    assert simulate(schedule(), schedule()) == simulate(list(reversed(schedule())), list(reversed(schedule())))


@pytest.mark.parametrize("seed", [-1, 2**32, 1.5, True])
def test_invalid_seed_rejected(seed: object) -> None:
    with pytest.raises(SimulationInputError, match="Seed"):
        MatchSimulator.simulate("fixture:team:1", schedule(), ROSTER,
                                "fixture:team:2", schedule(), ROSTER, seed=seed)


def test_api_stale_review_cannot_generate_probabilities() -> None:
    manifest = coverage().model_copy(update={"expected_matches": ROSTER, "match_data_sha256": "stale"})
    with TestClient(create_app(ScoredSeasonProvider(), [manifest])) as client:
        response = client.get("/simulate", params=comparison_params())
        assert response.status_code == 409
        assert response.json()["error"]["code"] == "coverage_not_verified"


def test_baseline_uses_total_team_appearances_not_unweighted_rates() -> None:
    matches = schedule()
    base = matches[0]
    third = base.home_team.model_copy(update={"id": "fixture:team:3"})
    matches.append(base.model_copy(update={"id": "extra", "away_team": third, "home_score": 10, "away_score": 0}))
    strength = team_strength("fixture:team:1", matches,
                             {"fixture:team:1": 11, "fixture:team:2": 10, "fixture:team:3": 1})
    assert strength.season_goals_per_team_match == pytest.approx(40 / 22)
    assert strength.goals_for_per_match == pytest.approx(30 / 11)
