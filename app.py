from __future__ import annotations

import argparse

from fusion_music import GenerationRequest, generate_track


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fusion AI jazz-lofi music generator")
    parser.add_argument("--prompt", default="", help="Optional vibe prompt for the LLM planner")
    parser.add_argument("--provider", default="ollama", choices=("ollama", "fallback"), help="Planner backend")
    parser.add_argument("--model", default="phi4-mini", help="LLM model name for provider backends that use models")
    parser.add_argument("--llm-host", default="http://127.0.0.1:11434", help="Provider endpoint, used by the Ollama backend")
    parser.add_argument("--llm-temperature", type=float, default=0.95, help="Sampling temperature for the LLM planner")
    parser.add_argument("--seed", type=int, default=None, help="Seed for reproducible planning and composition")
    parser.add_argument("--output-dir", default="output", help="Directory for generated files")
    parser.add_argument("--sample-rate", type=int, default=44_100, help="Audio sample rate")
    parser.add_argument("--immersion", choices=("music", "atmosphere", "world", "manual"), default=None, help="Override the mix world mode")
    parser.add_argument("--ambience", nargs="*", default=None, help="Manual ambience layers, for example: rain city vinyl")
    parser.add_argument("--export-stems", action="store_true", help="Write each rendered stem as a separate WAV file")
    parser.add_argument("--no-ollama", action="store_true", help="Backwards-compatible alias for --provider fallback")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    provider_name = "fallback" if args.no_ollama else args.provider
    result = generate_track(
        GenerationRequest(
            prompt=args.prompt,
            provider=provider_name,
            model=args.model,
            llm_host=args.llm_host,
            llm_temperature=args.llm_temperature,
            seed=args.seed,
            output_dir=args.output_dir,
            sample_rate=args.sample_rate,
            immersion=args.immersion,
            ambience=args.ambience,
            export_stems=args.export_stems,
        )
    )
    plan = result.metadata["plan"]

    print("=" * 68)
    print("Fusion AI Music Generator")
    print("=" * 68)
    print(f"Planner source : {plan['planner_source']}")
    print(f"Title          : {plan['title']}")
    print(f"Feel           : {plan['mood']}")
    print(f"Key / Mode     : {plan['key']} {plan['mode']}")
    print(f"BPM            : {plan['bpm']}")
    print(f"Progression    : {plan['progression_family']}")
    print(f"Drums / Bass   : {plan['drum_style']} / {plan['bass_style']}")
    print(f"Immersion      : {plan['immersion_mode']}")
    print(f"Ambience       : {', '.join(plan['ambience_layers']) if plan['ambience_layers'] else 'none'}")
    if plan.get("planner_notes"):
        print(f"Planner notes  : {plan['planner_notes']}")
    print("-" * 68)
    print(plan["description"])
    print("-" * 68)
    print(f"MIDI saved     : {result.midi_path}")
    print(f"WAV saved      : {result.wav_path}")
    if result.stem_paths:
        print(f"Stems saved    : {len(result.stem_paths)} files")
    print(f"Metadata saved : {result.info_path}")
    print("=" * 68)


if __name__ == "__main__":
    main()
