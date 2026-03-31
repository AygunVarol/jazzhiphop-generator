from __future__ import annotations

import random

from .defaults import FAMILY_DEGREE_CHORDS, MAJOR_TRANSITIONS, MINOR_TRANSITIONS
from .models import SectionPlan, TrackPlan


class HarmonyEngine:
    def __init__(self, plan: TrackPlan) -> None:
        self.plan = plan
        self.rng = random.Random(plan.seed + 17)
        self.degree_map = FAMILY_DEGREE_CHORDS[plan.progression_family]
        self.is_minor = "i" in self.degree_map
        self.transitions = MINOR_TRANSITIONS if self.is_minor else MAJOR_TRANSITIONS

    def generate_section_progression(
        self,
        section: SectionPlan,
        next_section_name: str | None,
        previous_degree: str | None,
    ) -> tuple[list[str], str]:
        current_degree = previous_degree or self._entry_degree(section.name)
        progression: list[str] = []

        for bar_index in range(section.bars):
            if bar_index == 0 and section.name == "chorus":
                current_degree = self._entry_degree("chorus")

            if bar_index >= section.bars - 2:
                current_degree = self._cadence_degree(
                    section.name,
                    next_section_name,
                    current_degree,
                    is_final_bar=bar_index == section.bars - 1,
                )
            elif bar_index > 0:
                current_degree = self._choose_next_degree(current_degree, section)

            current_degree = self._resolve_degree(current_degree)
            progression.append(self.degree_map[current_degree])

        return progression, current_degree

    def _choose_next_degree(self, current_degree: str, section: SectionPlan) -> str:
        options = list(self.transitions.get(current_degree, (self._tonic_degree(),)))
        if section.variation == "breakdown":
            if self.rng.random() < 0.45:
                return current_degree
            options = [degree for degree in options if degree not in {self._dominant_degree(), self._leading_degree()}] or options
        elif section.variation == "lift":
            options = self._weighted_pool(options, [self._dominant_degree(), self._leading_degree(), self._subdominant_degree()])
        elif section.variation == "release":
            options = self._weighted_pool(options, [self._tonic_degree(), self._relative_degree()])
        elif section.variation == "answer":
            options = self._weighted_pool(options, [self._subdominant_degree(), self._relative_degree()])

        if section.intensity < 0.45 and self.rng.random() < 0.35:
            return current_degree

        return self._resolve_degree(self.rng.choice(options))

    def _cadence_degree(
        self,
        section_name: str,
        next_section_name: str | None,
        current_degree: str,
        is_final_bar: bool,
    ) -> str:
        if section_name == "outro":
            return self._tonic_degree()
        if section_name == "intro" and is_final_bar:
            return self._tonic_degree()
        if next_section_name == "chorus":
            return self._dominant_degree() if is_final_bar else self._predominant_degree()
        if next_section_name == "bridge":
            return self._relative_degree() if is_final_bar else self._subdominant_degree()
        if is_final_bar and next_section_name is None:
            return self._tonic_degree()
        if is_final_bar and section_name == "chorus":
            return self._tonic_degree()
        return current_degree

    def _entry_degree(self, section_name: str) -> str:
        options = {
            "intro": [self._tonic_degree(), self._relative_degree()],
            "verse_a": [self._relative_degree(), self._tonic_degree(), self._predominant_degree()],
            "chorus": [self._tonic_degree(), self._subdominant_degree()],
            "verse_b": [self._predominant_degree(), self._relative_degree(), self._tonic_degree()],
            "bridge": [self._subdominant_degree(), self._relative_degree()],
            "outro": [self._tonic_degree()],
        }
        for degree in options.get(section_name, [self._tonic_degree()]):
            if degree in self.degree_map:
                return degree
        return self._tonic_degree()

    def _weighted_pool(self, options: list[str], favored: list[str]) -> list[str]:
        weighted = list(options)
        for degree in favored:
            if degree in options:
                weighted.extend([degree, degree])
        return weighted

    def _tonic_degree(self) -> str:
        return self._resolve_degree("i" if self.is_minor else "I")

    def _dominant_degree(self) -> str:
        return self._resolve_degree("V")

    def _leading_degree(self) -> str:
        return self._resolve_degree("VII")

    def _relative_degree(self) -> str:
        return self._resolve_degree("VI" if self.is_minor else "vi")

    def _subdominant_degree(self) -> str:
        return self._resolve_degree("iv" if self.is_minor else "IV")

    def _predominant_degree(self) -> str:
        return self._resolve_degree("ii")

    def _resolve_degree(self, degree: str) -> str:
        if degree in self.degree_map:
            return degree

        alternates = {
            "i": "I",
            "I": "i",
            "ii": "II",
            "II": "ii",
            "iii": "III",
            "III": "iii",
            "iv": "IV",
            "IV": "iv",
            "v": "V",
            "V": "v",
            "vi": "VI",
            "VI": "vi",
            "vii": "VII",
            "VII": "vii",
        }
        alternate = alternates.get(degree)
        if alternate in self.degree_map:
            return alternate

        for candidate in self.degree_map:
            if candidate.lower() == degree.lower():
                return candidate

        return next(iter(self.degree_map))
