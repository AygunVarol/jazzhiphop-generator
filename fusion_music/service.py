from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import soundfile as sf

from .composer import FusionComposer
from .planner import LLMPlanner
from .providers import create_provider
from .render import AudioRenderer


@dataclass
class GenerationRequest:
    prompt: str = ""
    provider: str = "ollama"
    model: str = "phi4-mini"
    llm_host: str = "http://127.0.0.1:11434"
    llm_temperature: float = 0.95
    seed: int | None = None
    output_dir: str = "output"
    sample_rate: int = 44_100
    immersion: str | None = None
    ambience: list[str] | None = None
    export_stems: bool = False


@dataclass
class GenerationResult:
    basename: str
    output_dir: str
    midi_path: str
    wav_path: str
    info_path: str
    stem_paths: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "untitled"


def generate_track(request: GenerationRequest, project_root: Path | None = None) -> GenerationResult:
    root = (project_root or Path(__file__).resolve().parent.parent).resolve()
    output_dir = (root / request.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    provider_name = request.provider
    provider = None if provider_name == "fallback" else create_provider(
        provider_name,
        model=request.model,
        host=request.llm_host,
        temperature=request.llm_temperature,
    )
    planner = LLMPlanner(provider=provider)
    plan = planner.build_plan(
        prompt_hint=request.prompt,
        seed=request.seed,
        use_provider=provider is not None,
        immersion_override=request.immersion,
        ambience_override=request.ambience,
    )

    composer = FusionComposer(plan)
    midi, composition_info = composer.compose()

    renderer = AudioRenderer(sample_rate=request.sample_rate, seed=plan.seed)
    mix, stems = renderer.render(midi, plan)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    basename = f"fusion_{slugify(plan.title)}_{plan.key}_{plan.bpm}bpm_{timestamp}"
    midi_path = output_dir / f"{basename}.mid"
    wav_path = output_dir / f"{basename}.wav"
    info_path = output_dir / f"{basename}_info.json"

    midi.write(str(midi_path))
    sf.write(str(wav_path), mix, request.sample_rate)

    stem_paths: list[str] = []
    if request.export_stems:
        stem_paths = save_stems(stems, output_dir, basename, request.sample_rate)

    metadata = {
        "generated_at": timestamp,
        "prompt_hint": request.prompt,
        "provider": provider_name,
        "model": request.model,
        "seed": plan.seed,
        "plan": plan.to_dict(),
        "composition": composition_info,
        "render": {
            "sample_rate": request.sample_rate,
            "duration_seconds": round(len(mix) / request.sample_rate, 3),
            "stems": sorted(stems),
            "exported_stems": stem_paths,
        },
        "files": {
            "midi": str(midi_path),
            "wav": str(wav_path),
        },
    }
    info_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    return GenerationResult(
        basename=basename,
        output_dir=str(output_dir),
        midi_path=str(midi_path),
        wav_path=str(wav_path),
        info_path=str(info_path),
        stem_paths=stem_paths,
        metadata=metadata,
    )


def save_stems(stems: dict[str, object], output_dir: Path, basename: str, sample_rate: int) -> list[str]:
    stems_dir = output_dir / f"{basename}_stems"
    stems_dir.mkdir(parents=True, exist_ok=True)
    written = []

    for stem_name, audio in stems.items():
        safe_name = slugify(stem_name)
        stem_path = stems_dir / f"{basename}_{safe_name}.wav"
        sf.write(str(stem_path), audio, sample_rate)
        written.append(str(stem_path))

    return written


def list_library(project_root: Path | None = None, output_dir: str = "output", limit: int = 24) -> list[dict[str, Any]]:
    root = (project_root or Path(__file__).resolve().parent.parent).resolve()
    directory = (root / output_dir).resolve()
    if not directory.exists():
        return []

    items: list[dict[str, Any]] = []
    info_files = sorted(directory.glob("*_info.json"), key=lambda path: path.stat().st_mtime, reverse=True)
    for info_path in info_files[: max(1, limit)]:
        try:
            metadata = json.loads(info_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue

        plan = metadata.get("plan", {})
        files = metadata.get("files", {})
        render = metadata.get("render", {})
        items.append(
            {
                "basename": info_path.stem[:-5] if info_path.stem.endswith("_info") else info_path.stem,
                "generated_at": metadata.get("generated_at"),
                "title": plan.get("title"),
                "description": plan.get("description"),
                "mood": plan.get("mood"),
                "key": plan.get("key"),
                "mode": plan.get("mode"),
                "bpm": plan.get("bpm"),
                "provider": metadata.get("provider"),
                "immersion": plan.get("immersion_mode"),
                "ambience": plan.get("ambience_layers", []),
                "palette": [
                    value
                    for value in (
                        plan.get("keys_sound"),
                        plan.get("bass_sound"),
                        plan.get("lead_sound"),
                    )
                    if value
                ],
                "wav_path": files.get("wav"),
                "midi_path": files.get("midi"),
                "info_path": str(info_path),
                "stems": render.get("exported_stems", []),
            }
        )

    return items


def probe_ollama(host: str = "http://127.0.0.1:11434") -> dict[str, Any]:
    url = host.rstrip("/") + "/api/tags"
    request = urllib.request.Request(url, method="GET")

    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return {
            "reachable": False,
            "host": host,
            "models": [],
            "error": str(exc),
        }

    models = [model.get("name") for model in payload.get("models", []) if isinstance(model, dict) and model.get("name")]
    return {
        "reachable": True,
        "host": host,
        "models": models,
        "error": "",
    }
