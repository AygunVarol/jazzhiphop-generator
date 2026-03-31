# Fusion AI Music Generator

Merged from your `jazzhiphop-generator-main` and `lofi-generator` repos, then upgraded using transferable engine ideas from `lofi-engine-master`.

This version keeps your local LLM composer, but it is no longer hard-wired to Ollama internals. The planner is now provider-based so you can swap the backend later without rewriting the music engine.

## What Improved

- Swappable LLM planner backend instead of an Ollama-only planner class
- Better harmony movement inspired by `lofi-engine` chord transitions
- Immersion modes inspired by `lofi-engine`:
  - `music`
  - `atmosphere`
  - `world`
  - `manual`
- Procedural ambience layers:
  - `vinyl`
  - `rain`
  - `wind`
  - `city`
  - `fire`
  - `waves`
  - `night`
  - `train`
- Stem export for post-processing in a DAW
- Cleaner CLI for model, host, temperature, ambience, and backend selection
- Small local web UI for generation, playback, and browsing recent renders
- More musical variety:
  - LLM-planned instrument palette per song
  - Riff shape and motif mutation controls
  - Counter-melody and percussion layers
  - More pattern mutation in keys, bass, drums, and lead writing

## Requirements

- Python 3.11+
- Ollama installed locally if you want live LLM planning
- `phi4-mini` pulled locally

## Install

```powershell
cd fusion-music-generator
python -m pip install -r requirements.txt
```

## Usage

Default local LLM generation:

```powershell
python app.py
```

Prompted generation:

```powershell
python app.py --prompt "rainy Tokyo backstreet, smoky Rhodes, heavy pocket"
```

Fallback planner only:

```powershell
python app.py --provider fallback
```

Manual ambience world:

```powershell
python app.py --immersion manual --ambience vinyl rain city train
```

Export stems:

```powershell
python app.py --export-stems
```

Use a different Ollama endpoint or model later:

```powershell
python app.py --provider ollama --model phi4-mini --llm-host http://127.0.0.1:11434
```

## Web UI

Launch the local web UI:

```powershell
python webui.py
```

This starts a small FastAPI app and opens your browser to a local control room where you can:

- prompt the generator
- switch provider/model/host
- set immersion and ambience
- export stems
- preview generated WAVs
- browse recent tracks from `output/`

Useful options:

```powershell
python webui.py --host 127.0.0.1 --port 7860 --model phi4-mini
python webui.py --no-browser
```

## CLI Highlights

- `--provider ollama|fallback`
- `--model <name>`
- `--llm-host <url>`
- `--llm-temperature <float>`
- `--immersion music|atmosphere|world|manual`
- `--ambience <layers...>`
- `--export-stems`
- `--seed <int>`

## Output

Generated files go to `output/`:

- `fusion_[title]_[key]_[bpm]_[timestamp].mid`
- `fusion_[title]_[key]_[bpm]_[timestamp].wav`
- `fusion_[title]_[key]_[bpm]_[timestamp]_info.json`
- Optional stem folder when `--export-stems` is enabled

## Architecture

- `fusion_music/providers.py`
  - LLM backend abstraction
  - Currently ships with an Ollama provider
- `fusion_music/service.py`
  - Shared generation flow used by both the CLI and the web UI
- `fusion_music/planner.py`
  - Builds a structured plan from the active provider or fallback rules
  - Chooses immersion mode and ambience layers
- `fusion_music/harmony.py`
  - Transition-aware chord routing inspired by `lofi-engine`
- `fusion_music/composer.py`
  - Writes piano, bass, drums, lead, and pad parts from the plan
- `fusion_music/ambience.py`
  - Generates procedural background world layers
- `fusion_music/render.py`
  - Renders music plus ambience into stereo WAV and stems
- `webui.py`
  - Local FastAPI server for the browser UI
- `webui_static/`
  - Single-page UI assets with no Node build step

## Notes

- The original repos remain untouched.
- The current swappable provider layer only implements Ollama, but the planner is no longer coupled to it.
- If you want, the next logical upgrade is a real sample-based renderer or a small desktop/web UI around this Python engine.
