from __future__ import annotations

import math

import numpy as np
import pretty_midi
from scipy import signal

from .ambience import AmbienceRenderer
from .models import TrackPlan


class AudioRenderer:
    def __init__(self, sample_rate: int = 44_100, seed: int = 0) -> None:
        self.sample_rate = sample_rate
        self.rng = np.random.default_rng(seed)
        self.ambience_renderer = AmbienceRenderer(sample_rate=sample_rate, seed=seed)

    def render(self, midi: pretty_midi.PrettyMIDI, plan: TrackPlan) -> tuple[np.ndarray, dict[str, np.ndarray]]:
        duration = max(8.0, midi.get_end_time() + 2.5)
        total_samples = int(duration * self.sample_rate)
        stems: dict[str, np.ndarray] = {}
        kick_hits: list[float] = []

        for instrument in midi.instruments:
            name = instrument.name or f"program_{instrument.program}"
            if instrument.is_drum:
                stem, hits = self._render_drums(instrument, total_samples)
                kick_hits.extend(hits)
            else:
                profile = self._instrument_profile(instrument)
                mono = self._render_tonal_instrument(
                    instrument,
                    total_samples,
                    role=profile["role"],
                    family=profile["family"],
                )
                stem = self._pan(mono, profile["pan"])
                if profile["widen"][0] > 0:
                    stem = self._widen(stem, profile["widen"][0], profile["widen"][1])
            stems[name] = stem

        if plan.ambience_layers:
            stems["ambience"] = self.ambience_renderer.render(duration, plan.ambience_layers)

        sidechain = self._sidechain_envelope(total_samples, kick_hits)
        for name, stem in list(stems.items()):
            lower_name = name.lower()
            if "drum" in lower_name or "percussion" in lower_name:
                continue
            if "bass:" in lower_name:
                stems[name] = stem * sidechain[:, None] * 0.93
            elif "ambience" in lower_name:
                stems[name] = stem * sidechain[:, None] * 0.985
            else:
                stems[name] = stem * sidechain[:, None]

        mix = np.zeros((total_samples, 2), dtype=np.float64)
        for stem in stems.values():
            mix += stem

        mix = self._master_bus(mix, plan)
        peak = np.max(np.abs(mix))
        if peak > 0:
            mix = mix / peak * 0.90

        return mix.astype(np.float32), {name: stem.astype(np.float32) for name, stem in stems.items()}

    def _render_tonal_instrument(
        self,
        instrument: pretty_midi.Instrument,
        total_samples: int,
        role: str,
        family: str,
    ) -> np.ndarray:
        mono = np.zeros(total_samples, dtype=np.float64)

        for note in instrument.notes:
            start = max(0, int(note.start * self.sample_rate))
            end = min(total_samples, int(note.end * self.sample_rate))
            if end <= start:
                continue

            length = end - start
            tone = self._synthesize_note(role, family, note.pitch, length, note.velocity / 127.0)
            mono[start:end] += tone[:length]

        if role == "bass":
            mono = self._apply_filter(mono, "lowpass", 340)
            mono = np.tanh(mono * 1.35)
        elif role == "keys":
            mono = self._apply_filter(mono, "lowpass", 5_200 if family != "jazz_guitar" else 4_200)
            mono = self._simple_delay(mono, 0.16, 2, 0.34, 0.14)
        elif role == "lead":
            mono = self._apply_filter(mono, "highpass", 300)
            mono = self._apply_filter(mono, "lowpass", 7_200)
            mono = self._simple_delay(mono, 0.23, 3, 0.42, 0.24)
        elif role == "pad":
            mono = self._apply_filter(mono, "lowpass", 2_800)
            mono = self._simple_delay(mono, 0.29, 3, 0.44, 0.26)
        elif role == "counter":
            mono = self._apply_filter(mono, "highpass", 420)
            mono = self._apply_filter(mono, "lowpass", 5_800)
            mono = self._simple_delay(mono, 0.18, 2, 0.3, 0.16)

        return mono

    def _render_drums(self, instrument: pretty_midi.Instrument, total_samples: int) -> tuple[np.ndarray, list[float]]:
        stereo = np.zeros((total_samples, 2), dtype=np.float64)
        kick_hits: list[float] = []

        for note in instrument.notes:
            start = max(0, int(note.start * self.sample_rate))
            if start >= total_samples:
                continue

            velocity = note.velocity / 127.0
            if note.pitch in {35, 36}:
                mono = self._kick(velocity)
                pan = 0.0
                kick_hits.append(note.start)
            elif note.pitch in {37}:
                mono = self._rim(velocity)
                pan = -0.14
            elif note.pitch in {38, 40, 39}:
                mono = self._clap(velocity) if note.pitch == 39 else self._snare(velocity)
                pan = -0.03
            elif note.pitch in {42, 44, 46, 82}:
                mono = self._hat(velocity, open_hat=note.pitch == 46, shaker=note.pitch == 82)
                pan = 0.24
            elif note.pitch in {49, 51}:
                mono = self._cymbal(velocity, bright=note.pitch == 49)
                pan = 0.12
            elif note.pitch in {41, 47, 50}:
                mono = self._tom(velocity, note.pitch)
                pan = -0.08 if note.pitch == 41 else 0.08
            elif note.pitch in {62, 64}:
                mono = self._conga(velocity, low=note.pitch == 64)
                pan = -0.05 if note.pitch == 64 else 0.07
            else:
                mono = self._hat(velocity, open_hat=False, shaker=False)
                pan = 0.0

            end = min(total_samples, start + len(mono))
            stereo[start:end] += self._pan(mono[: end - start], pan)

        stereo = np.tanh(stereo * 1.15)
        return stereo, kick_hits

    def _synthesize_note(self, role: str, family: str, pitch: int, length: int, velocity: float) -> np.ndarray:
        t = np.arange(length) / self.sample_rate
        freq = pretty_midi.note_number_to_hz(pitch)

        if role == "keys":
            if family == "rhodes":
                wave = (
                    0.62 * np.sin(2 * np.pi * freq * t)
                    + 0.18 * signal.sawtooth(2 * np.pi * freq * t, 0.58)
                    + 0.12 * np.sin(2 * np.pi * freq * 2 * t)
                    + 0.08 * np.sin(2 * np.pi * freq * 3 * t)
                )
                env = self._adsr(length, 0.006, 0.14, 0.58, 0.18)
                return wave * env * velocity * 0.32
            if family == "upright_piano":
                wave = (
                    0.58 * np.sin(2 * np.pi * freq * t)
                    + 0.24 * np.sin(2 * np.pi * freq * 2 * t)
                    + 0.10 * signal.sawtooth(2 * np.pi * freq * t, 0.52)
                )
                env = self._adsr(length, 0.004, 0.09, 0.44, 0.12)
                return wave * env * velocity * 0.34
            if family == "wurlitzer":
                wave = (
                    0.46 * signal.sawtooth(2 * np.pi * freq * t, 0.5)
                    + 0.26 * signal.square(2 * np.pi * freq * t)
                    + 0.12 * np.sin(2 * np.pi * freq * 2 * t)
                )
                env = self._adsr(length, 0.005, 0.11, 0.5, 0.14)
                return np.tanh(wave * 1.12) * env * velocity * 0.28
            if family == "jazz_guitar":
                wave = (
                    0.48 * signal.sawtooth(2 * np.pi * freq * t, 0.22)
                    + 0.22 * np.sin(2 * np.pi * freq * t)
                    + 0.16 * np.sin(2 * np.pi * freq * 2 * t)
                )
                env = self._adsr(length, 0.002, 0.06, 0.34, 0.10)
                return self._apply_filter(wave * env, "lowpass", 2_800) * velocity * 0.30

            detuned = signal.sawtooth(2 * np.pi * freq * 0.997 * t, 0.54) + signal.sawtooth(
                2 * np.pi * freq * 1.003 * t,
                0.46,
            )
            env = self._adsr(length, 0.006, 0.18, 0.54, 0.16)
            return detuned * env * velocity * 0.17

        if role == "bass":
            if family == "upright_bass":
                wave = (
                    0.78 * np.sin(2 * np.pi * freq * t)
                    + 0.18 * np.sin(2 * np.pi * freq * 2 * t)
                    + 0.08 * signal.sawtooth(2 * np.pi * freq * t, 0.35)
                )
                env = self._adsr(length, 0.003, 0.07, 0.48, 0.08)
                return wave * env * velocity * 0.34
            if family == "fretless_bass":
                vibrato = 1 + 0.004 * np.sin(2 * np.pi * 4.8 * t)
                wave = (
                    0.82 * np.sin(2 * np.pi * freq * vibrato * t)
                    + 0.16 * np.sin(2 * np.pi * freq * 2 * t)
                )
                env = self._adsr(length, 0.005, 0.08, 0.68, 0.08)
                return wave * env * velocity * 0.30
            if family == "sine_sub":
                wave = 0.92 * np.sin(2 * np.pi * freq * t)
                env = self._adsr(length, 0.004, 0.03, 0.82, 0.05)
                return wave * env * velocity * 0.30

            wave = (
                0.84 * np.sin(2 * np.pi * freq * t)
                + 0.24 * np.sin(2 * np.pi * freq * 0.5 * t)
                + 0.08 * signal.square(2 * np.pi * freq * t)
            )
            env = self._adsr(length, 0.004, 0.08, 0.72, 0.06)
            return wave * env * velocity * 0.32

        if role == "lead":
            if family == "vibes":
                wave = (
                    0.70 * np.sin(2 * np.pi * freq * t)
                    + 0.22 * np.sin(2 * np.pi * freq * 3 * t)
                    + 0.08 * np.sin(2 * np.pi * freq * 5 * t)
                )
                env = self._adsr(length, 0.004, 0.16, 0.52, 0.20)
                return wave * env * velocity * 0.28
            if family == "flute":
                breath = self.rng.standard_normal(length) * 0.03
                breath = self._apply_filter(breath, "bandpass", (1_500, 8_500))
                wave = 0.82 * np.sin(2 * np.pi * freq * t) + 0.08 * np.sin(2 * np.pi * freq * 2 * t)
                env = self._adsr(length, 0.01, 0.06, 0.72, 0.12)
                return (wave + breath) * env * velocity * 0.20
            if family == "muted_trumpet":
                wave = (
                    0.42 * signal.sawtooth(2 * np.pi * freq * t, 0.48)
                    + 0.24 * signal.square(2 * np.pi * freq * t)
                    + 0.16 * np.sin(2 * np.pi * freq * 2 * t)
                )
                env = self._adsr(length, 0.006, 0.08, 0.46, 0.11)
                return self._apply_filter(wave * env, "bandpass", (600, 4_200)) * velocity * 0.34
            if family == "electric_piano_lead":
                wave = (
                    0.62 * np.sin(2 * np.pi * freq * t)
                    + 0.14 * signal.sawtooth(2 * np.pi * freq * t, 0.58)
                    + 0.10 * np.sin(2 * np.pi * freq * 2 * t)
                )
                env = self._adsr(length, 0.005, 0.10, 0.56, 0.14)
                return wave * env * velocity * 0.25

            wave = (
                0.54 * signal.sawtooth(2 * np.pi * freq * t, 0.5)
                + 0.24 * signal.square(2 * np.pi * freq * t)
                + 0.08 * np.sin(2 * np.pi * freq * 2 * t)
            )
            env = self._adsr(length, 0.005, 0.09, 0.5, 0.12)
            return wave * env * velocity * 0.22

        if role == "pad":
            if family == "string_pad":
                detuned = signal.sawtooth(2 * np.pi * freq * 0.995 * t, 0.54) + signal.sawtooth(
                    2 * np.pi * freq * 1.005 * t,
                    0.48,
                )
                env = self._adsr(length, 0.08, 0.32, 0.72, 0.46)
                return detuned * env * velocity * 0.12
            if family == "choir_pad":
                wave = (
                    0.46 * np.sin(2 * np.pi * freq * t)
                    + 0.16 * np.sin(2 * np.pi * freq * 2 * t)
                    + 0.12 * np.sin(2 * np.pi * freq * 3.5 * t)
                )
                env = self._adsr(length, 0.10, 0.30, 0.68, 0.42)
                return wave * env * velocity * 0.15
            if family == "organ_pad":
                wave = (
                    0.32 * signal.square(2 * np.pi * freq * t)
                    + 0.18 * signal.square(2 * np.pi * freq * 2 * t)
                    + 0.10 * signal.square(2 * np.pi * freq * 3 * t)
                )
                env = self._adsr(length, 0.02, 0.12, 0.82, 0.16)
                return wave * env * velocity * 0.12

            detuned = signal.sawtooth(2 * np.pi * freq * 0.997 * t, 0.54) + signal.sawtooth(
                2 * np.pi * freq * 1.003 * t,
                0.46,
            )
            wave = 0.45 * detuned + 0.18 * np.sin(2 * np.pi * freq * 0.5 * t)
            env = self._adsr(length, 0.08, 0.30, 0.66, 0.42)
            return wave * env * velocity * 0.18

        if family == "clarinet":
            wave = (
                0.62 * np.sin(2 * np.pi * freq * t)
                + 0.20 * np.sin(2 * np.pi * freq * 3 * t)
                + 0.10 * np.sin(2 * np.pi * freq * 5 * t)
            )
            env = self._adsr(length, 0.008, 0.06, 0.62, 0.12)
            return wave * env * velocity * 0.18
        if family == "marimba":
            wave = (
                0.72 * np.sin(2 * np.pi * freq * t)
                + 0.12 * np.sin(2 * np.pi * freq * 4 * t)
                + 0.08 * np.sin(2 * np.pi * freq * 7 * t)
            )
            env = self._adsr(length, 0.002, 0.05, 0.24, 0.10)
            return wave * env * velocity * 0.18
        if family == "guitar_harmonics":
            wave = (
                0.34 * np.sin(2 * np.pi * freq * 2 * t)
                + 0.24 * np.sin(2 * np.pi * freq * 3 * t)
                + 0.20 * np.sin(2 * np.pi * freq * 4 * t)
            )
            env = self._adsr(length, 0.002, 0.04, 0.28, 0.10)
            return wave * env * velocity * 0.16

        wave = (
            0.56 * np.sin(2 * np.pi * freq * t)
            + 0.22 * np.sin(2 * np.pi * freq * 2.7 * t)
            + 0.08 * np.sin(2 * np.pi * freq * 4.1 * t)
        )
        env = self._adsr(length, 0.002, 0.05, 0.22, 0.10)
        return wave * env * velocity * 0.18

    def _kick(self, velocity: float) -> np.ndarray:
        length = int(0.34 * self.sample_rate)
        t = np.arange(length) / self.sample_rate
        sweep = np.linspace(112, 42, length)
        phase = 2 * np.pi * np.cumsum(sweep) / self.sample_rate
        body = np.sin(phase) * np.exp(-t * 10.5)
        click = np.sin(2 * np.pi * 1_900 * t) * np.exp(-t * 52.0)
        return (body * 0.95 + click * 0.09) * velocity * 0.85

    def _snare(self, velocity: float) -> np.ndarray:
        length = int(0.24 * self.sample_rate)
        t = np.arange(length) / self.sample_rate
        noise = self.rng.standard_normal(length)
        noise = self._apply_filter(noise, "highpass", 1_400)
        body = np.sin(2 * np.pi * 190 * t) * np.exp(-t * 15.0)
        return (0.58 * noise * np.exp(-t * 18.0) + 0.24 * body) * velocity * 0.42

    def _clap(self, velocity: float) -> np.ndarray:
        length = int(0.18 * self.sample_rate)
        t = np.arange(length) / self.sample_rate
        noise = self.rng.standard_normal(length)
        noise = self._apply_filter(noise, "bandpass", (900, 4_800))
        envelope = np.exp(-t * 24.0) * (1.0 + 0.4 * np.sin(2 * np.pi * 28 * t))
        return noise * envelope * velocity * 0.28

    def _rim(self, velocity: float) -> np.ndarray:
        length = int(0.08 * self.sample_rate)
        t = np.arange(length) / self.sample_rate
        tone = np.sin(2 * np.pi * 1_900 * t) * np.exp(-t * 55.0)
        return tone * velocity * 0.22

    def _hat(self, velocity: float, open_hat: bool, shaker: bool) -> np.ndarray:
        length = int((0.18 if shaker else 0.22 if open_hat else 0.08) * self.sample_rate)
        t = np.arange(length) / self.sample_rate
        noise = self.rng.standard_normal(length)
        noise = self._apply_filter(noise, "highpass", 6_800 if not shaker else 5_600)
        decay = 24.0 if shaker else 18.0 if open_hat else 62.0
        gain = 0.12 if shaker else 0.16 if open_hat else 0.11
        return noise * np.exp(-t * decay) * velocity * gain

    def _cymbal(self, velocity: float, bright: bool) -> np.ndarray:
        length = int((0.8 if bright else 0.6) * self.sample_rate)
        t = np.arange(length) / self.sample_rate
        noise = self.rng.standard_normal(length)
        noise = self._apply_filter(noise, "highpass", 4_000)
        tone = np.sin(2 * np.pi * 760 * t) * np.exp(-t * 8.0)
        return (0.72 * noise * np.exp(-t * 5.2) + 0.08 * tone) * velocity * 0.15

    def _tom(self, velocity: float, pitch: int) -> np.ndarray:
        length = int(0.20 * self.sample_rate)
        t = np.arange(length) / self.sample_rate
        freq_map = {41: 140, 47: 180, 50: 220}
        freq = freq_map.get(pitch, 180)
        tone = np.sin(2 * np.pi * freq * t) * np.exp(-t * 12.0)
        return tone * velocity * 0.28

    def _conga(self, velocity: float, low: bool) -> np.ndarray:
        length = int(0.14 * self.sample_rate)
        t = np.arange(length) / self.sample_rate
        freq = 190 if low else 260
        tone = np.sin(2 * np.pi * freq * t) * np.exp(-t * 14.0)
        attack = self.rng.standard_normal(length) * np.exp(-t * 32.0) * 0.08
        return (tone + attack) * velocity * 0.26

    def _sidechain_envelope(self, total_samples: int, kick_hits: list[float]) -> np.ndarray:
        envelope = np.ones(total_samples, dtype=np.float64)
        release_samples = int(0.26 * self.sample_rate)
        curve = 1.0 - 0.26 * np.exp(-np.linspace(0.0, 4.0, release_samples))

        for hit in kick_hits:
            start = int(hit * self.sample_rate)
            end = min(total_samples, start + release_samples)
            current_curve = curve[: end - start]
            envelope[start:end] = np.minimum(envelope[start:end], current_curve)

        return envelope

    def _master_bus(self, mix: np.ndarray, plan: TrackPlan) -> np.ndarray:
        duration = len(mix) / self.sample_rate
        time_axis = np.linspace(0.0, duration, len(mix), endpoint=False)
        wow = 1.0 + 0.008 * np.sin(2 * np.pi * 0.22 * time_axis) + 0.003 * np.sin(2 * np.pi * 1.7 * time_axis)
        mix = mix * wow[:, None]

        hiss_amount = {
            "dusty_warm": 0.0018,
            "silky_nocturne": 0.0012,
            "smoked_tape": 0.0030,
            "sunset_haze": 0.0014,
        }[plan.texture]
        mix += self.rng.standard_normal(mix.shape) * hiss_amount
        mix = self._simple_reverb(mix, 0.18 if plan.texture != "silky_nocturne" else 0.12)
        mix = self._stereo_filter(mix, "lowpass", 12_000)
        mix = self._stereo_filter(mix, "highpass", 28)
        mix = np.tanh(mix * (1.20 + plan.variety_amount * 0.04))

        fade_samples = int(self.sample_rate * 1.5)
        fade_in = np.linspace(0.0, 1.0, fade_samples)
        fade_out = np.linspace(1.0, 0.0, fade_samples)
        mix[:fade_samples] *= fade_in[:, None]
        mix[-fade_samples:] *= fade_out[:, None]
        return mix

    def _instrument_profile(self, instrument: pretty_midi.Instrument) -> dict[str, object]:
        name = instrument.name or ""
        if ":" in name:
            role, family = name.split(":", 1)
        else:
            role, family = "keys", "rhodes"

        profiles = {
            "keys": {"pan": -0.18, "widen": (160, 0.18)},
            "bass": {"pan": 0.0, "widen": (0, 0.0)},
            "lead": {"pan": 0.18, "widen": (40, 0.05)},
            "pad": {"pan": 0.05, "widen": (320, 0.26)},
            "counter": {"pan": -0.26, "widen": (120, 0.14)},
        }
        profile = profiles.get(role, {"pan": 0.0, "widen": (0, 0.0)})
        return {"role": role, "family": family, **profile}

    def _adsr(
        self,
        length: int,
        attack_seconds: float,
        decay_seconds: float,
        sustain_level: float,
        release_seconds: float,
    ) -> np.ndarray:
        env = np.ones(length, dtype=np.float64) * sustain_level
        attack = min(length, max(1, int(attack_seconds * self.sample_rate)))
        decay = min(max(0, length - attack), int(decay_seconds * self.sample_rate))
        release = min(length, max(1, int(release_seconds * self.sample_rate)))

        env[:attack] = np.linspace(0.0, 1.0, attack, endpoint=False)
        if decay > 0:
            env[attack : attack + decay] = np.linspace(1.0, sustain_level, decay, endpoint=False)
        env[-release:] *= np.linspace(1.0, 0.0, release)
        return env

    def _apply_filter(self, mono: np.ndarray, btype: str, cutoff: float | tuple[float, float]) -> np.ndarray:
        if len(mono) < 64:
            return mono
        if isinstance(cutoff, tuple):
            normalized = [value / (self.sample_rate / 2) for value in cutoff]
        else:
            normalized = cutoff / (self.sample_rate / 2)
        sos = signal.butter(3, normalized, btype=btype, output="sos")
        return signal.sosfiltfilt(sos, mono)

    def _stereo_filter(self, stereo: np.ndarray, btype: str, cutoff: float) -> np.ndarray:
        left = self._apply_filter(stereo[:, 0], btype, cutoff)
        right = self._apply_filter(stereo[:, 1], btype, cutoff)
        return np.column_stack((left, right))

    def _simple_delay(
        self,
        mono: np.ndarray,
        delay_seconds: float,
        repeats: int,
        feedback: float,
        mix: float,
    ) -> np.ndarray:
        delay_samples = int(delay_seconds * self.sample_rate)
        wet = np.zeros_like(mono)
        for repeat in range(1, repeats + 1):
            start = delay_samples * repeat
            if start >= len(mono):
                break
            wet[start:] += mono[:-start] * (feedback ** repeat)
        return mono * (1.0 - mix) + wet * mix

    def _simple_reverb(self, stereo: np.ndarray, mix: float) -> np.ndarray:
        wet = np.zeros_like(stereo)
        taps = [(0.031, 0.24), (0.047, 0.16), (0.071, 0.12), (0.109, 0.08)]
        for delay_seconds, gain in taps:
            delay = int(delay_seconds * self.sample_rate)
            if delay >= len(stereo):
                continue
            wet[delay:, 0] += stereo[:-delay, 1] * gain
            wet[delay:, 1] += stereo[:-delay, 0] * gain
        return stereo * (1.0 - mix) + wet * mix

    def _pan(self, mono: np.ndarray, pan: float) -> np.ndarray:
        left_gain = math.sqrt((1.0 - pan) / 2.0)
        right_gain = math.sqrt((1.0 + pan) / 2.0)
        return np.column_stack((mono * left_gain, mono * right_gain))

    def _widen(self, stereo: np.ndarray, delay_samples: int, blend: float) -> np.ndarray:
        if delay_samples <= 0 or delay_samples >= len(stereo):
            return stereo
        widened = stereo.copy()
        widened[delay_samples:, 0] += stereo[:-delay_samples, 1] * blend
        widened[delay_samples:, 1] += stereo[:-delay_samples, 0] * blend
        return widened
