from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class SectionPlan:
    name: str
    bars: int
    intensity: float
    layers: list[str] = field(default_factory=list)
    variation: str = "steady"
    lead_density: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TrackPlan:
    title: str
    description: str
    bpm: int
    key: str
    mode: str
    mood: str
    texture: str
    swing: float
    humanization: float
    arrangement_style: str
    progression_family: str
    drum_style: str
    bass_style: str
    piano_style: str
    lead_style: str
    keys_sound: str = "rhodes"
    bass_sound: str = "electric_bass"
    lead_sound: str = "vibes"
    pad_sound: str = "warm_pad"
    counter_sound: str = "none"
    percussion_style: str = "none"
    riff_shape: str = "arched"
    motif_variation: str = "sequence"
    riff_density: float = 0.5
    variety_amount: float = 0.5
    substitution_rate: float = 0.2
    immersion_mode: str = "atmosphere"
    ambience_layers: list[str] = field(default_factory=list)
    sections: list[SectionPlan] = field(default_factory=list)
    seed: int = 0
    planner_source: str = "fallback"
    planner_notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
