from __future__ import annotations

import math

import numpy as np
from scipy import signal


class AmbienceRenderer:
    def __init__(self, sample_rate: int = 44_100, seed: int = 0) -> None:
        self.sample_rate = sample_rate
        self.rng = np.random.default_rng(seed + 101)

    def render(self, duration_seconds: float, layers: list[str]) -> np.ndarray:
        total_samples = int(duration_seconds * self.sample_rate)
        stereo = np.zeros((total_samples, 2), dtype=np.float64)

        for layer in layers:
            mono = self._render_layer(layer, total_samples)
            pan = {
                "vinyl": 0.0,
                "rain": 0.08,
                "wind": -0.12,
                "city": 0.04,
                "fire": -0.06,
                "waves": 0.12,
                "night": 0.18,
                "train": -0.03,
            }.get(layer, 0.0)
            stereo += self._pan(mono, pan)

        return np.tanh(stereo)

    def _render_layer(self, layer: str, total_samples: int) -> np.ndarray:
        if layer == "vinyl":
            return self._vinyl(total_samples)
        if layer == "rain":
            return self._rain(total_samples)
        if layer == "wind":
            return self._wind(total_samples)
        if layer == "city":
            return self._city(total_samples)
        if layer == "fire":
            return self._fire(total_samples)
        if layer == "waves":
            return self._waves(total_samples)
        if layer == "night":
            return self._night(total_samples)
        if layer == "train":
            return self._train(total_samples)
        return np.zeros(total_samples, dtype=np.float64)

    def _vinyl(self, total_samples: int) -> np.ndarray:
        bed = self._filtered_noise(total_samples, "highpass", 2_200) * 0.0025
        pops = np.zeros(total_samples, dtype=np.float64)
        pop_count = max(12, total_samples // (self.sample_rate * 2))
        for _ in range(pop_count):
            start = self.rng.integers(0, max(1, total_samples - 800))
            length = int(self.rng.integers(80, 800))
            burst = self.rng.standard_normal(length) * np.exp(-np.linspace(0.0, 8.0, length))
            pops[start : start + length] += burst * self.rng.uniform(0.003, 0.01)
        return bed + pops

    def _rain(self, total_samples: int) -> np.ndarray:
        noise = self._filtered_noise(total_samples, "bandpass", (1_200, 7_500)) * 0.010
        envelope = self._slow_envelope(total_samples, cycles=0.35, floor=0.65, depth=0.35)
        return noise * envelope

    def _wind(self, total_samples: int) -> np.ndarray:
        noise = self._filtered_noise(total_samples, "bandpass", (180, 1_600)) * 0.012
        envelope = self._slow_envelope(total_samples, cycles=0.12, floor=0.35, depth=0.65)
        return self._filter(noise * envelope, "lowpass", 1_600)

    def _city(self, total_samples: int) -> np.ndarray:
        t = np.arange(total_samples) / self.sample_rate
        rumble = (np.sin(2 * np.pi * 42 * t) + 0.4 * np.sin(2 * np.pi * 83 * t)) * 0.004
        noise = self._filtered_noise(total_samples, "bandpass", (120, 3_200)) * 0.004
        horns = np.zeros(total_samples, dtype=np.float64)
        for _ in range(max(2, total_samples // (self.sample_rate * 18))):
            start = self.rng.integers(0, max(1, total_samples - self.sample_rate))
            length = int(self.sample_rate * self.rng.uniform(0.2, 0.7))
            freq = self.rng.choice([311, 370, 415, 466])
            tone = np.sin(2 * np.pi * freq * np.arange(length) / self.sample_rate)
            envelope = np.exp(-np.linspace(0.0, 5.0, length))
            horns[start : start + length] += tone * envelope * self.rng.uniform(0.001, 0.0035)
        return rumble + noise + horns

    def _fire(self, total_samples: int) -> np.ndarray:
        crackle = np.zeros(total_samples, dtype=np.float64)
        hit_count = max(60, total_samples // (self.sample_rate // 2))
        for _ in range(hit_count):
            start = self.rng.integers(0, max(1, total_samples - 2000))
            length = int(self.rng.integers(60, 600))
            burst = self._filtered_noise(length, "bandpass", (700, 4_000))
            crackle[start : start + length] += burst * np.exp(-np.linspace(0.0, 9.0, length)) * self.rng.uniform(0.002, 0.008)
        bed = self._filtered_noise(total_samples, "bandpass", (120, 1_600)) * 0.003
        return crackle + bed

    def _waves(self, total_samples: int) -> np.ndarray:
        noise = self._filtered_noise(total_samples, "bandpass", (100, 1_800)) * 0.010
        envelope = (np.sin(np.linspace(0.0, 6.0 * math.pi, total_samples)) + 1.0) * 0.35 + 0.2
        return self._filter(noise * envelope, "lowpass", 1_400)

    def _night(self, total_samples: int) -> np.ndarray:
        ambience = self._filtered_noise(total_samples, "bandpass", (3_000, 9_000)) * 0.0012
        chirps = np.zeros(total_samples, dtype=np.float64)
        count = max(8, total_samples // (self.sample_rate * 7))
        for _ in range(count):
            start = self.rng.integers(0, max(1, total_samples - self.sample_rate // 2))
            length = int(self.sample_rate * self.rng.uniform(0.06, 0.18))
            freq = self.rng.choice([2800, 3400, 4200, 5100])
            t = np.arange(length) / self.sample_rate
            tone = np.sin(2 * np.pi * freq * t) * np.exp(-np.linspace(0.0, 12.0, length))
            chirps[start : start + length] += tone * self.rng.uniform(0.001, 0.004)
        return ambience + chirps

    def _train(self, total_samples: int) -> np.ndarray:
        t = np.arange(total_samples) / self.sample_rate
        rumble = (np.sin(2 * np.pi * 48 * t) + 0.5 * np.sin(2 * np.pi * 96 * t)) * 0.005
        clacks = np.zeros(total_samples, dtype=np.float64)
        interval = int(self.sample_rate * 0.72)
        for start in range(0, total_samples - 4_000, interval):
            length = 3_000
            hit = self._filtered_noise(length, "bandpass", (900, 4_500))
            clacks[start : start + length] += hit * np.exp(-np.linspace(0.0, 10.0, length)) * 0.004
        return rumble + clacks

    def _slow_envelope(self, total_samples: int, cycles: float, floor: float, depth: float) -> np.ndarray:
        axis = np.linspace(0.0, 2 * math.pi * cycles, total_samples)
        return floor + ((np.sin(axis) + 1.0) * 0.5) * depth

    def _filtered_noise(
        self,
        total_samples: int,
        btype: str,
        cutoff: float | tuple[float, float],
    ) -> np.ndarray:
        noise = self.rng.standard_normal(total_samples)
        return self._filter(noise, btype, cutoff)

    def _filter(self, mono: np.ndarray, btype: str, cutoff: float | tuple[float, float]) -> np.ndarray:
        if len(mono) < 64:
            return mono
        if isinstance(cutoff, tuple):
            normalized = [value / (self.sample_rate / 2) for value in cutoff]
        else:
            normalized = cutoff / (self.sample_rate / 2)
        sos = signal.butter(3, normalized, btype=btype, output="sos")
        return signal.sosfiltfilt(sos, mono)

    def _pan(self, mono: np.ndarray, pan: float) -> np.ndarray:
        left_gain = math.sqrt((1.0 - pan) / 2.0)
        right_gain = math.sqrt((1.0 + pan) / 2.0)
        return np.column_stack((mono * left_gain, mono * right_gain))
