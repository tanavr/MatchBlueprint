"""Independent Poisson baseline; no I/O, tactical multipliers or fitted claims."""
from collections import Counter
from math import exp, fsum, isfinite
from typing import Optional, Sequence

from app.models.football import Match
from app.models.simulation import AverageScore, MatchSimulation, Scoreline, TeamGoalStrength


class SimulationInputError(ValueError):
    """Required score evidence is incomplete, incompatible or unsupported."""


def team_strength(team_id: str, matches: Sequence[Match],
                  expected_matches: dict[str, int]) -> TeamGoalStrength:
    """Normalize selected-team goal rates against a complete reviewed season."""
    if not matches or not expected_matches:
        raise SimulationInputError("A complete reviewed season roster and score dataset are required")
    if len({m.id for m in matches}) != len(matches):
        raise SimulationInputError("Duplicate match IDs")
    scopes = {(m.competition_id, m.season_id, m.provenance.source, m.provenance.data_kind) for m in matches}
    if len(scopes) != 1:
        raise SimulationInputError("Season records must share competition, season, source and data designation")
    counts: Counter[str] = Counter()
    total_goals = goals_for = goals_against = played = 0
    for match in matches:
        if match.home_team.id == match.away_team.id or match.home_score is None or match.away_score is None:
            raise SimulationInputError("Every match requires distinct teams and both final scores")
        counts.update((match.home_team.id, match.away_team.id))
        total_goals += match.home_score + match.away_score
        if team_id in (match.home_team.id, match.away_team.id):
            home = team_id == match.home_team.id
            goals_for += match.home_score if home else match.away_score
            goals_against += match.away_score if home else match.home_score
            played += 1
    if any(type(n) is not int or n <= 0 for n in expected_matches.values()) or dict(counts) != expected_matches:
        raise SimulationInputError("Observed team match counts must exactly match the independently reviewed full roster")
    if played < 10:
        raise SimulationInputError("Each selected team requires at least 10 scored matches")
    baseline = total_goals / (2 * len(matches))
    if baseline <= 0:
        raise SimulationInputError("Season goals per team-match must be positive")
    first = matches[0]
    provenance = list({(m.provenance.url, m.provenance.sha256): m.provenance
                       for m in sorted(matches, key=lambda m: m.id)}.values())
    return TeamGoalStrength(team_id=team_id, competition_id=first.competition_id, season_id=first.season_id,
                           matches=played, season_matches=len(matches), season_total_goals=total_goals,
                           goals_for_per_match=goals_for / played,
                           goals_against_per_match=goals_against / played,
                           season_goals_per_team_match=baseline, attack_ratio=goals_for / played / baseline,
                           concession_ratio=goals_against / played / baseline, provenance=provenance)


def poisson_probabilities(mean: float) -> list[float]:
    """PMF through a cutoff with a geometric upper bound on its tail <= 5e-9."""
    if not isfinite(mean) or not 0 <= mean <= 100:
        raise SimulationInputError("Expected goals must be finite and between 0 and 100; unsupported extremes are rejected")
    probabilities = [exp(-mean)]
    for k in range(1000):
        next_probability = probabilities[-1] * mean / (k + 1)
        if k + 2 > mean:
            tail_bound = next_probability / (1 - mean / (k + 2))
            if tail_bound <= 5e-9:
                return probabilities
        probabilities.append(next_probability)
    raise SimulationInputError("Unable to meet Poisson tail tolerance")


class MatchSimulator:
    @staticmethod
    def simulate(team_a: str, matches_a: Sequence[Match], expected_a: dict[str, int],
                 team_b: str, matches_b: Sequence[Match], expected_b: dict[str, int],
                 seed: Optional[int] = None) -> MatchSimulation:
        if seed is not None and (type(seed) is not int or not 0 <= seed <= 2**32 - 1):
            raise SimulationInputError("Seed must be an integer from 0 to 4294967295")
        a = team_strength(team_a, matches_a, expected_a)
        b = team_strength(team_b, matches_b, expected_b)
        if (a.provenance[0].source, a.provenance[0].data_kind) != (b.provenance[0].source, b.provenance[0].data_kind):
            raise SimulationInputError("Both teams must share a source and real/sample designation")
        reference = (a.season_goals_per_team_match + b.season_goals_per_team_match) / 2
        mean_a = reference * a.attack_ratio * b.concession_ratio
        mean_b = reference * b.attack_ratio * a.concession_ratio
        pa, pb = poisson_probabilities(mean_a), poisson_probabilities(mean_b)
        cells = [(i, j, p * q) for i, p in enumerate(pa) for j, q in enumerate(pb)]
        retained = fsum(p for _, _, p in cells)
        win_a = fsum(p for i, j, p in cells if i > j) / retained
        draw = fsum(p for i, j, p in cells if i == j) / retained
        win_b = fsum(p for i, j, p in cells if i < j) / retained
        scorelines = [Scoreline(goals_a=i, goals_b=j, probability=p / retained)
                      for i, j, p in sorted(cells, key=lambda cell: (-cell[2], cell[0] + cell[1], cell[0]))[:5]
                      if p > 0]
        return MatchSimulation(
            seed=seed, data_kind=a.provenance[0].data_kind, team_a=a, team_b=b,
            reference_goals_per_team_match=reference, expected_goals_a=mean_a, expected_goals_b=mean_b,
            team_a_win_probability=win_a, draw_probability=draw, team_b_win_probability=win_b,
            most_likely_scorelines=scorelines, average_simulated_score=AverageScore(team_a=mean_a, team_b=mean_b),
            omitted_probability_mass=max(0, 1 - retained), goal_cutoff_a=len(pa) - 1, goal_cutoff_b=len(pb) - 1,
            explanation=[
                f"A scores {a.attack_ratio:.3f} times its season average; B concedes {b.concession_ratio:.3f} times its season average.",
                f"B scores {b.attack_ratio:.3f} times its season average; A concedes {a.concession_ratio:.3f} times its season average.",
                f"The shared neutral scoring baseline is {reference:.3f} goals per team-match, giving means {mean_a:.3f} and {mean_b:.3f}.",
                "Probabilities are analytical; the average score is the exact model expectation, not a sampled match result. Seed is accepted but unused.",
            ], limitations=[
                "Uncalibrated hypothetical scenario, not a validated forecast or betting recommendation.",
                "Own-season ratios do not calibrate league strength, era, schedule difficulty or cross-league superiority.",
                "Independent Poisson goals omit score-state dependence, low-score correlation, injuries, lineups and home advantage.",
                "Means use observed goals, not shot-based xG. Small samples and finishing variance can distort strengths; no shrinkage is fitted.",
                "Final-score rates are per match, including any extra time and excluding shootouts; this is not a guaranteed 90-minute forecast.",
                "Zero observed scoring or conceding can imply zero expected goals in this unsmoothed baseline.",
            ])
