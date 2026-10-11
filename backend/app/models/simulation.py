"""Auditable inputs and outputs for the neutral-venue goals baseline."""
from typing import Literal, Optional

from pydantic import Field

from app.models.football import Provenance, Record


class TeamGoalStrength(Record):
    team_id: str
    competition_id: str
    season_id: str
    matches: int
    season_matches: int
    season_total_goals: int
    goals_for_per_match: float
    goals_against_per_match: float
    season_goals_per_team_match: float
    attack_ratio: float
    concession_ratio: float
    provenance: list[Provenance]


class Scoreline(Record):
    goals_a: int
    goals_b: int
    probability: float = Field(ge=0, le=1)


class AverageScore(Record):
    team_a: float
    team_b: float


class MatchSimulation(Record):
    model_version: str = "1.0.0"
    method: Literal["analytical_poisson"] = "analytical_poisson"
    venue: Literal["neutral"] = "neutral"
    data_kind: Literal["real", "sample"]
    seed: Optional[int] = None
    seed_used: bool = False
    team_a: TeamGoalStrength
    team_b: TeamGoalStrength
    reference_goals_per_team_match: float
    expected_goals_a: float
    expected_goals_b: float
    team_a_win_probability: float = Field(ge=0, le=1)
    draw_probability: float = Field(ge=0, le=1)
    team_b_win_probability: float = Field(ge=0, le=1)
    most_likely_scorelines: list[Scoreline]
    average_simulated_score: AverageScore
    omitted_probability_mass: float
    goal_cutoff_a: int
    goal_cutoff_b: int
    explanation: list[str]
    limitations: list[str]
