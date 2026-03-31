"""Fusion AI music generator package."""

from .ambience import AmbienceRenderer
from .composer import FusionComposer
from .planner import LLMPlanner, OllamaPlanner
from .providers import OllamaPlanProvider, PlanProvider, create_provider
from .render import AudioRenderer
from .service import GenerationRequest, GenerationResult, generate_track, list_library, probe_ollama

__all__ = [
    "AmbienceRenderer",
    "AudioRenderer",
    "FusionComposer",
    "GenerationRequest",
    "GenerationResult",
    "LLMPlanner",
    "OllamaPlanProvider",
    "OllamaPlanner",
    "PlanProvider",
    "create_provider",
    "generate_track",
    "list_library",
    "probe_ollama",
]
