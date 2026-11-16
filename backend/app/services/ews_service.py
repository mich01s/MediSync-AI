"""
MediSync AI — Early Warning System (EWS) Service
Rule-based vital sign evaluation returning a risk level 0–3.

Thresholds follow a simplified NEWS2 (National Early Warning Score) approach:
  Level 0 — Normal
  Level 1 — Low risk (monitor)
  Level 2 — Medium risk (escalate)
  Level 3 — Critical (immediate response required)
"""
from typing import Any


# ── Threshold definitions ─────────────────────────────────────────────────────

_THRESHOLDS: dict[str, dict[str, tuple[float, float]]] = {
    # param_name → {level: (low_bound, high_bound)} — out-of-range triggers level
    "bp_systolic": {
        "level_3_low": (0, 90),
        "level_3_high": (220, float("inf")),
        "level_2_low": (90, 100),
        "level_2_high": (200, 220),
        "level_1_low": (100, 110),
        "level_1_high": (180, 200),
    },
    "heart_rate": {
        "level_3_low": (0, 40),
        "level_3_high": (131, float("inf")),
        "level_2_low": (40, 50),
        "level_2_high": (111, 131),
        "level_1_low": (50, 60),
        "level_1_high": (91, 111),
    },
    "temperature": {
        "level_3_low": (0, 35.0),
        "level_3_high": (39.1, float("inf")),
        "level_2_low": (35.0, 35.9),
        "level_2_high": (38.6, 39.1),
        "level_1_low": (35.9, 36.0),
        "level_1_high": (38.1, 38.6),
    },
    "spo2": {
        "level_3_low": (0, 91),
        "level_2_low": (91, 94),
        "level_1_low": (94, 95),
    },
    "glucose": {
        "level_3_low": (0, 50),
        "level_3_high": (400, float("inf")),
        "level_2_low": (50, 70),
        "level_2_high": (300, 400),
        "level_1_low": (70, 80),
        "level_1_high": (200, 300),
    },
}


def _check_param(param: str, value: float) -> int:
    """Return the EWS level (0–3) triggered by a single vital sign value."""
    rules = _THRESHOLDS.get(param, {})
    max_level = 0
    for rule_name, (low, high) in rules.items():
        if low <= value < high:
            level = int(rule_name.split("_")[1])
            max_level = max(max_level, level)
    return max_level


def evaluate_ews(vitals: dict[str, Any]) -> dict[str, Any]:
    """
    Evaluate all present vital signs and return:
    - ``level``: aggregate EWS level (worst single param)
    - ``triggered_params``: which parameters triggered a warning
    - ``scores``: per-parameter level breakdown

    Args:
        vitals: Dict from ``tabular_metrics_json`` e.g.
            {"bp_systolic": 95, "heart_rate": 110, "temperature": 38.7, "spo2": 93}
    """
    scores: dict[str, int] = {}
    triggered: list[str] = []

    for param, value in vitals.items():
        if not isinstance(value, (int, float)):
            continue
        level = _check_param(param, float(value))
        scores[param] = level
        if level > 0:
            triggered.append(param)

    aggregate_level = max(scores.values(), default=0)

    return {
        "level": aggregate_level,
        "triggered_params": triggered,
        "scores": scores,
        "summary": _level_summary(aggregate_level),
    }


def _level_summary(level: int) -> str:
    messages = {
        0: "Normal — no immediate action required.",
        1: "Low risk — monitor closely.",
        2: "Medium risk — escalate to attending physician.",
        3: "CRITICAL — immediate emergency response required!",
    }
    return messages.get(level, "Unknown EWS level.")
