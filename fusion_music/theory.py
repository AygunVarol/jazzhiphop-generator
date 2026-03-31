from __future__ import annotations

import re
from typing import Iterable

from .defaults import KEY_TO_SEMITONE, MODE_INTERVALS

ROMAN_TO_DEGREE = {
    "I": 0,
    "II": 1,
    "III": 2,
    "IV": 3,
    "V": 4,
    "VI": 5,
    "VII": 6,
}

CHORD_PATTERN = re.compile(
    r"^(?P<accidental>[b#]?)(?P<roman>(?:VII|VI|IV|V|III|II|I|vii|vi|iv|v|iii|ii|i))(?P<quality>.*)$"
)


def key_root_midi(key: str, octave: int = 4) -> int:
    semitone = KEY_TO_SEMITONE[key]
    return 12 * (octave + 1) + semitone


def scale_pitch_classes(key: str, mode: str) -> set[int]:
    root_pc = KEY_TO_SEMITONE[key]
    return {(root_pc + interval) % 12 for interval in MODE_INTERVALS[mode]}


def scale_notes_for_range(key: str, mode: str, low: int, high: int) -> list[int]:
    pcs = scale_pitch_classes(key, mode)
    return [pitch for pitch in range(low, high + 1) if pitch % 12 in pcs]


def parse_chord_symbol(symbol: str) -> tuple[int, str, str, bool]:
    match = CHORD_PATTERN.match(symbol)
    if not match:
        raise ValueError(f"Unsupported chord symbol: {symbol}")

    roman = match.group("roman")
    quality = match.group("quality").strip()
    degree = ROMAN_TO_DEGREE[roman.upper()]
    return degree, quality, roman, roman.islower() or roman[0].islower()


def chord_root(symbol: str, key: str, mode: str, octave: int = 3) -> int:
    degree, _, _, _ = parse_chord_symbol(symbol)
    root = key_root_midi(key, octave) + MODE_INTERVALS[mode][degree]
    if symbol.startswith("b"):
        root -= 1
    elif symbol.startswith("#"):
        root += 1
    return root


def chord_tones(
    symbol: str,
    key: str,
    mode: str,
    octave: int = 4,
    rootless: bool = False,
) -> list[int]:
    root = chord_root(symbol, key, mode, octave)
    _, quality, roman, is_minor_roman = parse_chord_symbol(symbol)
    intervals = _intervals_for_quality(quality, is_minor_roman, roman)
    notes = [root + interval for interval in intervals]
    if rootless and len(notes) > 3:
        notes = notes[1:]
    return sorted(notes)


def voice_led_chord(
    symbol: str,
    key: str,
    mode: str,
    previous: list[int] | None = None,
    rootless: bool = True,
    low: int = 55,
    high: int = 84,
    center: int = 67,
) -> list[int]:
    base = chord_tones(symbol, key, mode, octave=4, rootless=rootless)
    variants = []
    raw_variants = [base]

    if len(base) >= 4:
        raw_variants.append(base[1:] + [base[0] + 12])
        raw_variants.append([base[0] - 12] + base[:-1])

    for variant in raw_variants:
        for shift in (-12, 0, 12):
            candidate = _fit_to_register([note + shift for note in variant], low, high, center)
            variants.append(candidate)

    if previous is None:
        return min(variants, key=lambda candidate: abs(_mean(candidate) - center))

    return min(variants, key=lambda candidate: _voice_leading_score(candidate, previous, center))


def nearest_scale_note(target: int, scale_pool: Iterable[int]) -> int:
    return min(scale_pool, key=lambda pitch: abs(pitch - target))


def _intervals_for_quality(quality: str, is_minor_roman: bool, roman: str) -> list[int]:
    normalized = quality.lower().replace("min", "m")
    if not normalized:
        return [0, 3, 7] if is_minor_roman else [0, 4, 7]

    if normalized == "6/9":
        return [0, 4, 7, 9, 14]
    if normalized == "maj7":
        return [0, 4, 7, 11]
    if normalized == "maj9":
        return [0, 4, 7, 11, 14]
    if normalized == "maj13":
        return [0, 4, 7, 11, 14, 21]
    if normalized in {"sus", "sus7", "7sus"}:
        return [0, 5, 7, 10]
    if normalized == "dim7":
        return [0, 3, 6, 9]
    if normalized == "halfdim":
        return [0, 3, 6, 10]

    if normalized.startswith("m"):
        remainder = normalized[1:] or "triad"
        if remainder == "triad":
            return [0, 3, 7]
        if remainder == "7":
            return [0, 3, 7, 10]
        if remainder == "9":
            return [0, 3, 7, 10, 14]
        if remainder == "11":
            return [0, 3, 7, 10, 14, 17]
        if remainder == "13":
            return [0, 3, 7, 10, 14, 21]

    if normalized in {"7", "9", "11", "13"}:
        if is_minor_roman:
            return _intervals_for_quality(f"m{normalized}", True, roman)
        dominant_map = {
            "7": [0, 4, 7, 10],
            "9": [0, 4, 7, 10, 14],
            "11": [0, 4, 7, 10, 14, 17],
            "13": [0, 4, 7, 10, 14, 21],
        }
        return dominant_map[normalized]

    return [0, 3, 7] if is_minor_roman else [0, 4, 7]


def _fit_to_register(notes: list[int], low: int, high: int, center: int) -> list[int]:
    adjusted = []
    for note in notes:
        while note < low:
            note += 12
        while note > high:
            note -= 12
        adjusted.append(note)

    mean = _mean(adjusted)
    while mean < center - 5 and max(adjusted) + 12 <= high + 12:
        adjusted = [note + 12 for note in adjusted]
        mean = _mean(adjusted)
    while mean > center + 5 and min(adjusted) - 12 >= low - 12:
        adjusted = [note - 12 for note in adjusted]
        mean = _mean(adjusted)

    return sorted(adjusted)


def _voice_leading_score(candidate: list[int], previous: list[int], center: int) -> float:
    score = abs(_mean(candidate) - center) * 0.2
    padded_previous = previous + [previous[-1]] * max(0, len(candidate) - len(previous))
    for left, right in zip(candidate, padded_previous):
        score += abs(left - right)
    return score


def _mean(values: list[int]) -> float:
    return sum(values) / max(1, len(values))
