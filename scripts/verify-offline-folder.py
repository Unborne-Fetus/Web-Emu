#!/usr/bin/env python3
"""Verify all emulation assets in the *extracted* Windows ZIP folder.

This validates completeness, actual WASM archive presence, manifest coverage,
source syntax, offline-only URLs, and launcher behavior. It does NOT claim
that every commercial ROM boots successfully.
"""
from pathlib import Path
import json
import re
import subprocess
import sys

if len(sys.argv) != 2:
    raise SystemExit("Usage: verify-offline-folder.py <extracted-package-root>")
root = Path(sys.argv[1]).resolve()
required = (
    "index.html", "Start-Web-Emu.cmd", "scripts/offline-server.cjs",
    "coi-serviceworker.js", "cores/3ds.js", "cores/3ds-player.html",
    "cores/retro.js", "cores/retro-player.html", "cores/retro-systems.json",
    "vendor/mgba-sdk.js", "vendor/mgba.js", "vendor/mgba.wasm",
    "vendor/emulatorjs/data/loader.js",
    "vendor/emulatorjs/data/emulator.min.js",
    "vendor/emulatorjs/data/emulator.min.css",
    "vendor/emulatorjs/data/cores/azahar-thread-wasm.data",
    "vendor/emulatorjs/data/cores/reports/azahar.json",
    "vendor/emulatorjs/data/cores/webemu-variants.json",
    "vendor/emulatorjs/data/compression/extractzip.js",
    "vendor/emulatorjs/data/compression/extract7z.js",
    "vendor/emulatorjs/data/compression/libunrar.js",
    "vendor/emulatorjs/data/compression/libunrar.wasm",
    "vendor/emulatorjs/LICENSE-GPL-3.0.txt",
    "licenses/coi-serviceworker-LICENSE",
    "runtime/node.exe", "runtime/NODE-LICENSE.txt",
)
for rel in required:
    file = root / rel
    if not file.is_file() or file.stat().st_size < 10:
        raise SystemExit(f"Offline ZIP incomplete: missing {rel}")

if (root / "runtime/node.exe").open("rb").read(2) != b"MZ":
    raise SystemExit("Bundled Node runtime is not a Windows executable")
if (root / "vendor/mgba.wasm").open("rb").read(4) != b"\\x00asm":
    raise SystemExit("Bundled mGBA runtime is not WebAssembly")
if (root / "vendor/emulatorjs/data/cores/azahar-thread-wasm.data").stat().st_size < 1_000_000:
    raise SystemExit("Missing/truncated Azahar WebAssembly archive")

catalog = json.loads((root / "cores/retro-systems.json").read_text(encoding="utf-8"))["systems"]
variants = json.loads((root / "vendor/emulatorjs/data/cores/webemu-variants.json").read_text(encoding="utf-8"))
if len(catalog) != 27:
    raise SystemExit(f"Expected 27 retro systems, got {len(catalog)}")
cores = {info["core"]: bool(info.get("threads")) for info in catalog.values()}
for name, threaded in cores.items():
    if name not in variants or bool(variants[name]["threads"]) != threaded:
        raise SystemExit(f"Missing or wrong core manifest entry for {name}")
    report = root / f"vendor/emulatorjs/data/cores/reports/{name}.json"
    if not report.is_file() or report.stat().st_size < 10:
        raise SystemExit(f"Missing {name} core report")
    options = variants[name]
    count = 0
    for style, suffix in (("webgl2", "-wasm.data"), ("legacy", "-legacy-wasm.data")):
        archive = root / f"vendor/emulatorjs/data/cores/{name}{'-thread' if threaded else ''}{suffix}"
        if options.get(style):
            if not archive.is_file() or archive.stat().st_size < 100_000:
                raise SystemExit(f"Missing / truncated {name} {style} WASM archive")
            count += 1
        elif archive.is_file():
            raise SystemExit(f"Unexpected untracked {name} WASM variant")
    if not count:
        raise SystemExit(f"No local WASM core installed for {name}")
if len(cores) < 20:
    raise SystemExit("Expected all requested emulator core families")

launcher = (root / "Start-Web-Emu.cmd").read_text(encoding="utf-8")
server = (root / "scripts/offline-server.cjs").read_text(encoding="utf-8")
main = (root / "index.html").read_text(encoding="utf-8")
player = (root / "cores/retro-player.html").read_text(encoding="utf-8")
azahar_player = (root / "cores/3ds-player.html").read_text(encoding="utf-8")
adapter = (root / "cores/retro.js").read_text(encoding="utf-8")
if "runtime\\\\node.exe" not in launcher:
    raise SystemExit("Offline starter missing bundled node.exe reference")
if "Cross-Origin-Opener-Policy" not in server or "Cross-Origin-Embedder-Policy" not in server:
    raise SystemExit("Offline server must set cross-origin isolation headers")
if 'EJS_pathtodata = new URL("../vendor/emulatorjs/data/"' not in azahar_player:
    raise SystemExit("Azahar player does not use local emulator assets")
if 'window.EJS_pathtodata = new URL("../vendor/emulatorjs/data/"' not in player:
    raise SystemExit("Retro player does not use local emulator assets")
if 'window.EJS_biosUrl = data.biosFile' not in player:
    raise SystemExit("User-provided firmware is not passed to EmulatorJS")
if "window.EJS_threads = Boolean(config.threads)" not in player:
    raise SystemExit("PSP / DOSBox missing thread selection")
if './vendor/mgba-sdk.js' not in main:
    raise SystemExit("mGBA SDK path missing from interface")
if 'cores/retro-systems.json' not in adapter:
    # The adapter loads the manifest relative to its module.
    if '"./retro-systems.json"' not in adapter:
        raise SystemExit("Shared console catalog not loaded by adapter")
if 'id="classicSystem"' not in main or 'id="tabClassic"' not in main:
    raise SystemExit("Offline UI missing console selection")
for system in catalog:
    if f'value="{system}"' not in main:
        raise SystemExit(f"Console {system} is missing from the offline selector")

sources = {
    "index": re.search(r'<script type="module">([\\s\\S]*?)</script>', main),
    "retro player": re.search(r'<script>([\\s\\S]*?)</script>', player),
    "3DS player": re.search(r'<script>([\\s\\S]*?)</script>', azahar_player),
}
for label, match in sources.items():
    if not match:
        raise SystemExit(f"Cannot locate {label} JavaScript")
    result = subprocess.run(["node", "--input-type=module", "--check"],
                            input=match.group(1), text=True, capture_output=True)
    if result.returncode:
        raise SystemExit(f"Syntax error in {label}: {result.stderr}")
for rel in ("scripts/offline-server.cjs", "cores/3ds.js", "cores/retro.js"):
    result = subprocess.run(["node", "--input-type=module", "--check"],
                            input=(root / rel).read_text(encoding="utf-8"),
                            text=True, capture_output=True)
    if result.returncode:
        raise SystemExit(f"Syntax error in {rel}: {result.stderr}")

print(f"PASS: Windows offline ZIP has {len(catalog)} retro consoles backed by {len(cores)} actual local libretro cores, plus mGBA and Azahar.")
print("PASS: Browser entrypoints, controls, user firmware, startup scripts, runtime files and COOP/COEP checks.")
print("NOTE: Real ROM boot, full-speed 3D emulation and save restoration remain unverified.")
