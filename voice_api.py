from __future__ import annotations

import argparse
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, Dict
from urllib.parse import unquote, urlparse

from voice_pipeline import generate_vocal

ROOT = Path(__file__).resolve().parent


class VoiceRequestHandler(BaseHTTPRequestHandler):
    def _send_json(self, payload: Dict[str, Any], status: int = 200) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, file_path: Path, content_type: str) -> None:
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(file_path.stat().st_size))
        self.end_headers()
        with file_path.open("rb") as fh:
            self.wfile.write(fh.read())

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            self._send_json({"status": "ok", "service": "diffsinger-voice-api"})
            return
        if parsed.path == "/audio":
            raw_path = parsed.query.split("=", 1)[1] if "=" in parsed.query else ""
            audio_path = Path(unquote(raw_path)).resolve()
            if not audio_path.exists() or not audio_path.is_file():
                self._send_json({"error": "audio not found"}, status=404)
                return
            try:
                audio_path.relative_to(ROOT.resolve())
            except ValueError:
                self._send_json({"error": "forbidden path"}, status=403)
                return
            content_type = "audio/wav"
            if audio_path.suffix.lower() == ".mp3":
                content_type = "audio/mpeg"
            elif audio_path.suffix.lower() == ".ogg":
                content_type = "audio/ogg"
            self._send_file(audio_path, content_type)
            return
        self._send_json({"error": "not found"}, status=404)

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path != "/generate":
            self._send_json({"error": "not found"}, status=404)
            return

        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length).decode("utf-8") or "{}"
        try:
            payload = json.loads(body)
        except json.JSONDecodeError as exc:
            self._send_json({"error": f"invalid json: {exc}"}, status=400)
            return

        try:
            voice_bank = payload.get("voice_bank")
            text = payload.get("text")
            if not voice_bank or not text:
                raise ValueError("voice_bank and text are required")

            output_dir = payload.get("output_dir", str(ROOT / "output" / "pred_all"))
            template = payload.get("template")
            speaker = payload.get("speaker")
            lang = payload.get("lang", "zh")
            key_shift = int(payload.get("key_shift", 0))
            pitch_steps = int(payload.get("pitch_steps", 10))
            variance_steps = int(payload.get("variance_steps", 10))
            acoustic_steps = int(payload.get("acoustic_steps", 50))
            gender = float(payload.get("gender", 0.0))

            results = generate_vocal(
                voice_bank_path=voice_bank,
                text=text,
                output_dir=output_dir,
                speaker=speaker,
                template_path=template,
                lang=lang,
                key_shift=key_shift,
                pitch_steps=pitch_steps,
                variance_steps=variance_steps,
                acoustic_steps=acoustic_steps,
                gender=gender,
            )
            audio_path = results.get("audio_path")
            audio_url = None
            if audio_path:
                audio_file = Path(audio_path).resolve()
                rel = audio_file.relative_to(ROOT.resolve()) if str(audio_file).startswith(str(ROOT.resolve())) else None
                if rel is not None:
                    audio_url = f"http://127.0.0.1:{self.server.server_address[1]}/audio?path={audio_file.as_posix()}"
            self._send_json({"status": "ok", "results": results, "audio_url": audio_url})
        except Exception as exc:  # pragma: no cover - network-facing error path
            self._send_json({"error": str(exc)}, status=500)


def main() -> None:
    parser = argparse.ArgumentParser(description="Minimal HTTP API for DiffSinger voice generation")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    server = HTTPServer((args.host, args.port), VoiceRequestHandler)
    print(f"Serving on http://{args.host}:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
