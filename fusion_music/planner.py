from __future__ import annotations

import json
import random
import re
from typing import Any

from .defaults import (
    AMBIENCE_LAYERS,
    ARRANGEMENT_STYLES,
    BASS_SOUNDS,
    BASS_STYLES,
    COUNTER_SOUNDS,
    DRUM_STYLES,
    FAMILY_PREFERRED_MODES,
    IMMERSION_MODES,
    KEY_TO_SEMITONE,
    KEYS_SOUNDS,
    LAYERS,
    LEAD_SOUNDS,
    LEAD_STYLES,
    MODE_INTERVALS,
    MOTIF_VARIATIONS,
    PAD_SOUNDS,
    PIANO_STYLES,
    PERCUSSION_STYLES,
    PROGRESSION_LIBRARY,
    RIFF_SHAPES,
    SECTION_TEMPLATES,
    SECTION_VARIATIONS,
    TEXTURES,
)
from .models import SectionPlan, TrackPlan
from .providers import OllamaPlanProvider, PlanProvider


class LLMPlanner:
    def __init__(self, provider: PlanProvider | None = None) -> None:
        self.provider = provider

    def build_plan(
        self,
        prompt_hint: str = "",
        seed: int | None = None,
        use_provider: bool = True,
        immersion_override: str | None = None,
        ambience_override: list[str] | None = None,
    ) -> TrackPlan:
        effective_seed = seed if seed is not None else random.randint(1, 999_999)

        if use_provider and self.provider is not None:
            try:
                raw = self.provider.generate(self._build_prompt(prompt_hint, effective_seed), effective_seed)
                data = self._extract_json(raw)
                return self._normalize_plan(
                    data,
                    effective_seed,
                    self.provider.name,
                    prompt_hint,
                    immersion_override=immersion_override,
                    ambience_override=ambience_override,
                )
            except Exception as exc:
                plan = self._fallback_plan(
                    prompt_hint,
                    effective_seed,
                    immersion_override=immersion_override,
                    ambience_override=ambience_override,
                )
                plan.planner_notes = f"{self.provider.name} fallback activated: {exc}"
                return plan

        return self._fallback_plan(
            prompt_hint,
            effective_seed,
            immersion_override=immersion_override,
            ambience_override=ambience_override,
        )

    def _build_prompt(self, prompt_hint: str, seed: int) -> str:
        keys = ", ".join(KEY_TO_SEMITONE)
        modes = ", ".join(MODE_INTERVALS)
        textures = ", ".join(TEXTURES)
        arrangements = ", ".join(ARRANGEMENT_STYLES)
        progressions = ", ".join(PROGRESSION_LIBRARY)
        drums = ", ".join(DRUM_STYLES)
        bass = ", ".join(BASS_STYLES)
        bass_sounds = ", ".join(BASS_SOUNDS)
        keys_sounds = ", ".join(KEYS_SOUNDS)
        piano = ", ".join(PIANO_STYLES)
        lead_sounds = ", ".join(LEAD_SOUNDS)
        lead = ", ".join(LEAD_STYLES)
        pad_sounds = ", ".join(PAD_SOUNDS)
        counter_sounds = ", ".join(COUNTER_SOUNDS)
        percussion_styles = ", ".join(PERCUSSION_STYLES)
        riff_shapes = ", ".join(RIFF_SHAPES)
        motif_variations = ", ".join(MOTIF_VARIATIONS)
        variations = ", ".join(SECTION_VARIATIONS)
        layers = ", ".join(LAYERS)
        immersion_modes = ", ".join(IMMERSION_MODES)
        ambience_layers = ", ".join(AMBIENCE_LAYERS)

        return f"""
You are the composition planner for an advanced jazz-lofi hip-hop generator.
Return only valid JSON with no markdown fences.

Use this exact schema:
{{
  "title": "2 to 5 word title",
  "description": "1 or 2 sentence atmospheric description",
  "bpm": 68 to 104 integer,
  "key": "one of: {keys}",
  "mode": "one of: {modes}",
  "mood": "2 to 8 word mood phrase",
  "texture": "one of: {textures}",
  "arrangement_style": "one of: {arrangements}",
  "progression_family": "one of: {progressions}",
  "drum_style": "one of: {drums}",
  "bass_style": "one of: {bass}",
  "piano_style": "one of: {piano}",
  "lead_style": "one of: {lead}",
  "keys_sound": "one of: {keys_sounds}",
  "bass_sound": "one of: {bass_sounds}",
  "lead_sound": "one of: {lead_sounds}",
  "pad_sound": "one of: {pad_sounds}",
  "counter_sound": "one of: {counter_sounds}",
  "percussion_style": "one of: {percussion_styles}",
  "riff_shape": "one of: {riff_shapes}",
  "motif_variation": "one of: {motif_variations}",
  "riff_density": 0.2 to 0.95 float,
  "variety_amount": 0.15 to 0.95 float,
  "substitution_rate": 0.0 to 0.65 float,
  "immersion_mode": "one of: {immersion_modes}",
  "ambience_layers": ["zero or more of: {ambience_layers}"],
  "swing": 0.04 to 0.24 float,
  "humanization": 0.01 to 0.08 float,
  "sections": [
    {{
      "name": "intro|verse_a|chorus|verse_b|bridge|outro",
      "bars": 4|8|12|16,
      "intensity": 0.25 to 1.0 float,
      "layers": ["any of {layers}"],
      "variation": "one of: {variations}",
      "lead_density": 0.0 to 1.0 float
    }}
  ]
}}

Rules:
- Make a coherent full-song arc, not a loop.
- Include 6 or 7 sections.
- `keys` must appear in every section.
- Save the strongest lead writing for chorus sections.
- Use jazz-hip-hop harmony, lofi atmosphere, and head-nod rhythm.
- Choose an instrument palette that feels distinct for this song.
- Let riffs mutate across sections so the song is not repetitive.
- Higher `variety_amount` means more mutated patterns, but keep the song musical.
- If immersion_mode is `music`, ambience_layers should be empty or just vinyl.
- If immersion_mode is `world`, add 2 to 4 ambience layers that fit the prompt.
- Use seed {seed} as the source of randomness.

User vibe hint: {prompt_hint or "No extra hint. Choose a sophisticated late-night jazz-lofi direction."}
""".strip()

    def _extract_json(self, text: str) -> dict[str, Any]:
        cleaned = text.strip().replace("```json", "").replace("```", "").strip()
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if not match:
            raise ValueError("LLM response did not contain JSON")
        return json.loads(match.group(0))

    def _normalize_plan(
        self,
        data: dict[str, Any],
        seed: int,
        source: str,
        prompt_hint: str,
        immersion_override: str | None,
        ambience_override: list[str] | None,
    ) -> TrackPlan:
        rng = random.Random(seed)
        arrangement_style = self._pick(data.get("arrangement_style"), ARRANGEMENT_STYLES, rng.choice(ARRANGEMENT_STYLES))
        template = SECTION_TEMPLATES[arrangement_style]
        progression_family = self._pick(data.get("progression_family"), tuple(PROGRESSION_LIBRARY), rng.choice(tuple(PROGRESSION_LIBRARY)))
        preferred_modes = FAMILY_PREFERRED_MODES[progression_family]
        mode = self._pick(data.get("mode"), tuple(MODE_INTERVALS), preferred_modes[0])

        sections = self._normalize_sections(data.get("sections"), template)
        if not sections:
            sections = self._sections_from_template(template)

        immersion_mode = self._normalize_immersion_mode(
            immersion_override or data.get("immersion_mode"),
            prompt_hint,
        )
        if immersion_override is None and immersion_mode == "music":
            prompt_inferred_mode = self._normalize_immersion_mode(None, prompt_hint)
            if prompt_inferred_mode != "music":
                immersion_mode = prompt_inferred_mode
        ambience_layers = self._normalize_ambience_layers(
            ambience_override if ambience_override is not None else data.get("ambience_layers"),
            immersion_mode,
            prompt_hint,
            rng,
        )

        title = self._clean_text(data.get("title"), "Velvet Transit")
        description = self._clean_text(
            data.get("description"),
            "A warm, cinematic pocket of jazz harmony, lofi dust, and late-night motion.",
        )

        counter_sound = self._pick(data.get("counter_sound"), COUNTER_SOUNDS, rng.choice(COUNTER_SOUNDS))
        percussion_style = self._pick(data.get("percussion_style"), PERCUSSION_STYLES, rng.choice(PERCUSSION_STYLES))
        riff_density = self._bounded_float(data.get("riff_density"), 0.2, 0.95, rng.uniform(0.38, 0.8))
        variety_amount = self._bounded_float(data.get("variety_amount"), 0.15, 0.95, rng.uniform(0.32, 0.78))
        sections = self._shape_sections(
            sections,
            counter_sound=counter_sound,
            percussion_style=percussion_style,
            riff_density=riff_density,
            variety_amount=variety_amount,
            rng=rng,
        )

        return TrackPlan(
            title=title,
            description=description,
            bpm=self._bounded_int(data.get("bpm"), 68, 104, rng.randint(72, 94)),
            key=self._pick(data.get("key"), tuple(KEY_TO_SEMITONE), rng.choice(tuple(KEY_TO_SEMITONE))),
            mode=mode,
            mood=self._clean_text(data.get("mood"), "late night drift"),
            texture=self._pick(data.get("texture"), TEXTURES, rng.choice(TEXTURES)),
            swing=self._bounded_float(data.get("swing"), 0.04, 0.24, rng.uniform(0.08, 0.18)),
            humanization=self._bounded_float(data.get("humanization"), 0.01, 0.08, rng.uniform(0.02, 0.05)),
            arrangement_style=arrangement_style,
            progression_family=progression_family,
            drum_style=self._pick(data.get("drum_style"), DRUM_STYLES, rng.choice(DRUM_STYLES)),
            bass_style=self._pick(data.get("bass_style"), BASS_STYLES, rng.choice(BASS_STYLES)),
            piano_style=self._pick(data.get("piano_style"), PIANO_STYLES, rng.choice(PIANO_STYLES)),
            lead_style=self._pick(data.get("lead_style"), LEAD_STYLES, rng.choice(LEAD_STYLES)),
            keys_sound=self._pick(data.get("keys_sound"), KEYS_SOUNDS, rng.choice(KEYS_SOUNDS)),
            bass_sound=self._pick(data.get("bass_sound"), BASS_SOUNDS, rng.choice(BASS_SOUNDS)),
            lead_sound=self._pick(data.get("lead_sound"), LEAD_SOUNDS, rng.choice(LEAD_SOUNDS)),
            pad_sound=self._pick(data.get("pad_sound"), PAD_SOUNDS, rng.choice(PAD_SOUNDS)),
            counter_sound=counter_sound,
            percussion_style=percussion_style,
            riff_shape=self._pick(data.get("riff_shape"), RIFF_SHAPES, rng.choice(RIFF_SHAPES)),
            motif_variation=self._pick(data.get("motif_variation"), MOTIF_VARIATIONS, rng.choice(MOTIF_VARIATIONS)),
            riff_density=riff_density,
            variety_amount=variety_amount,
            substitution_rate=self._bounded_float(data.get("substitution_rate"), 0.0, 0.65, rng.uniform(0.08, 0.32)),
            immersion_mode=immersion_mode,
            ambience_layers=ambience_layers,
            sections=sections,
            seed=seed,
            planner_source=source,
        )

    def _normalize_sections(self, section_data: Any, template: list[dict[str, Any]]) -> list[SectionPlan]:
        if not isinstance(section_data, list) or len(section_data) < 4:
            return []

        normalized: list[SectionPlan] = []
        for index, raw_section in enumerate(section_data[:7]):
            default_section = template[min(index, len(template) - 1)]
            if not isinstance(raw_section, dict):
                raw_section = {}

            layers = raw_section.get("layers")
            if not isinstance(layers, list):
                layers = list(default_section["layers"])
            layers = [layer for layer in layers if layer in LAYERS]
            if "keys" not in layers:
                layers.insert(0, "keys")
            layers = list(dict.fromkeys(layers))

            lead_density = self._bounded_float(
                raw_section.get("lead_density"),
                0.0,
                1.0,
                float(default_section.get("lead_density", 0.0)),
            )
            if lead_density > 0.0 and "lead" not in layers:
                layers.append("lead")

            normalized.append(
                SectionPlan(
                    name=self._pick(
                        raw_section.get("name"),
                        ("intro", "verse_a", "chorus", "verse_b", "bridge", "outro"),
                        default_section["name"],
                    ),
                    bars=self._pick_bars(raw_section.get("bars"), int(default_section["bars"])),
                    intensity=self._bounded_float(
                        raw_section.get("intensity"),
                        0.25,
                        1.0,
                        float(default_section["intensity"]),
                    ),
                    layers=layers,
                    variation=self._pick(
                        raw_section.get("variation"),
                        SECTION_VARIATIONS,
                        str(default_section["variation"]),
                    ),
                    lead_density=lead_density,
                )
            )

        return normalized

    def _fallback_plan(
        self,
        prompt_hint: str,
        seed: int,
        immersion_override: str | None,
        ambience_override: list[str] | None,
    ) -> TrackPlan:
        rng = random.Random(seed)
        arrangement_style = rng.choice(ARRANGEMENT_STYLES)
        progression_family = rng.choice(tuple(PROGRESSION_LIBRARY))
        preferred_modes = FAMILY_PREFERRED_MODES[progression_family]
        prompt_text = prompt_hint.lower()

        if any(token in prompt_text for token in ("rain", "night", "smoke", "drizzle", "midnight")):
            progression_family = "smoke_and_rain"
            preferred_modes = FAMILY_PREFERRED_MODES[progression_family]
        elif any(token in prompt_text for token in ("gold", "sun", "warm", "day", "summer")):
            progression_family = "golden_hour"
            preferred_modes = FAMILY_PREFERRED_MODES[progression_family]

        mood_options = [
            "late night drift",
            "dusty skyline glow",
            "subway window reflections",
            "rain on neon sidewalks",
            "head nod reverie",
        ]
        immersion_mode = self._normalize_immersion_mode(immersion_override, prompt_hint)
        ambience_layers = self._normalize_ambience_layers(ambience_override, immersion_mode, prompt_hint, rng)
        counter_sound = self._infer_choice(prompt_text, {
            "clarinet": "clarinet",
            "marimba": "marimba",
            "guitar": "guitar_harmonics",
            "bell": "bell_pluck",
        }, rng.choice(COUNTER_SOUNDS))
        percussion_style = rng.choice(PERCUSSION_STYLES)
        riff_density = round(rng.uniform(0.34, 0.82), 3)
        variety_amount = round(rng.uniform(0.28, 0.85), 3)
        sections = self._shape_sections(
            self._sections_from_template(SECTION_TEMPLATES[arrangement_style]),
            counter_sound=counter_sound,
            percussion_style=percussion_style,
            riff_density=riff_density,
            variety_amount=variety_amount,
            rng=rng,
        )

        return TrackPlan(
            title=rng.choice(["Velvet Transit", "Blue Platform", "Rain Study", "Static Sun", "Midnight Frames"]),
            description="A merged jazz-lofi generator plan built from the local fallback engine when the LLM planner is unavailable.",
            bpm=rng.randint(70, 96),
            key=rng.choice(tuple(KEY_TO_SEMITONE)),
            mode=rng.choice(preferred_modes),
            mood=rng.choice(mood_options),
            texture=rng.choice(TEXTURES),
            swing=round(rng.uniform(0.08, 0.18), 3),
            humanization=round(rng.uniform(0.02, 0.05), 3),
            arrangement_style=arrangement_style,
            progression_family=progression_family,
            drum_style=rng.choice(DRUM_STYLES),
            bass_style=rng.choice(BASS_STYLES),
            piano_style=rng.choice(PIANO_STYLES),
            lead_style=rng.choice(LEAD_STYLES),
            keys_sound=self._infer_choice(prompt_text, {
                "guitar": "jazz_guitar",
                "rhodes": "rhodes",
                "piano": "upright_piano",
                "wurli": "wurlitzer",
                "detuned": "detuned_keys",
            }, rng.choice(KEYS_SOUNDS)),
            bass_sound=self._infer_choice(prompt_text, {
                "upright": "upright_bass",
                "fretless": "fretless_bass",
                "sub": "sine_sub",
            }, rng.choice(BASS_SOUNDS)),
            lead_sound=self._infer_choice(prompt_text, {
                "flute": "flute",
                "trumpet": "muted_trumpet",
                "vibes": "vibes",
                "synth": "analog_lead",
                "ep": "electric_piano_lead",
            }, rng.choice(LEAD_SOUNDS)),
            pad_sound=rng.choice(PAD_SOUNDS),
            counter_sound=counter_sound,
            percussion_style=percussion_style,
            riff_shape=rng.choice(RIFF_SHAPES),
            motif_variation=rng.choice(MOTIF_VARIATIONS),
            riff_density=riff_density,
            variety_amount=variety_amount,
            substitution_rate=round(rng.uniform(0.06, 0.34), 3),
            immersion_mode=immersion_mode,
            ambience_layers=ambience_layers,
            sections=sections,
            seed=seed,
            planner_source="fallback",
            planner_notes="Deterministic local fallback planner used.",
        )

    def _normalize_immersion_mode(self, value: Any, prompt_hint: str) -> str:
        if isinstance(value, str) and value in IMMERSION_MODES:
            return value

        prompt_text = prompt_hint.lower()
        if any(token in prompt_text for token in ("city", "street", "station", "world", "train", "tokyo")):
            return "world"
        if any(token in prompt_text for token in ("rain", "wind", "waves", "fire", "forest", "night")):
            return "atmosphere"
        return "atmosphere"

    def _normalize_ambience_layers(
        self,
        value: Any,
        immersion_mode: str,
        prompt_hint: str,
        rng: random.Random,
    ) -> list[str]:
        if isinstance(value, list):
            layers = [layer for layer in value if isinstance(layer, str) and layer in AMBIENCE_LAYERS]
        else:
            layers = []

        if not layers:
            prompt_text = prompt_hint.lower()
            inferred = []
            keyword_map = {
                "rain": "rain",
                "storm": "rain",
                "wind": "wind",
                "city": "city",
                "street": "city",
                "tokyo": "city",
                "fire": "fire",
                "campfire": "fire",
                "wave": "waves",
                "ocean": "waves",
                "sea": "waves",
                "night": "night",
                "train": "train",
                "station": "train",
            }
            for token, layer in keyword_map.items():
                if token in prompt_text and layer not in inferred:
                    inferred.append(layer)
            layers = inferred

        if immersion_mode == "music":
            return ["vinyl"] if "vinyl" in layers else []

        if "vinyl" not in layers:
            layers.insert(0, "vinyl")

        if immersion_mode == "atmosphere":
            if len(layers) == 1:
                layers.append(rng.choice([layer for layer in ("rain", "wind", "waves", "fire", "night") if layer != layers[0]]))
            return layers[:2]

        if immersion_mode == "world":
            preferred = ["city", "train", "night", "rain", "wind", "waves", "fire"]
            for candidate in preferred:
                if candidate not in layers and len(layers) < 4:
                    layers.append(candidate)
                if len(layers) >= 3:
                    break
            return layers[:4]

        return layers[:4]

    def _sections_from_template(self, template: list[dict[str, Any]]) -> list[SectionPlan]:
        return [
            SectionPlan(
                name=str(item["name"]),
                bars=int(item["bars"]),
                intensity=float(item["intensity"]),
                layers=list(item["layers"]),
                variation=str(item["variation"]),
                lead_density=float(item["lead_density"]),
            )
            for item in template
        ]

    def _shape_sections(
        self,
        sections: list[SectionPlan],
        counter_sound: str,
        percussion_style: str,
        riff_density: float,
        variety_amount: float,
        rng: random.Random,
    ) -> list[SectionPlan]:
        shaped: list[SectionPlan] = []
        for section in sections:
            layers = list(dict.fromkeys(section.layers))
            if counter_sound != "none" and section.name in {"verse_a", "verse_b", "bridge"}:
                if rng.random() < 0.65 + variety_amount * 0.2 and "counter" not in layers:
                    layers.append("counter")
            if percussion_style != "none" and section.name in {"chorus", "verse_b"}:
                if rng.random() < 0.55 + variety_amount * 0.25 and "percussion" not in layers:
                    layers.append("percussion")
            if riff_density > 0.55 and section.name in {"verse_a", "verse_b"}:
                if rng.random() < 0.35 and "lead" not in layers:
                    layers.append("lead")
            if section.variation == "breakdown":
                layers = [layer for layer in layers if layer not in {"lead", "percussion"}]
            shaped.append(
                SectionPlan(
                    name=section.name,
                    bars=section.bars,
                    intensity=section.intensity,
                    layers=layers,
                    variation=section.variation,
                    lead_density=section.lead_density,
                )
            )
        return shaped

    @staticmethod
    def _pick(value: Any, allowed: tuple[str, ...], default: str) -> str:
        return value if isinstance(value, str) and value in allowed else default

    @staticmethod
    def _pick_bars(value: Any, default: int) -> int:
        allowed = (4, 8, 12, 16)
        try:
            value_int = int(value)
        except (TypeError, ValueError):
            return default
        if value_int in allowed:
            return value_int
        return min(allowed, key=lambda bar_count: abs(bar_count - value_int))

    @staticmethod
    def _bounded_int(value: Any, minimum: int, maximum: int, default: int) -> int:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            parsed = default
        return max(minimum, min(maximum, parsed))

    @staticmethod
    def _bounded_float(value: Any, minimum: float, maximum: float, default: float) -> float:
        try:
            parsed = float(value)
        except (TypeError, ValueError):
            parsed = default
        return max(minimum, min(maximum, parsed))

    @staticmethod
    def _clean_text(value: Any, default: str) -> str:
        if not isinstance(value, str):
            return default
        cleaned = " ".join(value.strip().split())
        return cleaned[:180] if cleaned else default

    @staticmethod
    def _infer_choice(prompt_text: str, keyword_map: dict[str, str], default: str) -> str:
        for token, choice in keyword_map.items():
            if token in prompt_text:
                return choice
        return default


class OllamaPlanner(LLMPlanner):
    def __init__(
        self,
        model: str = "phi4-mini",
        host: str = "http://127.0.0.1:11434",
        timeout_seconds: int = 90,
        temperature: float = 0.95,
    ) -> None:
        super().__init__(
            provider=OllamaPlanProvider(
                model=model,
                host=host,
                timeout_seconds=timeout_seconds,
                temperature=temperature,
            )
        )
