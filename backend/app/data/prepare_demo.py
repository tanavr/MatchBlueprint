"""Prepare a complete double-round-robin open league, never during API requests."""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import os
from pathlib import Path
import tempfile

from app.analytics.team_season import TeamSeasonMetrics
from app.data.json_source import CachedJSONSource
from app.data.prepared import DEFAULT_SNAPSHOT, PreparedDataset, PreparedSeason
from app.data.provider import DataFormatError, DataProviderError
from app.data.statsbomb import StatsBombOpenDataProvider, raw_id
from app.models.api import SeasonCoverage
from app.models.football import Event, Match
from app.models.metrics import MatchEvents


def verify_schedule(matches: list[Match], expected_teams: int) -> dict[str, int]:
    teams = {t.id for m in matches for t in (m.home_team, m.away_team)}
    pairs = Counter((m.home_team.id, m.away_team.id) for m in matches)
    if (len(teams) != expected_teams or len(pairs) != expected_teams * (expected_teams - 1)
            or any(count != 1 or a == b for (a, b), count in pairs.items())
            or any(m.home_score is None or m.away_score is None for m in matches)):
        raise DataFormatError("Expected a complete double round robin with known final scores")
    return {team: 2 * (expected_teams - 1) for team in sorted(teams)}


def verify_events(match: Match, events: list[Event]) -> str:
    # Structural checks are an operational completeness check, not an assertion
    # that a human annotator captured every football action without error.
    teams = {match.home_team.id, match.away_team.id}
    if not events or {e.period for e in events} != {1, 2}:
        raise DataFormatError(f"{match.id}: expected two regulation periods")
    for period in (1, 2):
        for kind in ("Half Start", "Half End"):
            if {e.team_id for e in events if e.type == kind and e.period == period} != teams:
                raise DataFormatError(f"{match.id}: missing half boundary records")
    if max(e.minute for e in events if e.period == 2) < 90:
        raise DataFormatError(f"{match.id}: second half ends before 90 minutes")
    goals = Counter(e.team_id for e in events if e.type == "Own Goal For" or
                    (e.type == "Shot" and e.source_fields.get("shot", {}).get("outcome", {}).get("name") == "Goal"))
    if goals[match.home_team.id] != match.home_score or goals[match.away_team.id] != match.away_score:
        raise DataFormatError(f"{match.id}: event goals disagree with final score")
    return events[0].provenance.sha256


def prepare(competition_id: str, season_id: str, expected_teams: int, output: Path) -> None:
    source = CachedJSONSource()
    provider = StatsBombOpenDataProvider(source)
    competition = next(c for c in provider.get_competitions() if c.id == competition_id)
    season = next(s for s in provider.get_seasons(competition_id) if s.id == season_id)
    matches = provider.get_matches(competition_id, season)
    expected = verify_schedule(matches, expected_teams)
    print(f"Preparing {competition.name} {season.name}: {len(matches)} matches, {len(expected)} clubs", flush=True)

    def download(match: Match) -> None:
        for attempt in range(3):
            try:
                source.read(f"events/{raw_id('match', match.id)}.json")
                return
            except DataProviderError:
                if attempt == 2:
                    raise
    with ThreadPoolExecutor(max_workers=4) as pool:
        for i, _ in enumerate(pool.map(download, matches), 1):
            if i % 20 == 0:
                print(f"Cached {i}/{len(matches)} event files", flush=True)
    hashes = {}
    profiles = []
    # Keep only one team's events in memory at a time.
    for team in expected:
        selected = [m for m in matches if team in (m.home_team.id, m.away_team.id)]
        feeds = {}
        for match in selected:
            events = provider.get_match_events(match.id)
            hashes[match.id] = verify_events(match, events)
            feeds[match.id] = MatchEvents(events=events, complete=True)
        profiles.append(TeamSeasonMetrics.calculate(team, season, selected, feeds))
        print(f"Calculated club {len(profiles)}/{len(expected)}", flush=True)
    coverage = SeasonCoverage(competition_id=competition_id, season_id=season_id,
        source="statsbomb", data_kind="real", match_data_sha256=matches[0].provenance.sha256,
        complete_event_sha256=hashes, expected_matches=expected,
        evidence=f"Configured {expected_teams}-club double round robin; verified each ordered pairing once, final scores, both half boundaries and event goal reconciliation. See docs/REAL_DATA.md.")
    prepared = PreparedSeason(competition=competition, season=season, matches=matches, coverage=coverage, profiles=profiles)
    existing = PreparedDataset.model_validate_json(output.read_text()).seasons if output.exists() else []
    dataset = PreparedDataset(seasons=[s for s in existing if (s.competition.id, s.season.id) != (competition_id, season_id)] + [prepared])
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", dir=output.parent, delete=False) as handle:
        handle.write(dataset.model_dump_json())
        temporary = handle.name
    os.replace(temporary, output)
    print(f"Ready: {output}. Restart the backend to load this snapshot.", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--competition", default="statsbomb:competition:2")
    parser.add_argument("--season", default="statsbomb:season:27")
    parser.add_argument("--expected-teams", type=int, default=20)
    parser.add_argument("--output", type=Path, default=DEFAULT_SNAPSHOT)
    args = parser.parse_args()
    try:
        prepare(args.competition, args.season, args.expected_teams, args.output)
    except (DataProviderError, ValueError, StopIteration, OSError) as exc:
        parser.exit(1, f"Preparation failed; previous snapshot retained: {exc}\n")


if __name__ == "__main__":
    main()
