"""A validated local snapshot for fast, offline application serving."""
from pathlib import Path

from pydantic import BaseModel, model_validator

from app.data.provider import DataNotFoundError
from app.data.statsbomb import StatsBombOpenDataProvider
from app.data.json_source import CachedJSONSource
from app.models.api import SeasonCoverage
from app.models.football import Competition, Match, Season
from app.models.metrics import TeamSeasonProfile

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
        for match in self.matches:
            if ((match.competition_id, match.season_id) != scope or
                    match.provenance.sha256 != self.coverage.match_data_sha256):
                raise ValueError("Snapshot match provenance mismatch")
        for profile in self.profiles:
            ids = {m.id for m in self.matches if profile.team_id in (m.home_team.id, m.away_team.id)}
            if ((profile.competition_id, profile.season_id) != scope or profile.metrics_version != "1.0.0"
                    or set(profile.match_ids) != ids or profile.matches_played != len(ids)
                    or len(ids) != roster[profile.team_id]):
                raise ValueError("Snapshot profile scope, version or coverage mismatch")
        return self


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
