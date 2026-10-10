#!/usr/bin/env python3
"""Static deployment smoke test for 3DS and nine classic systems; not real ROM boot."""
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
retro_adapter = Path("cores/retro.js")
retro_player = Path("cores/retro-player.html")
if not retro_adapter.is_file() or not retro_player.is_file():
    raise SystemExit("Classic consoles adapter/player missing")
retro_source = retro_player.read_text(encoding="utf-8")
adapter_source = retro_adapter.read_text(encoding="utf-8")
if 'id="classicSystem"' not in main or 'id="tabClassic"' not in main:
    raise SystemExit("Classic consoles selector missing from index")
retro_cores = (
    "desmume", "fceumm", "snes9x", "mupen64plus_next",
    "genesis_plus_gx", "stella2014", "beetle_vb",
)
for name in retro_cores:
    if name not in adapter_source or name not in retro_source:
        raise SystemExit(f"Missing libretro core mapping: {name}")
    report = runtime / "cores" / "reports" / f"{name}.json"
    if not report.is_file() or report.stat().st_size < 10:
        raise SystemExit(f"Missing libretro build report: {report}")
    for suffix in ("-wasm", "-legacy-wasm", "-thread-wasm", "-thread-legacy-wasm"):
        data = runtime / "cores" / f"{name}{suffix}.data"
        if not data.is_file() or data.stat().st_size < 100_000:
            raise SystemExit(f"Missing/incomplete bundled libretro core: {data}")

script = re.search(r'<script type="module">([\s\S]*?)</script>', main)
player_script = re.search(r'<script>([\s\S]*?)</script>', player)
retro_script = re.search(r'<script>([\s\S]*?)</script>', retro_source)
if not script or not player_script or not retro_script:
    raise SystemExit("Could not find embedded JavaScript in emulator pages")
for name, source in [
    ("index module", script.group(1)),
    ("3DS player", player_script.group(1)),
    ("3DS adapter", adapter.read_text(encoding="utf-8")),
    ("COI helper", sw.read_text(encoding="utf-8")),
    ("Classic player", retro_script.group(1)),
    ("Classic adapter", adapter_source),
]:
    result = subprocess.run(
        ["node", "--input-type=module", "--check"],
        input=source, text=True, capture_output=True,
    )
    if result.returncode:
        raise SystemExit(f"Syntax error in {name}:\n{result.stderr}")
    print(f"OK: {name} syntax")
print("OK: Azahar 3DS and nine classic systems with seven full local libretro core variants (ROM boot still untested)")
