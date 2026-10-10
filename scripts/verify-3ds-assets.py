#!/usr/bin/env python3
"""Static deployment smoke test; this does NOT verify real 3DS game boot."""
from pathlib import Path
import re
import subprocess

main = Path("index.html").read_text(encoding="utf-8")
player = Path("cores/3ds-player.html").read_text(encoding="utf-8")
adapter = Path("cores/3ds.js")
sw = Path("coi-serviceworker.js")
core = Path("vendor/emulatorjs/data/cores/azahar-thread-wasm.data")
runtime = Path("vendor/emulatorjs/data")
required = [
    "loader.js", "emulator.min.js", "emulator.min.css",
    "compression/extractzip.js", "compression/extract7z.js",
    "compression/libunrar.js", "compression/libunrar.wasm",
]
for filename in required:
    path = runtime / filename
    if not path.is_file() or path.stat().st_size < 10:
        raise SystemExit(f"Missing Azahar runtime asset: {path}")
if not core.is_file() or core.stat().st_size < 1_000_000:
    raise SystemExit("Missing/empty Azahar threaded core binary")
if not sw.is_file() or not adapter.is_file():
    raise SystemExit("3DS adapter or isolation service worker missing")
if 'EJS_threads = true' not in player or 'EJS_core = "3ds"' not in player:
    raise SystemExit("3DS runtime configuration missing from player")
if 'crossOriginIsolated' not in adapter.read_text(encoding="utf-8"):
    raise SystemExit("Missing cross-origin isolation probe")
if 'id="threeDsHost"' not in main or 'coi-serviceworker.js' not in main:
    raise SystemExit("3DS host/isolation bootstrap missing from index")
script = re.search(r'<script type="module">([\s\S]*?)</script>', main)
player_script = re.search(r'<script>([\s\S]*?)</script>', player)
if not script or not player_script:
    raise SystemExit("Could not find embedded JavaScript in emulator pages")
for name, source in [
    ("index module", script.group(1)),
    ("3DS player", player_script.group(1)),
    ("3DS adapter", adapter.read_text(encoding="utf-8")),
    ("COI helper", sw.read_text(encoding="utf-8")),
]:
    result = subprocess.run(
        ["node", "--input-type=module", "--check"],
        input=source, text=True, capture_output=True,
    )
    if result.returncode:
        raise SystemExit(f"Syntax error in {name}:\n{result.stderr}")
    print(f"OK: {name} syntax")
print("OK: Azahar 3DS frontend/core files present (ROM boot still untested)")
