#!/usr/bin/env python3
"""Validate browser deployment for all configured systems.

Static checks only; commercial ROM boot, graphics, sound and saves need real
browser/console testing after a successful build.
"""
from pathlib import Path
import json
import re
import subprocess

root = Path(__file__).resolve().parent.parent
runtime = root / "vendor" / "emulatorjs" / "data"
manifest = json.loads((root / "cores" / "retro-systems.json").read_text(encoding="utf-8"))["systems"]
variants = json.loads((runtime / "cores/webemu-variants.json").read_text(encoding="utf-8"))
main = (root / "index.html").read_text(encoding="utf-8")
azahar_player = (root / "cores/3ds-player.html").read_text(encoding="utf-8")
retro_player = (root / "cores/retro-player.html").read_text(encoding="utf-8")
adapter = (root / "cores/retro.js").read_text(encoding="utf-8")
sw = (root / "coi-serviceworker.js").read_text(encoding="utf-8")

required = [
    "loader.js", "emulator.min.js", "emulator.min.css",
    "compression/extractzip.js", "compression/extract7z.js",
    "compression/libunrar.js", "compression/libunrar.wasm",
    "cores/reports/azahar.json", "cores/azahar-thread-wasm.data",
]
for rel in required:
    path = runtime / rel
    if not path.is_file() or path.stat().st_size < 10:
        raise SystemExit(f"Missing browser emulator asset: {path}")
if (runtime / "cores/azahar-thread-wasm.data").stat().st_size < 1_000_000:
    raise SystemExit("Azahar WebAssembly data is too small")
if len(manifest) != 27:
    raise SystemExit(f"Expected 27 retro system variants, got {len(manifest)}")
unique_cores = {info["core"]: bool(info.get("threads")) for info in manifest.values()}
if len(unique_cores) < 20:
    raise SystemExit("Not all requested emulator cores are configured")
for name, threaded in unique_cores.items():
    choices = variants.get(name)
    if not choices or bool(choices.get("threads")) != threaded:
        raise SystemExit(f"Manifest missing {name} core or incorrect threading")
    report_path = runtime / f"cores/reports/{name}.json"
    if not report_path.is_file() or report_path.stat().st_size < 10:
        raise SystemExit(f"Missing offline metadata report for {name}")
    if not any(choices.get(style) for style in ("webgl2", "legacy")):
        raise SystemExit(f"No playable {name} variant")
    for style, suffix in (("webgl2", "-wasm.data"), ("legacy", "-legacy-wasm.data")):
        if choices.get(style):
            path = runtime / f"cores/{name}{'-thread' if threaded else ''}{suffix}"
            if not path.is_file() or path.stat().st_size < 100_000:
                raise SystemExit(f"Missing/truncated {name} {style} core: {path}")

if 'EJS_core = "3ds"' not in azahar_player or 'EJS_threads = true' not in azahar_player:
    raise SystemExit("Azahar needs selected 3DS threaded core")
if "crossOriginIsolated" not in (root / "cores/3ds.js").read_text(encoding="utf-8"):
    raise SystemExit("3DS adapter missing cross-origin isolation precheck")
if "coi-serviceworker.js" not in main or not sw:
    raise SystemExit("GitHub Pages isolation service worker missing")
if 'id="tabClassic"' not in main or 'id="classicSystem"' not in main:
    raise SystemExit("Missing retro console browser UI")
for system in manifest:
    if f'value="{system}"' not in main:
        raise SystemExit(f"Console {system} absent from selector")

sources = {
    "index": re.search(r'<script type="module">([\\s\\S]*?)</script>', main),
    "Azahar player": re.search(r'<script>([\\s\\S]*?)</script>', azahar_player),
    "retro player": re.search(r'<script>([\\s\\S]*?)</script>', retro_player),
}
for label, match in sources.items():
    if not match:
        raise SystemExit(f"Cannot find embedded JavaScript in {label}")
    proc = subprocess.run(["node", "--input-type=module", "--check"],
                          input=match.group(1), text=True, capture_output=True)
    if proc.returncode:
        raise SystemExit(f"{label} JavaScript syntax error:\\n{proc.stderr}")
    print(f"PASS: {label} syntax")
for rel in ("cores/3ds.js", "cores/retro.js", "coi-serviceworker.js"):
    proc = subprocess.run(["node", "--input-type=module", "--check"],
                          input=(root / rel).read_text(encoding="utf-8"),
                          text=True, capture_output=True)
    if proc.returncode:
        raise SystemExit(f"{rel} JavaScript syntax error:\\n{proc.stderr}")
    print(f"PASS: {rel} syntax")
if '"./retro-systems.json"' not in adapter or 'window.EJS_threads = Boolean(config.threads)' not in retro_player:
    raise SystemExit("Browser emulator adapter does not use shared core manifest or thread configuration")
print(f"PASS: {len(manifest)} retro consoles, {len(unique_cores)} real libretro core families, Azahar threaded 3DS and local frontend runtime.")
print("NOTE: Static validation does not prove game boot, frame rate, sound or save persistence.")
