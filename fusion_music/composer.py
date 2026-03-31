from __future__ import annotations

import random
from typing import Any

import pretty_midi

from .defaults import BASS_PATTERNS, DRUM_PATTERNS, LEAD_PATTERNS, PIANO_PATTERNS
from .harmony import HarmonyEngine
from .models import SectionPlan, TrackPlan
from .theory import chord_root, chord_tones, nearest_scale_note, scale_notes_for_range, voice_led_chord


class FusionComposer:
    def __init__(self, plan: TrackPlan) -> None:
        self.plan = plan
        self.rng = random.Random(plan.seed)
        self.bar_duration = 240.0 / plan.bpm
        self.sixteenth_duration = self.bar_duration / 16.0
        self.scale_pool = scale_notes_for_range(plan.key, plan.mode, 36, 96)
        self.upper_scale_pool = [pitch for pitch in self.scale_pool if 67 <= pitch <= 96]
        self.mid_scale_pool = [pitch for pitch in self.scale_pool if 55 <= pitch <= 88]
        self.lower_scale_pool = [pitch for pitch in self.scale_pool if 28 <= pitch <= 60]
        self.harmony = HarmonyEngine(plan)
        self.base_motif = self._generate_base_motif()
        self.base_riff_steps = self._generate_riff_steps(plan.riff_density)
        self.base_counter_steps = self._generate_counter_steps()
        self.instruments = self._build_instruments()

    def compose(self) -> tuple[pretty_midi.PrettyMIDI, dict[str, Any]]:
        midi = pretty_midi.PrettyMIDI(initial_tempo=self.plan.bpm)
        section_summaries: list[dict[str, Any]] = []
        current_time = 0.0
        previous_voicing: list[int] | None = None
        previous_degree: str | None = None

        for section_index, section in enumerate(self.plan.sections):
            next_section_name = self.plan.sections[section_index + 1].name if section_index + 1 < len(self.plan.sections) else None
            progression, previous_degree = self.harmony.generate_section_progression(
                section,
                next_section_name=next_section_name,
                previous_degree=previous_degree,
            )
            section_start = current_time
            section_end = section_start + section.bars * self.bar_duration

            for bar_index in range(section.bars):
                raw_chord = progression[bar_index]
                chord_symbol = self._embellish_chord_symbol(raw_chord, section, section_index, bar_index)
                next_symbol = progression[(bar_index + 1) % len(progression)]
                bar_start = section_start + bar_index * self.bar_duration
                voicing = voice_led_chord(
                    chord_symbol,
                    self.plan.key,
                    self.plan.mode,
                    previous=previous_voicing,
                    rootless=True,
                )

                if self._role_active(section, "keys"):
                    self._write_keys(section, voicing, bar_start, bar_index)
                if self._role_active(section, "bass"):
                    self._write_bass(section, chord_symbol, next_symbol, bar_start, bar_index)
                if self._role_active(section, "lead"):
                    self._write_lead(section, chord_symbol, bar_start, bar_index)
                if self._role_active(section, "counter"):
                    self._write_counter(section, chord_symbol, bar_start, bar_index)
                if self._role_active(section, "pad"):
                    self._write_pad(section, voicing, bar_start, section_end, bar_index)
                if self._role_active(section, "drums"):
                    self._write_drums(section, bar_start, bar_index)
                if self._role_active(section, "percussion"):
                    self._write_percussion(section, bar_start, bar_index)

                previous_voicing = voicing

            if self._role_active(section, "drums") and section_index < len(self.plan.sections) - 1:
                if section.variation in {"lift", "release"}:
                    self._write_fill(section_end - self.bar_duration * 0.5)

            section_summaries.append(
                {
                    "name": section.name,
                    "bars": section.bars,
                    "start_seconds": round(section_start, 3),
                    "end_seconds": round(section_end, 3),
                    "progression": progression,
                    "layers": section.layers,
                    "variation": section.variation,
                }
            )
            current_time = section_end

        for instrument in self.instruments.values():
            if instrument.notes:
                instrument.notes.sort(key=lambda note: note.start)
                midi.instruments.append(instrument)

        return midi, {
            "duration_seconds": round(current_time, 3),
            "total_bars": sum(section.bars for section in self.plan.sections),
            "sections": section_summaries,
            "instrument_palette": {
                "keys_sound": self.plan.keys_sound,
                "bass_sound": self.plan.bass_sound,
                "lead_sound": self.plan.lead_sound,
                "pad_sound": self.plan.pad_sound,
                "counter_sound": self.plan.counter_sound,
                "percussion_style": self.plan.percussion_style,
                "riff_shape": self.plan.riff_shape,
                "motif_variation": self.plan.motif_variation,
            },
        }

    def _build_instruments(self) -> dict[str, pretty_midi.Instrument]:
        program_maps = {
            "keys": {
                "rhodes": 4,
                "upright_piano": 0,
                "wurlitzer": 5,
                "jazz_guitar": 26,
                "detuned_keys": 5,
            },
            "bass": {
                "electric_bass": 33,
                "upright_bass": 32,
                "fretless_bass": 35,
                "sine_sub": 38,
            },
            "lead": {
                "vibes": 11,
                "flute": 73,
                "muted_trumpet": 59,
                "analog_lead": 80,
                "electric_piano_lead": 4,
            },
            "pad": {
                "warm_pad": 89,
                "string_pad": 49,
                "choir_pad": 52,
                "organ_pad": 17,
            },
            "counter": {
                "none": 0,
                "bell_pluck": 8,
                "guitar_harmonics": 31,
                "clarinet": 71,
                "marimba": 12,
            },
        }

        return {
            "keys": pretty_midi.Instrument(program=program_maps["keys"][self.plan.keys_sound], name=f"keys:{self.plan.keys_sound}"),
            "bass": pretty_midi.Instrument(program=program_maps["bass"][self.plan.bass_sound], name=f"bass:{self.plan.bass_sound}"),
            "lead": pretty_midi.Instrument(program=program_maps["lead"][self.plan.lead_sound], name=f"lead:{self.plan.lead_sound}"),
            "pad": pretty_midi.Instrument(program=program_maps["pad"][self.plan.pad_sound], name=f"pad:{self.plan.pad_sound}"),
            "counter": pretty_midi.Instrument(program=program_maps["counter"][self.plan.counter_sound], name=f"counter:{self.plan.counter_sound}"),
            "drums": pretty_midi.Instrument(program=0, is_drum=True, name=f"drums:{self.plan.drum_style}"),
            "percussion": pretty_midi.Instrument(program=0, is_drum=True, name=f"percussion:{self.plan.percussion_style}"),
        }

    def _generate_base_motif(self) -> list[int]:
        seed_pattern = list(self.rng.choice(LEAD_PATTERNS[self.plan.lead_style]))
        shape = self.plan.riff_shape

        if shape == "ascending":
            motif = sorted(seed_pattern)
        elif shape == "descending":
            motif = sorted(seed_pattern, reverse=True)
        elif shape == "arched":
            left = sorted(seed_pattern[: len(seed_pattern) // 2 + 1])
            right = sorted(seed_pattern[len(seed_pattern) // 2 :], reverse=True)
            motif = left + right
        elif shape == "circular":
            rotate = self.rng.randrange(len(seed_pattern))
            motif = seed_pattern[rotate:] + seed_pattern[:rotate]
        elif shape == "question_answer":
            motif = seed_pattern[:3] + [degree - 2 for degree in seed_pattern[:3]]
        else:
            motif = []
            current = 0
            for degree in seed_pattern[:6]:
                current += 1 if degree >= current else 0
                motif.append(current)

        return [max(-6, min(9, int(value))) for value in motif[:8]]

    def _generate_riff_steps(self, density: float) -> list[int]:
        count = max(3, min(8, int(round(2 + density * 7))))
        candidates = [0, 2, 4, 6, 8, 10, 12, 14]
        if density > 0.55:
            candidates.extend([1, 5, 7, 11, 15])
        chosen = {0}
        while len(chosen) < count:
            chosen.add(self.rng.choice(candidates))
        return sorted(chosen)

    def _generate_counter_steps(self) -> list[int]:
        steps = [step + 1 for step in self.base_riff_steps if step + 1 < 16 and step % 4 == 0]
        if not steps:
            steps = [1, 7, 11, 15]
        return sorted(set(steps))

    def _role_active(self, section: SectionPlan, role: str) -> bool:
        if role not in section.layers:
            return False
        if role == "counter" and self.plan.counter_sound == "none":
            return False
        if role == "percussion" and self.plan.percussion_style == "none":
            return False
        return True

    def _write_keys(self, section: SectionPlan, voicing: list[int], bar_start: float, bar_index: int) -> None:
        patterns = PIANO_PATTERNS[self.plan.piano_style]
        base_pattern = list(patterns[self.rng.randrange(len(patterns))])
        pattern = self._mutate_step_pattern(base_pattern, section, bar_index, role="keys")
        velocity = int(42 + section.intensity * 32)

        for hit_index, step in enumerate(pattern):
            start = self._step_time(bar_start, step, swingable=True)
            duration_steps = 3 if self.plan.keys_sound == "jazz_guitar" else 6 if self.plan.piano_style == "lush_spread" else 4
            end = min(bar_start + self.bar_duration, start + duration_steps * self.sixteenth_duration)
            chord_slice = voicing

            if self.plan.piano_style == "broken_voicings":
                split = max(2, len(voicing) - 1)
                chord_slice = voicing[:split] if hit_index % 2 == 0 else voicing[-split:]
            elif self.plan.keys_sound == "jazz_guitar":
                chord_slice = voicing[: min(3, len(voicing))]

            for note_offset, pitch in enumerate(chord_slice):
                offset = note_offset * (0.012 if self.plan.keys_sound in {"jazz_guitar", "upright_piano"} else 0.007)
                self._add_note(
                    self.instruments["keys"],
                    pitch,
                    start + offset,
                    end,
                    velocity + self.rng.randint(-10, 10),
                )

    def _write_bass(
        self,
        section: SectionPlan,
        chord_symbol: str,
        next_symbol: str,
        bar_start: float,
        bar_index: int,
    ) -> None:
        base_pattern = list(BASS_PATTERNS[self.plan.bass_style][bar_index % len(BASS_PATTERNS[self.plan.bass_style])])
        pattern = self._mutate_step_pattern(base_pattern, section, bar_index, role="bass")
        root = chord_root(chord_symbol, self.plan.key, self.plan.mode, octave=2)
        next_root = chord_root(next_symbol, self.plan.key, self.plan.mode, octave=2)
        chord_pool = chord_tones(chord_symbol, self.plan.key, self.plan.mode, octave=2, rootless=False)
        velocity = int(58 + section.intensity * 28)

        for note_index, step in enumerate(pattern):
            start = self._step_time(bar_start, step, swingable=False)
            next_step = pattern[note_index + 1] if note_index + 1 < len(pattern) else 16
            end = bar_start + min(16, next_step) * self.sixteenth_duration * 0.96
            pitch = self._choose_bass_pitch(root, next_root, chord_pool, note_index, section)
            self._add_note(
                self.instruments["bass"],
                pitch,
                start,
                end,
                velocity + self.rng.randint(-8, 8),
            )

    def _choose_bass_pitch(
        self,
        root: int,
        next_root: int,
        chord_pool: list[int],
        note_index: int,
        section: SectionPlan,
    ) -> int:
        if self.plan.bass_style == "root_pocket":
            choices = [root, root + 12, chord_pool[min(2, len(chord_pool) - 1)] - 12, root + 14]
            pitch = choices[note_index % len(choices)]
        elif self.plan.bass_style == "walking_glide":
            walk = [
                root,
                chord_pool[min(1, len(chord_pool) - 1)] - 12,
                chord_pool[min(2, len(chord_pool) - 1)] - 12,
                next_root - 1 if next_root >= root else next_root + 1,
            ]
            pitch = walk[note_index % len(walk)]
        elif self.plan.bass_style == "counter_melody":
            target = root + [0, 7, 10, 14, 12, 7][note_index % 6]
            pitch = nearest_scale_note(target, self.lower_scale_pool)
        else:
            bounce = [root, root + 12, root + 7, root + 12]
            pitch = bounce[note_index % len(bounce)]

        if self.plan.bass_sound == "upright_bass":
            pitch -= 2 if section.intensity < 0.6 and note_index % 2 == 0 else 0
        elif self.plan.bass_sound == "sine_sub":
            pitch -= 5
        return max(24, min(55, pitch))

    def _write_lead(self, section: SectionPlan, chord_symbol: str, bar_start: float, bar_index: int) -> None:
        if self.rng.random() > max(0.12, section.lead_density + self.plan.riff_density * 0.15):
            return

        motif = self._mutate_motif(self.base_motif, section, bar_index)
        rhythm = self._mutate_riff_steps(self.base_riff_steps, section, bar_index, role="lead")
        anchor = nearest_scale_note(chord_root(chord_symbol, self.plan.key, self.plan.mode, octave=5) + 12, self.upper_scale_pool)
        anchor_index = self.upper_scale_pool.index(anchor)
        velocity = int(54 + section.intensity * 34)

        for note_index, step in enumerate(rhythm[: len(motif)]):
            if self.rng.random() > min(0.98, section.lead_density + self.plan.riff_density * 0.28):
                continue

            degree_offset = motif[note_index]
            scale_index = max(0, min(len(self.upper_scale_pool) - 1, anchor_index + degree_offset))
            pitch = self.upper_scale_pool[scale_index]
            if self.plan.lead_sound == "muted_trumpet":
                pitch = max(68, min(90, pitch))
            elif self.plan.lead_sound == "flute":
                pitch = max(72, min(96, pitch + 2))
            elif self.plan.lead_sound == "analog_lead":
                pitch = max(65, min(94, pitch))

            start = self._step_time(bar_start, step, swingable=True)
            next_step = rhythm[note_index + 1] if note_index + 1 < len(rhythm) else 16
            duration = max(2, next_step - step)
            end = min(bar_start + self.bar_duration, start + duration * self.sixteenth_duration * 0.88)
            self._add_note(
                self.instruments["lead"],
                pitch,
                start,
                end,
                velocity + self.rng.randint(-12, 12),
            )

    def _write_counter(self, section: SectionPlan, chord_symbol: str, bar_start: float, bar_index: int) -> None:
        if self.rng.random() > min(0.78, 0.26 + self.plan.variety_amount * 0.4):
            return

        motif = self._mutate_motif([-degree for degree in self.base_motif[:5]], section, bar_index, counter=True)
        rhythm = self._mutate_riff_steps(self.base_counter_steps, section, bar_index, role="counter")
        anchor = nearest_scale_note(chord_root(chord_symbol, self.plan.key, self.plan.mode, octave=4) + 7, self.mid_scale_pool)
        anchor_index = self.mid_scale_pool.index(anchor)
        velocity = int(36 + section.intensity * 24)

        for note_index, step in enumerate(rhythm[: len(motif)]):
            if self.rng.random() > 0.62:
                continue

            scale_index = max(0, min(len(self.mid_scale_pool) - 1, anchor_index + motif[note_index]))
            pitch = self.mid_scale_pool[scale_index]
            if self.plan.counter_sound == "guitar_harmonics":
                pitch = max(60, min(88, pitch + 12))
            elif self.plan.counter_sound == "clarinet":
                pitch = max(58, min(84, pitch))

            start = self._step_time(bar_start, step, swingable=True)
            next_step = rhythm[note_index + 1] if note_index + 1 < len(rhythm) else 16
            end = min(bar_start + self.bar_duration, start + max(2, next_step - step) * self.sixteenth_duration * 0.74)
            self._add_note(
                self.instruments["counter"],
                pitch,
                start,
                end,
                velocity + self.rng.randint(-8, 8),
            )

    def _write_pad(
        self,
        section: SectionPlan,
        voicing: list[int],
        bar_start: float,
        section_end: float,
        bar_index: int,
    ) -> None:
        if bar_index % 2 == 1 and section.name not in {"chorus", "outro"}:
            return

        hold_bars = 1 if self.plan.pad_sound == "organ_pad" else 2 if bar_index + 1 < section.bars else 1
        end = min(section_end, bar_start + self.bar_duration * hold_bars)
        pad_notes = sorted({pitch - 12 for pitch in voicing[:3]} | {voicing[-1] - 12})
        velocity = int(30 + section.intensity * 18)

        for pitch in pad_notes:
            self._add_note(
                self.instruments["pad"],
                max(43, min(86, pitch)),
                bar_start,
                end,
                velocity + self.rng.randint(-5, 6),
            )

    def _write_drums(self, section: SectionPlan, bar_start: float, bar_index: int) -> None:
        pattern_bank = DRUM_PATTERNS[self.plan.drum_style]
        base_pattern = pattern_bank[(bar_index + self.rng.randrange(len(pattern_bank))) % len(pattern_bank)]
        pattern = self._mutate_drum_pattern(base_pattern, section, bar_index)

        if bar_index == 0 and section.name == "chorus":
            self._add_drum_note("drums", 49, bar_start, 0.35, 92)

        for step in range(16):
            if pattern["kick"][step] and self.rng.random() < min(1.0, 0.8 + section.intensity * 0.24):
                self._add_drum_note("drums", 36, self._step_time(bar_start, step, swingable=False), 0.18, int(84 + section.intensity * 30))
            if pattern["snare"][step]:
                pitch = 39 if self.plan.percussion_style == "rimshot" and self.rng.random() < 0.25 else 38
                self._add_drum_note("drums", pitch, self._step_time(bar_start, step, swingable=False), 0.16, int(70 + section.intensity * 22))
            if pattern["hat"][step] and (section.intensity > 0.3 or step % 4 == 0):
                self._add_drum_note("drums", 42, self._step_time(bar_start, step, swingable=True), 0.08, int(36 + section.intensity * 20))
            if pattern["ghost"][step] and section.intensity > 0.4 and self.rng.random() < min(0.9, section.intensity + self.plan.variety_amount * 0.2):
                self._add_drum_note("drums", 37, self._step_time(bar_start, step, swingable=True), 0.05, int(24 + section.intensity * 12))
            if pattern["open"][step] and section.intensity > 0.5:
                self._add_drum_note("drums", 46, self._step_time(bar_start, step, swingable=True), 0.15, int(40 + section.intensity * 18))

    def _write_percussion(self, section: SectionPlan, bar_start: float, bar_index: int) -> None:
        style = self.plan.percussion_style
        if style == "none":
            return

        if style == "shaker":
            steps = [1, 3, 5, 7, 9, 11, 13, 15]
            pitch = 82
            duration = 0.05
        elif style == "ride":
            steps = [0, 4, 8, 12, 14]
            pitch = 51
            duration = 0.12
        elif style == "conga":
            steps = [0, 3, 6, 10, 14]
            pitch = 64 if bar_index % 2 == 0 else 62
            duration = 0.10
        else:
            steps = [4, 12]
            pitch = 39
            duration = 0.08

        steps = self._mutate_riff_steps(steps, section, bar_index, role="percussion")
        velocity = int(24 + section.intensity * 26)
        for step in steps:
            if self.rng.random() > min(0.95, 0.55 + self.plan.variety_amount * 0.3):
                continue
            self._add_drum_note("percussion", pitch, self._step_time(bar_start, step, swingable=True), duration, velocity + self.rng.randint(-6, 6))

    def _write_fill(self, start_time: float) -> None:
        fill = [
            (0.00, 50, 72),
            (0.08, 47, 70),
            (0.16, 41, 76),
            (0.24, 38, 84),
            (0.34, 49, 92),
        ]
        for offset, pitch, velocity in fill:
            self._add_drum_note("drums", pitch, start_time + offset, 0.12, velocity)

    def _mutate_step_pattern(self, pattern: list[int], section: SectionPlan, bar_index: int, role: str) -> list[int]:
        steps = sorted({max(0, min(15, int(step))) for step in pattern})
        amount = self.plan.variety_amount

        if section.variation == "breakdown" and len(steps) > 2:
            steps = steps[::2]
        if section.variation in {"lift", "release"} and self.rng.random() < 0.7:
            steps.append(self.rng.choice([11, 14, 15]))
        if section.variation == "answer" and self.rng.random() < 0.5:
            steps = [(step + 2) % 16 for step in steps]

        if self.rng.random() < amount * 0.7:
            shift = self.rng.choice([0, 1, 2, 3])
            steps = [((step + shift) % 16) for step in steps]
        if self.rng.random() < amount * 0.55 and len(steps) > 2:
            steps.pop(self.rng.randrange(len(steps)))
        if self.rng.random() < amount * 0.65 and len(steps) < 8:
            steps.append(self.rng.randrange(16))
        if role == "bass":
            steps.append(0)
        if role == "keys" and self.plan.keys_sound == "jazz_guitar" and 0 not in steps:
            steps.append(0)

        return sorted({step % 16 for step in steps})

    def _mutate_drum_pattern(self, pattern: dict[str, list[int]], section: SectionPlan, bar_index: int) -> dict[str, list[int]]:
        mutated = {name: list(values) for name, values in pattern.items()}
        amount = self.plan.variety_amount

        for lane_name, lane in mutated.items():
            for step in range(len(lane)):
                if lane_name == "hat" and self.rng.random() < amount * 0.12:
                    lane[step] = 1 - lane[step]
                elif lane_name in {"kick", "ghost"} and self.rng.random() < amount * 0.08:
                    lane[step] = 1 if lane[step] == 0 and step not in {4, 12} else lane[step]

        if section.variation == "breakdown":
            mutated["kick"] = [value if index in {0, 8} else 0 for index, value in enumerate(mutated["kick"])]
            mutated["hat"] = [value if index % 4 == 0 else 0 for index, value in enumerate(mutated["hat"])]
        elif section.variation in {"lift", "release"}:
            mutated["hat"][self.rng.choice([11, 13, 15])] = 1
            mutated["ghost"][self.rng.choice([5, 7, 9, 11, 13])] = 1

        if bar_index % 4 == 3 and self.rng.random() < amount * 0.55:
            mutated["kick"][15] = 1

        return mutated

    def _mutate_motif(self, motif: list[int], section: SectionPlan, bar_index: int, counter: bool = False) -> list[int]:
        values = list(motif)
        variation = self.plan.motif_variation

        if variation == "sequence":
            shift = (bar_index % 3) - 1
            values = [value + shift for value in values]
        elif variation == "rhythm_flip":
            values = list(reversed(values))
        elif variation == "ornament":
            ornamented: list[int] = []
            for value in values:
                ornamented.extend([value, value + self.rng.choice([-1, 1])])
                if len(ornamented) >= len(values) + 2:
                    break
            values = ornamented[:8]
        elif variation == "invert":
            pivot = values[0] if values else 0
            values = [pivot - (value - pivot) for value in values]
        elif variation == "expand":
            values = [int(round(value * 1.4)) for value in values]
        elif variation == "call_response":
            midpoint = max(2, len(values) // 2)
            values = values[:midpoint] + [value - 2 for value in values[:midpoint]]

        if section.variation == "breakdown":
            values = values[: max(2, len(values) // 2)]
        elif section.variation == "answer":
            values = [value - 1 for value in values]
        elif section.variation == "release":
            values = values[1:] + values[:1]
        elif section.variation == "lift":
            values = values + [values[-1] + 2] if values else values

        if counter:
            values = [max(-8, min(6, int(value))) for value in values]
        else:
            values = [max(-6, min(10, int(value))) for value in values]
        return values[:8]

    def _mutate_riff_steps(self, steps: list[int], section: SectionPlan, bar_index: int, role: str) -> list[int]:
        mutated = list(sorted({step % 16 for step in steps}))
        amount = self.plan.variety_amount

        if self.plan.motif_variation == "rhythm_flip":
            mutated = sorted({(15 - step) for step in mutated})
        elif self.plan.motif_variation == "call_response" and bar_index % 2 == 1:
            mutated = sorted({(step + 2) % 16 for step in mutated})

        if section.variation == "breakdown":
            mutated = mutated[::2] or mutated[:1]
        elif section.variation in {"lift", "release"} and self.rng.random() < amount * 0.85:
            mutated.append(self.rng.choice([13, 14, 15]))

        if role == "counter":
            mutated = [step for step in mutated if step % 2 == 1] or mutated
        if role == "percussion" and self.rng.random() < amount * 0.5:
            mutated.append(self.rng.choice([5, 11, 15]))

        return sorted({step % 16 for step in mutated})[:8]

    def _embellish_chord_symbol(self, chord_symbol: str, section: SectionPlan, section_index: int, bar_index: int) -> str:
        if self.rng.random() > self.plan.substitution_rate * max(0.25, section.intensity):
            return chord_symbol

        replacements = (
            ("maj7", "maj9"),
            ("maj9", "maj13"),
            ("7", "9"),
            ("9", "11"),
            ("11", "13"),
            ("m7", "m9"),
            ("m9", "m11"),
            ("m11", "m13"),
        )
        for left, right in replacements:
            if chord_symbol.endswith(left):
                return chord_symbol[: -len(left)] + right

        if bar_index == 0 and section_index % 2 == 1 and chord_symbol.endswith("13"):
            return chord_symbol[:-2] + "9"
        return chord_symbol

    def _step_time(self, bar_start: float, step: int, swingable: bool) -> float:
        time = bar_start + step * self.sixteenth_duration
        if swingable and step % 4 >= 2:
            time += self.plan.swing * self.sixteenth_duration
        jitter = self.rng.uniform(-1.0, 1.0) * self.plan.humanization * self.sixteenth_duration
        return max(bar_start, time + jitter)

    def _add_note(
        self,
        instrument: pretty_midi.Instrument,
        pitch: int,
        start: float,
        end: float,
        velocity: int,
    ) -> None:
        if end <= start:
            end = start + 0.05
        instrument.notes.append(
            pretty_midi.Note(
                velocity=max(1, min(127, int(velocity))),
                pitch=max(0, min(127, int(pitch))),
                start=max(0.0, start),
                end=max(start + 0.01, end),
            )
        )

    def _add_drum_note(self, role: str, pitch: int, start: float, duration: float, velocity: int) -> None:
        self.instruments[role].notes.append(
            pretty_midi.Note(
                velocity=max(1, min(127, int(velocity))),
                pitch=pitch,
                start=max(0.0, start),
                end=max(start + 0.01, start + duration),
            )
        )
