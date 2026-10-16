"""Preparation and fast serving checks use synthetic records, never internet."""

import pytest
from fastapi.testclient import TestClient
from app.data.fixture import FixtureFootballDataProvider
from app.data.prepare_demo import verify_schedule, verify_events
from app.data.prepared import PreparedDataset, PreparedSeason, PreparedDataProvider
from app.data.provider import DataFormatError, DataNotFoundError
from app.analytics.team_season import TeamSeasonMetrics
from app.models.api import SeasonCoverage
from app.main import create_app


def snapshot():
    provider = FixtureFootballDataProvider()
    competition = provider.get_competitions()[0]
    season = provider.get_seasons(competition.id)[0]
    matches = provider.get_matches(competition.id, season)
    teams = provider.get_teams(competition.id, season)
    coverage = SeasonCoverage(
        competition_id=competition.id,
        season_id=season.id,
        source="fixture",
        data_kind="sample",
        match_data_sha256=matches[0].provenance.sha256,
        expected_matches={t.id: 1 for t in teams},
        evidence="Synthetic test",
    )
    profiles = [TeamSeasonMetrics.calculate(t.id, season, matches, {}) for t in teams]
    return PreparedDataset(
        seasons=[
            PreparedSeason(
                competition=competition,
                season=season,
                matches=matches,
                coverage=coverage,
                profiles=profiles,
            )
        ]
    )


def test_prepared_app_loads_and_serves_without_event_access(tmp_path, monkeypatch):
    dataset = snapshot()
    path = tmp_path / "prepared.json"
    path.write_text(dataset.model_dump_json())
    monkeypatch.setenv("FOOTBALL_PREPARED_PATH", str(path))
    monkeypatch.delenv("FOOTBALL_COVERAGE_PATH", raising=False)

    def forbidden(*args):
        raise AssertionError("Prepared requests must not re-read event files")

    monkeypatch.setattr(PreparedDataProvider, "get_match_events", forbidden)
    client = TestClient(create_app())
    item = dataset.seasons[0]
    base = f"/competitions/{item.competition.id}/seasons/{item.season.id}"
    assert client.get("/dataset").json()["seasons"][0]["matches"] == 1
    assert client.get("/dataset").json()["seasons"][0]["data_kind"] == "sample"
    assert len(client.get("/competitions").json()["competitions"]) == 1
    for suffix in ["metrics", "tactical-profile"]:
        assert (
            client.get(f"{base}/teams/{item.profiles[0].team_id}/{suffix}").status_code
            == 200
        )
    assert (
        client.get(
            base.replace(item.season.id, "fixture:season:unknown") + "/teams"
        ).status_code
        == 404
    )


@pytest.mark.parametrize("change", ["version", "roster", "scope", "hash", "duplicates"])
def test_corrupt_snapshot_rejected(change):
    data = snapshot().model_dump()
    item = data["seasons"][0]
    if change == "version":
        item["profiles"][0]["metrics_version"] = "future"
    if change == "roster":
        item["profiles"].pop()
    if change == "scope":
        item["season"]["competition_id"] = "wrong"
    if change == "hash":
        item["coverage"]["match_data_sha256"] = "wrong"
    if change == "duplicates":
        data["seasons"].append(item)
    with pytest.raises(ValueError):
        PreparedDataset.model_validate(data)


def test_schedule_requires_every_ordered_pair_and_scores():
    match = snapshot().seasons[0].matches[0]
    reverse = match.model_copy(
        update={
            "id": "fixture:match:2",
            "home_team": match.away_team,
            "away_team": match.home_team,
        }
    )
    assert set(verify_schedule([match, reverse], 2).values()) == {2}
    for invalid in [
        [match],
        [match, match],
        [match, reverse.model_copy(update={"home_score": None})],
    ]:
        with pytest.raises(DataFormatError):
            verify_schedule(invalid, 2)


def test_event_review_rejects_tiny_fixture():
    item = snapshot().seasons[0]
    with pytest.raises(DataFormatError):
        verify_events(
            item.matches[0],
            FixtureFootballDataProvider().get_match_events(item.matches[0].id),
        )


def test_provider_does_not_offer_unprepared_scopes():
    provider = PreparedDataProvider(snapshot())
    with pytest.raises(DataNotFoundError):
        provider.get_seasons("statsbomb:competition:2")


