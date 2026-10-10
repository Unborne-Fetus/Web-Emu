#!/usr/bin/env python3
"""Fail the multi-console artifact build if the extracted ZIP would need the web."""
from pathlib import Path
import re
import subprocess
import sys

if len(sys.argv) != 2:
    raise SystemExit("Usage: verify-offline-folder.py <extracted-package-root>")
root = Path(sys.argv[1]).resolve()
required = [
    "index.html",
    "Start-Web-Emu.cmd",
    "scripts/offline-server.cjs",
    "cores/3ds.js",
    "cores/3ds-player.html",
    "cores/retro.js",
    "cores/retro-player.html",
    "coi-serviceworker.js",
    "vendor/mgba-sdk.js",
    "vendor/mgba.js",
    "vendor/mgba.wasm",
    "vendor/emulatorjs/data/loader.js",
    "vendor/emulatorjs/data/emulator.min.js",
    "vendor/emulatorjs/data/emulator.min.css",
    "vendor/emulatorjs/data/cores/azahar-thread-wasm.data",
    "vendor/emulatorjs/data/cores/reports/azahar.json",
    "vendor/emulatorjs/data/compression/extractzip.js",
    "vendor/emulatorjs/data/compression/extract7z.js",
    "vendor/emulatorjs/data/compression/libunrar.js",
    "vendor/emulatorjs/data/compression/libunrar.wasm",
    "vendor/emulatorjs/LICENSE-GPL-3.0.txt",
    "licenses/coi-serviceworker-LICENSE",
    "runtime/node.exe",
    "runtime/NODE-LICENSE.txt",
]
retro_cores = (
    "desmume", "fceumm", "snes9x", "mupen64plus_next",
    "genesis_plus_gx", "stella2014", "beetle_vb",
)
for core in retro_cores:
    required.append(f"vendor/emulatorjs/data/cores/reports/{core}.json")
    for variant in ("-wasm", "-legacy-wasm", "-thread-wasm", "-thread-legacy-wasm"):
        required.append(f"vendor/emulatorjs/data/cores/{core}{variant}.data")

for rel in required:
    p = root / rel
    if not p.is_file() or p.stat().st_size < 10:
        raise SystemExit(f"Offline ZIP incomplete: missing {rel}")
if (root / "runtime/node.exe").open("rb").read(2) != b"MZ":
    raise SystemExit("Bundled Windows node.exe isn't a Windows executable")
if (root / "vendor/mgba.wasm").open("rb").read(4) != bytes([0, 97, 115, 109]):
    raise SystemExit("Bundled mGBA core is not WebAssembly")
if (root / "vendor/emulatorjs/data/cores/azahar-thread-wasm.data").stat().st_size < 1_000_000:
    raise SystemExit("Azahar WebAssembly core is incomplete")
launcher = (root / "Start-Web-Emu.cmd").read_text(encoding="utf-8")
server = (root / "scripts/offline-server.cjs").read_text(encoding="utf-8")
player = (root / "cores/3ds-player.html").read_text(encoding="utf-8")
index = (root / "index.html").read_text(encoding="utf-8")
if "runtime\\node.exe" not in launcher:
    raise SystemExit("Launcher does not point at the bundled Node executable")
if "Cross-Origin-Opener-Policy" not in server or "Cross-Origin-Embedder-Policy" not in server:
    raise SystemExit("Offline localhost HTTP server is missing thread isolation headers")
if 'EJS_pathtodata = new URL("../vendor/emulatorjs/data/"' not in player:
    raise SystemExit("3DS player does not use bundled EmulatorJS files")
if './vendor/mgba-sdk.js' not in index:
    raise SystemExit("GBA player does not use its bundled SDK")
for rel in ("scripts/offline-server.cjs", "cores/3ds.js", "cores/retro.js"):
    p = root / rel
    proc = subprocess.run(
        ["node", "--input-type=module", "--check"],
        input=p.read_text(encoding="utf-8"), capture_output=True, text=True
    )
    if proc.returncode:
        raise SystemExit(f"JavaScript parse failed: {rel}: {proc.stderr}")
retro_player = (root / "cores/retro-player.html").read_text(encoding="utf-8")
if 'EJS_core = data.system' not in retro_player:
    raise SystemExit("Retro player does not dynamically select requested console")
if 'window.EJS_pathtodata = new URL("../vendor/emulatorjs/data/"' not in retro_player:
    raise SystemExit("Retro player does not load locally bundled cores")
if '"desmume"' not in retro_player:
    raise SystemExit("Nintendo DS default needs a bootable DeSmuME WASM core")
if 'id="classicSystem"' not in index or 'id="tabClassic"' not in index:
    raise SystemExit("Classic console selector is missing from the UI")
for core in retro_cores:
    for variant in ("-wasm", "-legacy-wasm", "-thread-wasm", "-thread-legacy-wasm"):
        p = root / f"vendor/emulatorjs/data/cores/{core}{variant}.data"
        if p.stat().st_size < 100_000:
            raise SystemExit(f"Core data appears truncated: {p}")
import re
for label, source in (
    ("main interface", re.search(r'<script type="module">([\s\S]*?)</script>', index)),
    ("retro player", re.search(r'<script>([\s\S]*?)</script>', retro_player)),
):
    if not source:
        raise SystemExit(f"Cannot find embedded script for {label}")
    proc = subprocess.run(
        ["node", "--input-type=module", "--check"],
        input=source.group(1), capture_output=True, text=True
    )
    if proc.returncode:
        raise SystemExit(f"JavaScript parse failed: {label}: {proc.stderr}")
print(f"OK: {len(required)} essential offline files, seven bundled libretro cores, 9 classic systems, localhost headers, JS syntax")

