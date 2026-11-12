"""Parsing and scoring for Epic Seven gear screenshots."""

from __future__ import annotations

from dataclasses import dataclass, field
import re


SUBSTAT_WEIGHTS = {
    "attack": 1.0,
    "critical hit chance": 1.2,
    "critical hit damage": 1.2,
    "speed": 1.5,
    "health": 0.65,
    "defense": 0.65,
    "effectiveness": 0.75,
    "effect resistance": 0.75,
}

SUBSTAT_PATTERNS = {
    "attack": r"(?:attack|atk)\s*([+-]?\d+(?:\.\d+)?)\s*%",
    "critical hit chance": r"(?:critical hit chance|crit(?:ical)? chance|crit)\s*([+-]?\d+(?:\.\d+)?)\s*%",
    "critical hit damage": r"(?:critical hit damage|crit(?:ical)? damage|cdmg)\s*([+-]?\d+(?:\.\d+)?)\s*%",
    "speed": r"(?:speed|spd)\s*([+-]?\d+(?:\.\d+)?)\b",
    "health": r"(?:health|hp)\s*([+-]?\d+(?:\.\d+)?)\s*%",
    "defense": r"(?:defense|def)\s*([+-]?\d+(?:\.\d+)?)\s*%",
    "effectiveness": r"(?:effectiveness|eff)\s*([+-]?\d+(?:\.\d+)?)\s*%",
    "effect resistance": r"(?:effect resistance|effect resist|resistance|res)\s*([+-]?\d+(?:\.\d+)?)\s*%",
}


@dataclass(frozen=True)
class Substat:
    name: str
    value: float
    unit: str


@dataclass
class Gear:
    level: int | None = None
    main_stat: str | None = None
    substats: list[Substat] = field(default_factory=list)


@dataclass(frozen=True)
class Evaluation:
    score: float
    recommendation: str
    reasons: tuple[str, ...]


def parse_gear(text: str) -> Gear:
    """Extract values stable enough to recognize from OCR text."""
    level_match = re.search(r"(?:level|lv\.?)\s*[:.]?\s*(\d{1,2})", text, re.IGNORECASE)
    level = int(level_match.group(1)) if level_match else None

    main_stat = None
    main_match = re.search(
        r"(?:main stat|main)\s*[:.]?\s*([^\n]+)", text, re.IGNORECASE
    )
    if main_match:
        main_stat = main_match.group(1).strip()

    substats: list[Substat] = []
    for line in text.splitlines():
        if re.search(r"\bmain stat\b|\bmain\s*:", line, re.IGNORECASE):
            continue
        for name, pattern in SUBSTAT_PATTERNS.items():
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                substats.append(Substat(name=name, value=float(match.group(1)), unit="%"))
    return Gear(level=level, main_stat=main_stat, substats=substats)


def _value_quality(substat: Substat) -> float:
    caps = {
        "attack": 8,
        "critical hit chance": 8,
        "critical hit damage": 7,
        "speed": 5,
        "health": 8,
        "defense": 8,
        "effectiveness": 8,
        "effect resistance": 8,
    }
    return min(max(substat.value / caps[substat.name], 0.0), 1.0)


def evaluate_gear(gear: Gear) -> Evaluation:
    """Score initial substats on a 0-100 scale and explain the result."""
    if not gear.substats:
        return Evaluation(0.0, "Insufficient data", ("No recognizable substats were found.",))

    weighted_total = sum(
        _value_quality(stat) * SUBSTAT_WEIGHTS[stat.name] for stat in gear.substats
    )
    weight_total = sum(SUBSTAT_WEIGHTS[stat.name] for stat in gear.substats)
    score = round(100 * weighted_total / weight_total, 1)

    useful_count = sum(_value_quality(stat) >= 0.6 for stat in gear.substats)
    reasons = [
        f"{useful_count}/{len(gear.substats)} substats are at least 60% of a typical high starting value."
    ]
    if len(gear.substats) < 3:
        reasons.append("Fewer than three substats were recognized; check the OCR text.")
    if any(stat.name == "speed" and stat.value >= 4 for stat in gear.substats):
        reasons.append("Speed is a strong positive signal.")
    if score >= 65 and len(gear.substats) >= 3:
        recommendation = "Roll"
        reasons.append("The starting substat quality is strong enough to justify rolling.")
    elif score >= 45:
        recommendation = "Maybe"
        reasons.append("Roll only if the set, main stat, and target build fit your account.")
    else:
        recommendation = "Skip"
        reasons.append("The starting substat quality is weak for a general-purpose roll.")
    return Evaluation(score, recommendation, tuple(reasons))
