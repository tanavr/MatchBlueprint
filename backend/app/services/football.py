from typing import Optional, Sequence

from app.analytics.comparison import TeamComparisonEngine
from app.analytics.simulation import MatchSimulator
from app.models.simulation import MatchSimulation
from app.analytics.tactical import TacticalStyleModel
from app.analytics.team_season import TeamSeasonMetrics
from app.data.provider import DataNotFoundError, FootballDataProvider
from app.models.api import CompetitionList, SeasonCoverage, SeasonList, TeamList
from app.models.comparison import TeamComparison
from app.models.football import Match, Season
from app.models.metrics import MatchEvents, TeamSeasonProfile
from app.models.tactical import TacticalProfile


class CoverageConflictError(ValueError):
    """Verified coverage is absent, stale, or incompatible with the data."""


class FootballService:
    def __init__(self, provider: FootballDataProvider,
                 coverage: Sequence[SeasonCoverage] = (), *,
                 prepared_profiles: Optional[dict[tuple[str, str], list[TeamSeasonProfile]]] = None) -> None:
        self.prepared_profiles = prepared_profiles or {}
        self.provider = provider
        self.coverage = {(c.competition_id, c.season_id): c for c in coverage}
        if len(self.coverage) != len(coverage):
            raise ValueError("Duplicate competition-season coverage entries")

    def competitions(self) -> CompetitionList:
        return CompetitionList(competitions=self.provider.get_competitions())

    def seasons(self, competition_id: str) -> SeasonList:
        if competition_id not in {c.id for c in self.provider.get_competitions()}:
            raise DataNotFoundError("Competition is not available from the configured provider")
        return SeasonList(competition_id=competition_id, seasons=self.provider.get_seasons(competition_id))

    def _season(self, competition_id: str, season_id: str) -> Season:
        for season in self.seasons(competition_id).seasons:
            if season.id == season_id:
                return season
        raise DataNotFoundError("Season is not available within this competition")

    def teams(self, competition_id: str, season_id: str) -> TeamList:
        season = self._season(competition_id, season_id)
        return TeamList(competition_id=competition_id, season_id=season_id,
                        teams=self.provider.get_teams(competition_id, season))

    def _context(self, competition_id: str, season_id: str, team_id: str
                 ) -> tuple[Season, list[Match], Optional[SeasonCoverage]]:
        season = self._season(competition_id, season_id)
        matches = self.provider.get_matches(competition_id, season)
        if not any(team_id in {m.home_team.id, m.away_team.id} for m in matches):
            raise DataNotFoundError("Team is not present in this competition-season's available matches")
        coverage = self.coverage.get((competition_id, season_id))
        if coverage:
            if any((m.provenance.source, m.provenance.data_kind, m.provenance.sha256) !=
                   (coverage.source, coverage.data_kind, coverage.match_data_sha256) for m in matches):
                raise CoverageConflictError("Coverage evidence does not match the current match dataset; review it again")
        return season, matches, coverage

    def _feeds(self, matches: list[Match], coverage: Optional[SeasonCoverage]) -> dict[str, MatchEvents]:
        feeds = {}
        if coverage is None:
            return feeds
        for match in matches:
            expected_hash = coverage.complete_event_sha256.get(match.id)
            if expected_hash is None:
                continue
            events = self.provider.get_match_events(match.id)
            if not events or any((e.provenance.source, e.provenance.data_kind, e.provenance.sha256) !=
                                 (coverage.source, coverage.data_kind, expected_hash) for e in events):
                raise CoverageConflictError("A reviewed event feed is empty or has changed; review its completeness again")
            feeds[match.id] = MatchEvents(events=events, complete=True)
        return feeds

    def metrics(self, competition_id: str, season_id: str, team_id: str) -> TeamSeasonProfile:
        season, matches, coverage = self._context(competition_id, season_id, team_id)
        prepared = self.prepared_profiles.get((competition_id, season_id))
        if prepared is not None:
            return next(p for p in prepared if p.team_id == team_id)
        selected = [m for m in matches if team_id in {m.home_team.id, m.away_team.id}]
        return TeamSeasonMetrics.calculate(team_id, season, selected, self._feeds(selected, coverage))

    def tactical_profile(self, competition_id: str, season_id: str, team_id: str) -> TacticalProfile:
        cohort, expected = self._tactical_inputs(competition_id, season_id, team_id)
        return TacticalStyleModel().score(team_id, cohort, expected)

    def simulate(self, competition_a: str, season_a: str, team_a: str,
                 competition_b: str, season_b: str, team_b: str,
                 seed: Optional[int] = None) -> MatchSimulation:
        contexts = {}
        inputs = []
        for competition, season, team in ((competition_a, season_a, team_a),
                                          (competition_b, season_b, team_b)):
            scope = (competition, season)
            if scope not in contexts:
                contexts[scope] = self._context(competition, season, team)
            _, matches, coverage = contexts[scope]
            if not any(team in {m.home_team.id, m.away_team.id} for m in matches):
                raise DataNotFoundError("Team is not present in this competition-season")
            if coverage is None or not coverage.expected_matches:
                raise CoverageConflictError("Simulation requires a reviewed full roster and expected match counts")
            inputs.append((team, matches, coverage.expected_matches))
        return MatchSimulator.simulate(*inputs[0], *inputs[1], seed=seed)

    def compare(self, competition_a: str, season_a: str, team_a: str,
                competition_b: str, season_b: str, team_b: str) -> TeamComparison:
        # Reuse the cohort within this request when both teams share a season.
        inputs = {}
        profiles = []
        for competition, season, team in ((competition_a, season_a, team_a),
                                          (competition_b, season_b, team_b)):
            scope = (competition, season)
            if scope not in inputs:
                inputs[scope] = self._tactical_inputs(competition, season, team)
            cohort, expected = inputs[scope]
            if team not in {p.team_id for p in cohort}:
                raise DataNotFoundError("Team is not present in this competition-season's available matches")
            profiles.append(TacticalStyleModel().score(team, cohort, expected))
        return TeamComparisonEngine.compare(*profiles)

    def _tactical_inputs(self, competition_id: str, season_id: str, team_id: str
                         ) -> tuple[list[TeamSeasonProfile], dict[str, int]]:
        season, matches, coverage = self._context(competition_id, season_id, team_id)
        if coverage is None or not coverage.expected_matches:
            raise CoverageConflictError("Tactical scoring requires a reviewed full roster and expected completed-match counts")
        prepared = self.prepared_profiles.get((competition_id, season_id))
        if prepared is not None:
            return prepared, coverage.expected_matches
        teams = sorted({t.id for m in matches for t in (m.home_team, m.away_team)})
        if not set(teams) <= set(coverage.expected_matches):
            raise CoverageConflictError("Reviewed roster does not include all observed teams")
        feeds = self._feeds(matches, coverage)
        cohort = []
        for team in teams:
            selected = [m for m in matches if team in {m.home_team.id, m.away_team.id}]
            if len(selected) > coverage.expected_matches[team]:
                raise CoverageConflictError("Observed match count exceeds the reviewed expected count")
            selected_feeds = {m.id: feeds[m.id] for m in selected if m.id in feeds}
            cohort.append(TeamSeasonMetrics.calculate(team, season, selected, selected_feeds))
        return cohort, coverage.expected_matches
