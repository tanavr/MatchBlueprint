"""Comparison results keep raw context distinct from relative style evidence."""

from typing import Literal, Optional

from app.models.football import Record
from app.models.tactical import TacticalProfile


class Difference(Record):
    team_a: Optional[float] = None
    team_b: Optional[float] = None
    difference_a_minus_b: Optional[float] = None
    unit: str
    basis: Literal["raw_context_only", "component_percentile", "relative_tactical_score"]
    reason: Optional[str] = None


class StyleAdvantage(Record):
    category: str
    lead_points: float
    meaning: str = "Greater relative stylistic emphasis; not a competitive advantage or win prediction"


class TeamComparison(Record):
    comparison_version: str = "1.0.0"
    team_a: TacticalProfile
    team_b: TacticalProfile
    raw_metric_differences: dict[str, Difference]
    normalized_metric_differences: dict[str, Difference]
    tactical_score_comparison: dict[str, Difference]
    team_a_advantages: list[StyleAdvantage]
    team_b_advantages: list[StyleAdvantage]
    similarities: list[str]
    matchup_observations: list[str]
    limitations: list[str]
