"""Compare existing independent competition-season profiles; never rank a pair."""

from math import isfinite
from typing import Optional

from app.analytics.tactical import DIMENSIONS
from app.models.comparison import Difference, StyleAdvantage, TeamComparison
from app.models.metrics import Metric
from app.models.tactical import TacticalProfile, TacticalScore


class ComparisonInputError(ValueError):
    """Profiles do not share compatible definitions or reference settings."""


def _finite(value: Optional[float]) -> Optional[float]:
    return value if value is not None and isfinite(value) else None


def _raw(metric: Optional[Metric]) -> Optional[float]:
    if metric is None or metric.status == "unavailable" or metric.denominator <= 0:
        return None
    return _finite(metric.value)


def _reference_reason(a: TacticalProfile, b: TacticalProfile,
                      sa: Optional[TacticalScore], sb: Optional[TacticalScore]) -> Optional[str]:
    if sa is None or sb is None or _finite(sa.value) is None or _finite(sb.value) is None:
        return "A tactical dimension is unavailable on one or both sides"
    for profile, score in ((a, sa), (b, sb)):
        if len(set(score.cohort_team_ids)) < profile.config.min_teams or profile.team_id not in score.cohort_team_ids:
            return "Reference cohort metadata is insufficient"
    if (a.competition_id, a.season_id) == (b.competition_id, b.season_id):
        if set(sa.cohort_team_ids) != set(sb.cohort_team_ids) or a.expected_matches != b.expected_matches:
            return "Same-season scores use different reference cohorts or roster counts"
    return None


class TeamComparisonEngine:
    @staticmethod
    def compare(a: TacticalProfile, b: TacticalProfile) -> TeamComparison:
        if (a.source, a.data_kind, a.model_version, a.metrics_version, a.config) != (
                b.source, b.data_kind, b.model_version, b.metrics_version, b.config):
            raise ComparisonInputError("Profiles must share source, real/sample status, model versions and scoring configuration")
        if a.model_version != "1.0.0" or a.metrics_version != "1.0.0":
            raise ComparisonInputError("Unsupported profile version")
        raw = {}
        for name in sorted(set(a.raw_metrics) | set(b.raw_metrics)):
            ma, mb = a.raw_metrics.get(name), b.raw_metrics.get(name)
            va, vb = _raw(ma), _raw(mb)
            reason = None
            if va is None or vb is None:
                reason = "Raw metric unavailable on one or both sides"
            elif ma.unit != mb.unit:
                reason = "Raw metric units differ"
            raw[name] = Difference(team_a=va, team_b=vb, unit=ma.unit if ma else mb.unit,
                                   difference_a_minus_b=va - vb if reason is None else None,
                                   basis="raw_context_only", reason=reason)
        normalized, tactical = {}, {}
        for dimension, names in DIMENSIONS.items():
            sa, sb = a.scores.get(dimension), b.scores.get(dimension)
            reference_reason = _reference_reason(a, b, sa, sb)
            score_reason = reference_reason
            if score_reason is None and (sa.constant_components or sb.constant_components):
                score_reason = "A component has no variation in one or both reference cohorts"
            va, vb = _finite(sa.value) if sa else None, _finite(sb.value) if sb else None
            tactical[dimension] = Difference(team_a=va, team_b=vb,
                                             difference_a_minus_b=va - vb if score_reason is None else None,
                                             unit="score points", basis="relative_tactical_score", reason=score_reason)
            for name in names:
                ca = _finite(sa.components.get(name)) if sa else None
                cb = _finite(sb.components.get(name)) if sb else None
                reason = reference_reason
                if reason is None and (ca is None or cb is None):
                    reason = "Component percentile unavailable"
                if reason is None and (name in sa.constant_components or name in sb.constant_components):
                    reason = "Component is constant in one or both reference cohorts"
                normalized[name] = Difference(team_a=ca, team_b=cb, unit="percentile points",
                                              difference_a_minus_b=ca - cb if reason is None else None,
                                              basis="component_percentile", reason=reason)
        # Metrics without a fitted reference distribution stay unnormalized.
        for name in sorted(raw):
            if name not in normalized:
                normalized[name] = Difference(unit="percentile points", basis="component_percentile",
                                              reason="No component percentile is retained for this raw metric")
        deltas = {name: item.difference_a_minus_b for name, item in tactical.items()
                  if item.difference_a_minus_b is not None}
        advantages_a = [StyleAdvantage(category=name, lead_points=delta)
                        for name, delta in sorted(deltas.items(), key=lambda item: (-item[1], item[0]))
                        if delta >= 10][:3]
        advantages_b = [StyleAdvantage(category=name, lead_points=-delta)
                        for name, delta in sorted(deltas.items(), key=lambda item: (item[1], item[0]))
                        if delta <= -10][:3]
        similarities = [f"Similar relative {name.replace('_', ' ')}: within {abs(delta):.1f} score points."
                        for name, delta in sorted(deltas.items()) if abs(delta) <= 5]
        observations = []
        for first, second, sign in (("A", "B", 1), ("B", "A", -1)):
            def stronger_high(name: str) -> bool:
                value = tactical[name].team_a if sign == 1 else tactical[name].team_b
                return value is not None and value >= 75 and sign * deltas.get(name, 0) >= 10

            def other_high(name: str) -> bool:
                value = tactical[name].team_b if sign == 1 else tactical[name].team_a
                return value is not None and value >= 75 and sign * deltas.get(name, 0) <= -10

            if stronger_high("possession") and other_high("counterattacking_tendency"):
                observations.append(f"Team {first} emphasizes passing share relative to its peers, while Team {second} "
                                    "emphasizes source-tagged counters. This is a possession/transition style contrast, not a predicted outcome.")
            if stronger_high("attacking_intensity") and other_high("defensive_intensity"):
                observations.append(f"Team {first} ranks high in attacking activity while Team {second} ranks high in defensive activity. "
                                    "Defensive activity alone does not establish defensive quality or a low block.")
        if not observations:
            observations.append("No supported possession/counter or attacking/defensive contrast meets the stated thresholds.")
        if not deltas:
            observations.append("Insufficient comparable normalized evidence; no stylistic advantages or similarities are inferred.")
        return TeamComparison(team_a=a, team_b=b, raw_metric_differences=raw,
                              normalized_metric_differences=normalized, tactical_score_comparison=tactical,
                              team_a_advantages=advantages_a, team_b_advantages=advantages_b,
                              similarities=similarities, matchup_observations=observations, limitations=[
                                  "Raw deltas are context only and do not adjust for league strength, era, opponents or match selection.",
                                  "Normalized deltas compare relative style against each team's own competition-season, not absolute quality.",
                                  "Advantages mean greater relative stylistic emphasis, not superiority or expected match results.",
                                  "Possession and pressing retain their proxy limitations; activity is not effort, success or block depth.",
                                  "Different eligible match sets or provider fidelity across seasons can still affect interpretation.",
                                  "Constant reference components cannot establish comparable relative differences.",
                              ])
