#!/usr/bin/env python3
"""Assemble the *offline* multi-console folder from already downloaded cores.

No remote assets are fetched by this script. It fails rather than ship a
partially online build. Windows node.exe is added by the Actions workflow.
"""
from pathlib import Path
from shutil import copy2, copytree
import json

root = Path(__file__).resolve().parent.parent
package = root / "dist-offline-complete" / "Web-Emu-Offline"

required = [
    "index.html",
    "coi-serviceworker.js",
    "Start-Web-Emu.cmd",
    "cores/3ds.js",
    "cores/3ds-player.html",
    "scripts/offline-server.cjs",
    "cores/retro.js",
    "cores/retro-player.html",
    "vendor/mgba-sdk.js",
    "vendor/mgba.js",
    "vendor/mgba.wasm",
    "vendor/emulatorjs/data/loader.js",
    "vendor/emulatorjs/data/emulator.min.js",
    "vendor/emulatorjs/data/emulator.min.css",
    "vendor/emulatorjs/data/cores/azahar-thread-wasm.data",
    "vendor/emulatorjs/data/cores/reports/azahar.json",
    # The player selects legacy/threads variants dynamically. All four
    # must be included to guarantee an actually offline core load.
    *(
        f"vendor/emulatorjs/data/cores/{core}{variant}.data"
        for core in (
            "desmume", "fceumm", "snes9x", "mupen64plus_next",
            "genesis_plus_gx", "stella2014", "beetle_vb",
        )
        for variant in ("-wasm", "-legacy-wasm", "-thread-wasm", "-thread-legacy-wasm")
    ),
    *(
        f"vendor/emulatorjs/data/cores/reports/{core}.json"
        for core in (
            "desmume", "fceumm", "snes9x", "mupen64plus_next",
            "genesis_plus_gx", "stella2014", "beetle_vb",
        )
    ),

    "vendor/emulatorjs/data/compression/extractzip.js",
    "vendor/emulatorjs/data/compression/extract7z.js",
    "vendor/emulatorjs/data/compression/libunrar.js",
    "vendor/emulatorjs/data/compression/libunrar.wasm",
    "vendor/emulatorjs/LICENSE-GPL-3.0.txt",
    "licenses/coi-serviceworker-LICENSE",
]
for rel in required:
    path = root / rel
    if not path.is_file() or not path.stat().st_size:
        raise SystemExit(f"Cannot produce complete offline package. Missing: {rel}")

if (root / "vendor" / "emulatorjs" / "data" / "cores" / "azahar-thread-wasm.data").stat().st_size < 1_000_000:
    raise SystemExit("Azahar core appears incomplete")

package.mkdir(parents=True, exist_ok=True)
for rel in required[:8]:
    dst = package / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    copy2(root / rel, dst)
copytree(root / "vendor", package / "vendor", dirs_exist_ok=True)
copytree(root / "licenses", package / "licenses", dirs_exist_ok=True)
copy2(root / "README.md", package / "README.md")
print(f"Offline package staged: {package}")
print(f"Local files: {sum(1 for p in package.rglob('*') if p.is_file())}")
print("Windows Node runtime (node.exe) must still be bundled before upload.")
