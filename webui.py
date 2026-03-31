from __future__ import annotations

import argparse
import threading
import webbrowser
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from fusion_music import GenerationRequest, generate_track, list_library, probe_ollama
from fusion_music.defaults import AMBIENCE_LAYERS, IMMERSION_MODES


class GeneratePayload(BaseModel):
    prompt: str = ""
    provider: str = "ollama"
    model: str = "phi4-mini"
    llm_host: str = "http://127.0.0.1:11434"
    llm_temperature: float = Field(default=0.95, ge=0.0, le=2.0)
    seed: int | None = None
    sample_rate: int = Field(default=44_100, ge=8_000, le=96_000)
    immersion: str | None = None
    ambience: list[str] | None = None
    export_stems: bool = False


def create_app(
    project_root: Path | None = None,
    output_dir: str = "output",
    default_model: str = "phi4-mini",
    default_llm_host: str = "http://127.0.0.1:11434",
) -> FastAPI:
    root = (project_root or Path(__file__).resolve().parent).resolve()
    static_dir = root / "webui_static"
    generated_dir = (root / output_dir).resolve()
    generated_dir.mkdir(parents=True, exist_ok=True)

    app = FastAPI(title="Fusion Music Generator UI")
    app.state.project_root = root
    app.state.output_dir = output_dir
    app.state.generated_dir = generated_dir
    app.state.default_model = default_model
    app.state.default_llm_host = default_llm_host

    app.mount("/assets", StaticFiles(directory=static_dir), name="assets")
    app.mount("/generated", StaticFiles(directory=generated_dir), name="generated")

    @app.get("/")
    async def index() -> FileResponse:
        return FileResponse(static_dir / "index.html")

    @app.get("/api/config")
    async def config() -> dict[str, Any]:
        return {
            "providers": ["ollama", "fallback"],
            "immersion_modes": list(IMMERSION_MODES),
            "ambience_layers": list(AMBIENCE_LAYERS),
            "defaults": {
                "provider": "ollama",
                "model": app.state.default_model,
                "llm_host": app.state.default_llm_host,
                "sample_rate": 44_100,
            },
        }

    @app.get("/api/status")
    async def status(host: str | None = None) -> dict[str, Any]:
        target_host = host or app.state.default_llm_host
        ollama = await run_in_threadpool(probe_ollama, target_host)
        library = await run_in_threadpool(list_library, app.state.project_root, app.state.output_dir, 6)
        return {
            "ollama": ollama,
            "library_count": len(library),
            "output_dir": str(app.state.generated_dir),
        }

    @app.get("/api/library")
    async def library(limit: int = 18) -> dict[str, Any]:
        items = await run_in_threadpool(list_library, app.state.project_root, app.state.output_dir, limit)
        return {"items": [_serialize_library_item(item, app.state.generated_dir) for item in items]}

    @app.post("/api/generate")
    async def generate(payload: GeneratePayload) -> dict[str, Any]:
        result = await run_in_threadpool(
            generate_track,
            GenerationRequest(
                prompt=payload.prompt,
                provider=payload.provider,
                model=payload.model,
                llm_host=payload.llm_host,
                llm_temperature=payload.llm_temperature,
                seed=payload.seed,
                output_dir=app.state.output_dir,
                sample_rate=payload.sample_rate,
                immersion=payload.immersion,
                ambience=payload.ambience,
                export_stems=payload.export_stems,
            ),
            app.state.project_root,
        )
        return {
            "result": _serialize_generation_result(result.to_dict(), app.state.generated_dir),
            "library": [
                _serialize_library_item(item, app.state.generated_dir)
                for item in list_library(app.state.project_root, app.state.output_dir, 12)
            ],
        }

    return app


def _serialize_generation_result(result: dict[str, Any], generated_dir: Path) -> dict[str, Any]:
    serialized = dict(result)
    serialized["wav_url"] = _to_generated_url(result["wav_path"], generated_dir)
    serialized["midi_url"] = _to_generated_url(result["midi_path"], generated_dir)
    serialized["info_url"] = _to_generated_url(result["info_path"], generated_dir)
    serialized["stem_urls"] = [_to_generated_url(path, generated_dir) for path in result.get("stem_paths", [])]
    return serialized


def _serialize_library_item(item: dict[str, Any], generated_dir: Path) -> dict[str, Any]:
    serialized = dict(item)
    serialized["wav_url"] = _to_generated_url(item.get("wav_path"), generated_dir)
    serialized["midi_url"] = _to_generated_url(item.get("midi_path"), generated_dir)
    serialized["info_url"] = _to_generated_url(item.get("info_path"), generated_dir)
    serialized["stem_urls"] = [_to_generated_url(path, generated_dir) for path in item.get("stems", [])]
    return serialized


def _to_generated_url(path_text: str | None, generated_dir: Path) -> str | None:
    if not path_text:
        return None
    path = Path(path_text).resolve()
    try:
        relative = path.relative_to(generated_dir)
    except ValueError:
        return None
    return "/generated/" + relative.as_posix()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Launch the Fusion Music Generator web UI")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind the UI server")
    parser.add_argument("--port", type=int, default=7860, help="Port to bind the UI server")
    parser.add_argument("--output-dir", default="output", help="Directory used for generated tracks")
    parser.add_argument("--model", default="phi4-mini", help="Default model shown in the UI")
    parser.add_argument("--llm-host", default="http://127.0.0.1:11434", help="Default Ollama host shown in the UI")
    parser.add_argument("--no-browser", action="store_true", help="Do not open the browser automatically")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    app = create_app(
        output_dir=args.output_dir,
        default_model=args.model,
        default_llm_host=args.llm_host,
    )

    if not args.no_browser:
        url = f"http://{args.host}:{args.port}"
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()

    uvicorn.run(app, host=args.host, port=args.port)


app = create_app()


if __name__ == "__main__":
    main()
