#!/usr/bin/env python3
"""Stage a complete Windows offline folder with every configured console core.

The build fetches cores before this step. Missing systems are fatal. No network
requests are made during offline packaging or gameplay.
"""
from pathlib import Path
from shutil import copy2, copytree, rmtree
import json

root = Path(__file__).resolve().parent.parent
output = root / "dist-offline-complete" / "Web-Emu-Offline"
app_files = (
    "index.html", "coi-serviceworker.js", "Start-Web-Emu.cmd",
    "cores/3ds.js", "cores/3ds-player.html",
    "cores/retro.js", "cores/retro-player.html",
    "cores/retro-systems.json", "scripts/offline-server.cjs",
)
static_files = (
    "vendor/mgba-sdk.js", "vendor/mgba.js", "vendor/mgba.wasm",
    "vendor/emulatorjs/data/loader.js",
    "vendor/emulatorjs/data/emulator.min.js",
    "vendor/emulatorjs/data/emulator.min.css",
    "vendor/emulatorjs/data/cores/azahar-thread-wasm.data",
    "vendor/emulatorjs/data/cores/ppsspp-assets.zip",
    "vendor/emulatorjs/data/cores/reports/azahar.json",
    "vendor/emulatorjs/data/cores/webemu-variants.json",
    "vendor/emulatorjs/data/compression/extractzip.js",
    "vendor/emulatorjs/data/compression/extract7z.js",
    "vendor/emulatorjs/data/compression/libunrar.js",
    "vendor/emulatorjs/data/compression/libunrar.wasm",
    "vendor/emulatorjs/LICENSE-GPL-3.0.txt",
    "licenses/coi-serviceworker-LICENSE",
)
for rel in (*app_files, *static_files, "README.md"):
    file = root / rel
    if not file.is_file() or file.stat().st_size < 10:
        raise SystemExit(f"Cannot package offline Web Emu: missing {rel}")

catalog = json.loads((root / "cores/retro-systems.json").read_text(encoding="utf-8"))["systems"]
variants = json.loads((root / "vendor/emulatorjs/data/cores/webemu-variants.json").read_text(encoding="utf-8"))
if len(catalog) != 27:
    raise SystemExit(f"Expected 27 retro systems, got {len(catalog)}")
cores = {info["core"]: bool(info.get("threads")) for info in catalog.values()}
for name, threaded in cores.items():
    if name not in variants or bool(variants[name]["threads"]) != threaded:
        raise SystemExit(f"Missing/incorrect {name} WebAssembly core variant manifest")
    report = root / f"vendor/emulatorjs/data/cores/reports/{name}.json"
    if not report.is_file():
        raise SystemExit(f"Missing offline core metadata for {name}")
    prefix = f"vendor/emulatorjs/data/cores/{name}{'-thread' if threaded else ''}"
    if not any((root / (prefix + suffix)).is_file()
               for suffix in ("-wasm.data", "-legacy-wasm.data")):
        raise SystemExit(f"Offline package cannot run {name}: no matching WASM core")

psp_assets = root / "vendor/emulatorjs/data/cores/ppsspp-assets.zip"
if psp_assets.stat().st_size < 5_000_000 or psp_assets.open("rb").read(4)[:2] != b"PK":
    raise SystemExit("Missing / invalid PPSSPP assets ZIP: PSP cannot initialize offline")
if (root / "vendor/emulatorjs/data/cores/azahar-thread-wasm.data").stat().st_size < 1_000_000:
    raise SystemExit("Azahar core appears truncated")
if output.exists():
    rmtree(output)
output.mkdir(parents=True)
for rel in app_files:
    dest = output / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    copy2(root / rel, dest)
copytree(root / "vendor", output / "vendor", dirs_exist_ok=True)
copytree(root / "licenses", output / "licenses", dirs_exist_ok=True)
copy2(root / "README.md", output / "README.md")

print(f"Offline package staged at {output}")
print(f"Retro: {len(catalog)} systems using {len(cores)} unique libretro cores; Azahar + mGBA included")
print(f"Files: {sum(1 for p in output.rglob('*') if p.is_file())}")
print("GitHub Actions adds Windows node.exe before ZIP upload.")
