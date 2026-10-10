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
for rel in ("scripts/offline-server.cjs", "cores/3ds.js"):
    p = root / rel
    proc = subprocess.run(["node", "--check", str(p)], capture_output=True, text=True)
    if proc.returncode:
        raise SystemExit(f"JavaScript parse failed: {rel}: {proc.stderr}")
print(f"OK: {len(required)} essential offline files, Windows exe, WASM, localhost security headers, JS syntax")
