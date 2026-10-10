#!/usr/bin/env python3
"""Vendor the Azahar/EmulatorJS nightly runtime for hosted and offline builds.

A real archive is included in the output. The built game launcher never
requests the core from an external site. All downloads happen at build time.
"""
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from time import sleep
import json

root = Path(__file__).resolve().parent.parent
target = root / "vendor" / "emulatorjs"
base = "https://cdn.emulatorjs.org/nightly/data/"
assets = [
    "loader.js", "emulator.min.js", "emulator.min.css", "version.json",
    "emulator.css",
    "cores/azahar-thread-wasm.data",
    "cores/reports/azahar.json",
    "compression/extractzip.js",
    "compression/extract7z.js",
    "compression/libunrar.js",
    "compression/libunrar.wasm",
]
# Real libretro cores for Nintendo DS, NES, SNES, Nintendo 64,
# Genesis/Game Gear/Master System, Atari 2600 and Virtual Boy.
# Include every WASM variant: EmulatorJS chooses legacy/threads at runtime.
retro_cores = (
    "desmume", "fceumm", "snes9x", "mupen64plus_next",
    "genesis_plus_gx", "stella2014", "beetle_vb",
)
for core_name in retro_cores:
    assets.append(f"cores/reports/{core_name}.json")
    for variant in ("-wasm", "-legacy-wasm", "-thread-wasm", "-thread-legacy-wasm"):
        assets.append(f"cores/{core_name}{variant}.data")

assets += [f"localization/{name}.json" for name in (
    "ar", "bn", "de", "el", "en", "es", "fa", "fr", "hi", "it",
    "ja", "jv", "km", "ko", "pt", "retroarch", "ro", "ru",
    "tr", "ua", "ur", "vi", "zh"
)]
assets += [f"src/{name}.js" for name in (
    "GameManager", "cache", "compression", "consts", "emulator",
    "frontend", "gamepad", "license", "netplay", "nipplejs",
    "setup", "shaders", "socket.io.min", "storage", "utils"
)]
assets += ["src/vendor/nipplejs.js", "src/vendor/socket.io.min.js"]

def download(url, dest):
    dest.parent.mkdir(parents=True, exist_ok=True)
    last_error = None
    for attempt in range(4):
        try:
            req = Request(url, headers={"User-Agent": "Web-Emu-offline-builder/1.0"})
            with urlopen(req, timeout=90) as source, dest.open("wb") as output:
                while chunk := source.read(1024 * 1024):
                    output.write(chunk)
            if dest.stat().st_size < 10:
                raise RuntimeError(f"Empty file: {url}")
            print(f"Fetched {url} ({dest.stat().st_size:,} bytes)", flush=True)
            return
        except (HTTPError, URLError, OSError, RuntimeError) as error:
            last_error = error
            dest.unlink(missing_ok=True)
            if attempt < 3:
                sleep(attempt + 1)
    raise SystemExit(f"Failed to download required offline asset {url}: {last_error}")

for name in assets:
    download(base + name, target / "data" / name)

download("https://raw.githubusercontent.com/EmulatorJS/EmulatorJS/main/LICENSE",
         target / "LICENSE-GPL-3.0.txt")

core = target / "data" / "cores" / "azahar-thread-wasm.data"
if core.stat().st_size < 1_000_000:
    raise SystemExit("Azahar archive is unexpectedly small; refusing to deploy")
report = json.loads((target / "data" / "cores" / "reports" / "azahar.json").read_text())
if not isinstance(report, dict):
    raise SystemExit("Unexpected Azahar build report")
print(f"EmulatorJS runtime bundled locally ({len(assets)} files; {len(retro_cores)} classic cores, 9 classic systems; Azahar {core.stat().st_size:,} bytes)")
