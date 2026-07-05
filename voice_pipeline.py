from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional

try:
    from diffsinger_utau.voice_bank import PredAll
    from diffsinger_utau.voice_bank.commons.ds_reader import DSReader
except Exception:  # pragma: no cover - runtime dependency may be absent
    PredAll = None
    DSReader = None

ROOT = Path(__file__).resolve().parent
DEFAULT_TEMPLATE = ROOT / "sample.ds"


def build_ds_from_text(text: str, template_path: Optional[Path] = None):
    if DSReader is None:
        raise RuntimeError("diffsinger-utau is not installed. Please install the project requirements first.")

    template = template_path or DEFAULT_TEMPLATE
    ds_items = DSReader(str(template)).read_ds()
    if not ds_items:
        raise ValueError(f"No DS entries found in template: {template}")

    ds = ds_items[0]
    ds["text"] = text
    ds.replace(text)
    return ds


def generate_vocal(
    voice_bank_path: str | Path,
    text: str,
    output_dir: str | Path = "output/pred_all",
    speaker: Optional[str] = None,
    template_path: Optional[str | Path] = None,
    lang: str = "zh",
    key_shift: int = 0,
    pitch_steps: int = 10,
    variance_steps: int = 10,
    acoustic_steps: int = 50,
    gender: float = 0.0,
    save_intermediate: bool = True,
):
    if PredAll is None:
        raise RuntimeError("DiffSinger backend is unavailable because diffsinger-utau is not installed.")

    voice_bank = Path(voice_bank_path).expanduser().resolve()
    if not voice_bank.exists():
        raise FileNotFoundError(f"Voice bank not found: {voice_bank}")

    predictor = PredAll(voice_bank)
    resolved_speaker = speaker or (predictor.available_speakers[0] if predictor.available_speakers else None)
    if not resolved_speaker:
        raise ValueError("No speaker was provided and no speaker was found in the voice bank.")

    ds = build_ds_from_text(text, Path(template_path).expanduser().resolve() if template_path else None)

    results = predictor.predict_full_pipeline(
        ds=ds,
        lang=lang,
        speaker=resolved_speaker,
        key_shift=key_shift,
        pitch_steps=pitch_steps,
        variance_steps=variance_steps,
        acoustic_steps=acoustic_steps,
        gender=gender,
        output_dir=str(output_dir),
        save_intermediate=save_intermediate,
    )
    return results


def main():
    parser = argparse.ArgumentParser(description="Generate a DiffSinger vocal from text for integration into a music app")
    parser.add_argument("--voice-bank", required=True, help="Path to a DiffSinger-compatible voice bank directory")
    parser.add_argument("--text", required=True, help="Lyrics or prompt text to synthesize")
    parser.add_argument("--speaker", default=None, help="Speaker name to use from the voice bank")
    parser.add_argument("--template", default=str(DEFAULT_TEMPLATE), help="Path to a .ds template file")
    parser.add_argument("--output-dir", default="output/pred_all", help="Directory for generated audio")
    parser.add_argument("--lang", default="zh", help="Language code, for example zh")
    parser.add_argument("--key-shift", type=int, default=0)
    parser.add_argument("--pitch-steps", type=int, default=10)
    parser.add_argument("--variance-steps", type=int, default=10)
    parser.add_argument("--acoustic-steps", type=int, default=50)
    parser.add_argument("--gender", type=float, default=0.0)
    args = parser.parse_args()

    results = generate_vocal(
        voice_bank_path=args.voice_bank,
        text=args.text,
        output_dir=args.output_dir,
        speaker=args.speaker,
        template_path=args.template,
        lang=args.lang,
        key_shift=args.key_shift,
        pitch_steps=args.pitch_steps,
        variance_steps=args.variance_steps,
        acoustic_steps=args.acoustic_steps,
        gender=args.gender,
    )
    print(results.get("audio_path") or results)


if __name__ == "__main__":
    main()