def test_cache_is_inside_repository():
    from pathlib import Path
    from app.data.json_source import DEFAULT_CACHE

    assert DEFAULT_CACHE == Path(__file__).resolve().parents[2] / "data/cache/statsbomb"


def test_event_review_checks_boundaries_and_goal_reconciliation():
    from app.models.football import Event

    match = snapshot().seasons[0].matches[0]
    events = []
    for period in (1, 2):
        for kind in ("Half Start", "Half End"):
            for team in (match.home_team.id, match.away_team.id):
                events.append(
                    Event(
                        id=f"fixture:event:{len(events)}",
                        match_id=match.id,
                        index=len(events) + 1,
                        type=kind,
                        period=period,
                        minute=90 if period == 2 else 45,
                        second=0,
                        team_id=team,
                        provenance=match.provenance,
                    )
                )
    for team, score in [
        (match.home_team.id, match.home_score),
        (match.away_team.id, match.away_score),
    ]:
        for _ in range(score):
            events.append(
                Event(
                    id=f"fixture:event:{len(events)}",
                    match_id=match.id,
                    index=len(events) + 1,
                    type="Shot",
                    period=1,
                    minute=10,
                    second=0,
                    team_id=team,
                    provenance=match.provenance,
                    source_fields={"shot": {"outcome": {"name": "Goal"}}},
                )
            )
    assert verify_events(match, events) == match.provenance.sha256
    with pytest.raises(DataFormatError):
        verify_events(match, events[1:])
    with pytest.raises(DataFormatError):
        verify_events(
            match.model_copy(update={"home_score": match.home_score + 1}), events
        )


@pytest.mark.parametrize(
    "change",
    [
        "sample_match",
        "sample_catalog",
        "sample_profile",
        "missing_provenance",
        "duplicate_profile_match",
        "unknown_eligible_match",
        "unknown_event_hash",
        "nonfinite_metric",
        "wrong_ratio",
        "overlapping_coverage",
        "wrong_goal_total",
    ],
)
def test_snapshot_rejects_inconsistent_evidence(change):
    data = snapshot().model_dump()
    season = data["seasons"][0]
    profile = season["profiles"][0]
    metric = profile["metrics"]["goals_for_per_match"]
    if change == "sample_match":
        season["matches"][0]["provenance"]["data_kind"] = "real"
    if change == "sample_catalog":
        season["competition"]["provenance"]["data_kind"] = "real"
    if change == "sample_profile":
        profile["provenance"][0]["data_kind"] = "real"
    if change == "missing_provenance":
        profile["provenance"] = []
    if change == "duplicate_profile_match":
        profile["match_ids"].append(profile["match_ids"][0])
    if change == "unknown_eligible_match":
        metric["eligible_match_ids"] = ["unknown"]
    if change == "unknown_event_hash":
        season["coverage"]["complete_event_sha256"]["unknown"] = "hash"
    if change == "nonfinite_metric":
        metric["value"] = float("inf")
    if change == "wrong_ratio":
        metric["value"] = 99
    if change == "overlapping_coverage":
        metric["excluded_matches"][profile["match_ids"][0]] = "missing"
    if change == "wrong_goal_total":
        metric["value"] = 99
        metric["numerator"] = 99 * metric["denominator"]
    with pytest.raises(ValueError):
        PreparedDataset.model_validate(data)


def test_explicit_coverage_is_not_overridden_by_local_snapshot(tmp_path, monkeypatch):
    path = tmp_path / "prepared.json"
    path.write_text(snapshot().model_dump_json())
    monkeypatch.setenv("FOOTBALL_PREPARED_PATH", str(path))
    monkeypatch.delenv("FOOTBALL_COVERAGE_PATH", raising=False)
    app = create_app(coverage=[])
    assert app.state.football_service.coverage == {}
    assert app.state.football_service.prepared_profiles == {}


@pytest.mark.parametrize("change", ["missing_metric", "wrong_unit", "negative_value"])
def test_snapshot_metric_contract(change):
    data = snapshot().model_dump()
    metrics = data["seasons"][0]["profiles"][0]["metrics"]
    if change == "missing_metric":
        metrics.pop("shots_per_match")
    elif change == "wrong_unit":
        metrics["shots_per_match"]["unit"] = "shots/90"
    else:
        metrics["shots_per_match"].update(
            value=-1, numerator=-1, denominator=1, status="available"
        )
    with pytest.raises(ValueError):
        PreparedDataset.model_validate(data)
