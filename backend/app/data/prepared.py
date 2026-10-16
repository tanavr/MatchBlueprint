"""A validated local snapshot for fast, offline application serving."""
from pathlib import Path
from math import isclose, isfinite

from pydantic import BaseModel, model_validator

from app.data.provider import DataNotFoundError
from app.data.statsbomb import StatsBombOpenDataProvider
from app.data.json_source import CachedJSONSource
from app.models.api import SeasonCoverage
from app.models.football import Competition, Match, Season
from app.models.metrics import TeamSeasonProfile
from app.analytics.team_season import TeamSeasonMetrics, UNITS

DEFAULT_SNAPSHOT = Path(__file__).resolve().parents[3] / "data" / "prepared.json"


class PreparedSeason(BaseModel):
    competition: Competition
    season: Season
    matches: list[Match]
    coverage: SeasonCoverage
    profiles: list[TeamSeasonProfile]

    @model_validator(mode="after")
    def consistent(self) -> "PreparedSeason":
        scope = (self.competition.id, self.season.id)
        if self.season.competition_id != scope[0] or scope != (self.coverage.competition_id, self.coverage.season_id):
            raise ValueError("Snapshot scope mismatch")
        roster = self.coverage.expected_matches or {}
        if not roster or {p.team_id for p in self.profiles} != set(roster) or len(self.profiles) != len(roster):
            raise ValueError("Snapshot profiles must cover the reviewed roster")
        if len({m.id for m in self.matches}) != len(self.matches):
            raise ValueError("Duplicate snapshot matches")
        match_ids = {m.id for m in self.matches}
        if set(self.coverage.complete_event_sha256) - match_ids:
            raise ValueError("Event coverage references unknown matches")
        observed_teams = {t.id for m in self.matches for t in (m.home_team, m.away_team)}
        if observed_teams != set(roster):
            raise ValueError("Snapshot roster differs from match teams")
        provenance = [self.competition.provenance, self.season.provenance]
        for match in self.matches:
            provenance.extend([match.provenance, match.home_team.provenance, match.away_team.provenance])
            if match.home_team.id == match.away_team.id or match.home_score is None or match.away_score is None:
                raise ValueError("Prepared matches need distinct teams and final scores")
            if ((match.competition_id, match.season_id) != scope or
                    match.provenance.sha256 != self.coverage.match_data_sha256):
                raise ValueError("Snapshot match provenance mismatch")
        for profile in self.profiles:
            ids = {m.id for m in self.matches if profile.team_id in (m.home_team.id, m.away_team.id)}
            if ((profile.competition_id, profile.season_id) != scope or profile.metrics_version != "1.0.0"
                    or set(profile.match_ids) != ids or len(profile.match_ids) != len(ids)
                    or profile.matches_played != len(ids)
                    or len(ids) != roster[profile.team_id]):
                raise ValueError("Snapshot profile scope, version or coverage mismatch")
            if not profile.provenance:
                raise ValueError("Snapshot profile provenance is required")
            provenance.extend(profile.provenance)
            allowed_hashes = {self.season.provenance.sha256, self.coverage.match_data_sha256}
            allowed_hashes.update(self.coverage.complete_event_sha256[mid] for mid in ids
                                  if mid in self.coverage.complete_event_sha256)
            if any(p.sha256 not in allowed_hashes for p in profile.provenance):
                raise ValueError("Profile provenance is outside reviewed coverage")
            self._validate_metrics(profile, ids)
        expected_source = (self.coverage.source, self.coverage.data_kind)
        if any((p.source, p.data_kind) != expected_source for p in provenance):
            raise ValueError("Snapshot mixes sources or real/sample records")
        return self

    def _validate_metrics(self, profile: TeamSeasonProfile, ids: set[str]) -> None:
        if set(profile.metrics) != set(UNITS) | {"high_turnovers_per_match"}:
            raise ValueError("Snapshot metrics do not match the engine version")
        for name, metric in profile.metrics.items():
            eligible = set(metric.eligible_match_ids)
            excluded = set(metric.excluded_matches)
            if (len(eligible) != len(metric.eligible_match_ids) or eligible & excluded
                    or not (eligible | excluded) <= ids):
                raise ValueError("Invalid metric coverage identifiers")
            numbers = [metric.numerator, metric.denominator]
            if metric.value is not None:
                numbers.append(metric.value)
            if not all(isfinite(n) for n in numbers) or metric.denominator < 0:
                raise ValueError("Metric values must be finite with nonnegative denominators")
            if name in UNITS and metric.unit != UNITS[name]:
                raise ValueError("Metric units do not match the engine")
            if metric.value is not None:
                if name != "net_forward_progression_per_pass" and metric.value < 0:
                    raise ValueError("Count, rate and distance metrics cannot be negative")
                if name.endswith("_pct") and metric.value > 100:
                    raise ValueError("Percentage metrics cannot exceed 100")
            if metric.status == "unavailable":
                if metric.value is not None:
                    raise ValueError("Unavailable metric has a value")
                continue
            if (metric.value is None or metric.denominator <= 0 or not eligible
                    or not isclose(metric.value, metric.numerator / metric.denominator,
                                   rel_tol=1e-9, abs_tol=1e-9)):
                raise ValueError("Metric value disagrees with its totals")
            if metric.status != ("partial" if excluded else "available") or eligible | excluded != ids:
                raise ValueError("Metric status or coverage is incomplete")
            if name.endswith("_per_match") and metric.denominator != len(eligible):
                raise ValueError("Per-match denominator disagrees with coverage")
            if not name.startswith("goals_") and not eligible <= set(self.coverage.complete_event_sha256):
                raise ValueError("Event metric lacks reviewed event coverage")
        # Scores are inexpensive to recompute and must agree with the cached rates.
        selected = [m for m in self.matches if m.id in ids]
        expected = TeamSeasonMetrics.calculate(profile.team_id, self.season, selected, {})
        for name in ("goals_for_per_match", "goals_against_per_match"):
            if profile.metrics.get(name) != expected.metrics[name]:
                raise ValueError("Cached goal metric disagrees with match scores")


class PreparedDataset(BaseModel):
    format_version: int = 1
    seasons: list[PreparedSeason]

    @model_validator(mode="after")
    def unique(self) -> "PreparedDataset":
        if self.format_version != 1 or not self.seasons:
            raise ValueError("Unsupported or empty prepared dataset")
        scopes = {(s.competition.id, s.season.id) for s in self.seasons}
        if len(scopes) != len(self.seasons):
            raise ValueError("Duplicate prepared seasons")
        return self


class PreparedDataProvider(StatsBombOpenDataProvider):
    """Expose only prepared scopes; event retrieval remains available from disk."""
    def __init__(self, dataset: PreparedDataset) -> None:
        super().__init__(CachedJSONSource(offline=True))
        self.dataset = dataset

    def get_competitions(self) -> list[Competition]:
        return list({s.competition.id: s.competition for s in self.dataset.seasons}.values())

    def get_seasons(self, competition: str) -> list[Season]:
        seasons = [s.season for s in self.dataset.seasons if s.competition.id == competition]
        if not seasons:
            raise DataNotFoundError("Competition has not been prepared")
        return seasons

    def get_matches(self, competition: str, season: Season) -> list[Match]:
        self.validate_season(competition, season)
        for item in self.dataset.seasons:
            if (competition, season.id) == (item.competition.id, item.season.id):
                return item.matches
        raise DataNotFoundError("Season has not been prepared")
