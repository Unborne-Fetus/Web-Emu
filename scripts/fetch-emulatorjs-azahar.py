#!/usr/bin/env python3
"""Download EmulatorJS assets and every configured console's actual WASM core.

All network access happens in GitHub Actions, never while playing offline.
Core variants are discovered instead of assuming nonexistent thread/legacy
builds exist for every libretro emulator.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import json
import time

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "vendor" / "emulatorjs" / "data"
BASE = "https://cdn.emulatorjs.org/nightly/data/"
SYSTEMS = json.loads((ROOT / "cores" / "retro-systems.json").read_text(encoding="utf-8"))["systems"]
CORES = {info["core"]: bool(info.get("threads")) for info in SYSTEMS.values()}
if len(SYSTEMS) < 27:
    raise SystemExit("The console manifest is incomplete")
if len(CORES) < 20:
    raise SystemExit("Expected more unique emulator cores")

def download(relative: str, *, required: bool = True) -> bool:
    dest = DATA / relative
    dest.parent.mkdir(parents=True, exist_ok=True)
    last_error = None
    for attempt in range(3 if required else 2):
        try:
            req = Request(BASE + relative, headers={"User-Agent": "Web-Emu-offline-builder/2.0"})
            with urlopen(req, timeout=120) as source, dest.open("wb") as output:
                while chunk := source.read(1024 * 1024):
                    output.write(chunk)
            if dest.stat().st_size < 10:
                raise OSError("Downloaded file is empty")
            print(f"Fetched {relative}: {dest.stat().st_size:,} bytes", flush=True)
            return True
        except HTTPError as error:
            last_error = error
            dest.unlink(missing_ok=True)
            if error.code in (403, 404, 410) and not required:
                print(f"Optional upstream asset unavailable: {relative} ({error.code})", flush=True)
                return False
            if error.code in (403, 404, 410) and required:
                break
        except (URLError, OSError, TimeoutError) as error:
            last_error = error
            dest.unlink(missing_ok=True)
        if attempt < (2 if required else 1):
            time.sleep(attempt + 1)
    if required:
        raise RuntimeError(f"Missing required offline asset {relative}: {last_error}")
    print(f"Optional upstream asset skipped: {relative} ({last_error})", flush=True)
    return False

# Only these frontend assets are needed when the standard minified release is used.
# Avoid hardcoded guessed src/vendor paths: they have broken nightly CI on 404.
required_files = [
    "loader.js",
    "emulator.min.js",
    "emulator.min.css",
    "compression/extractzip.js",
    "compression/extract7z.js",
    "compression/libunrar.js",
    "compression/libunrar.wasm",
    "cores/azahar-thread-wasm.data",
    "cores/ppsspp-assets.zip",
]
for rel in required_files:
    download(rel)

# Language files are nice offline but not every upstream locale exists.
optional_files = [
    "version.json",
    "emulator.css",
    *[f"localization/{name}.json" for name in (
        "en", "es", "fr", "de", "it", "ja", "zh", "ko", "pt", "ru",
        "ar", "hi", "tr", "ro", "vi", "fa", "el", "bn", "km", "ur",
    )],
]
with ThreadPoolExecutor(max_workers=5) as pool:
    jobs = [pool.submit(download, rel, required=False) for rel in optional_files]
    for future in as_completed(jobs):
        future.result()

# Every configured libretro emulator needs its own real build, not just a UI tab.
# Threads are *required* by PPSSPP and DOSBox Pure; classic cores run single-threaded.
# On a modern browser EmulatorJS loads -wasm, and on an older browser -legacy-wasm.
# Download whichever builds actually exist for this nightly.
variants = {}
def fetch_core(core: str, threaded: bool) -> tuple[str, dict]:
    prefix = f"cores/{core}{'-thread' if threaded else ''}"
    found = {}
    for style, suffix in (("webgl2", "-wasm.data"), ("legacy", "-legacy-wasm.data")):
        rel = prefix + suffix
        found[style] = download(rel, required=False)
    if not any(found.values()):
        raise RuntimeError(
            f"Neither required {core} core variant exists upstream. "
            "Refusing to publish an offline package that cannot run this system."
        )

    report_path = f"cores/reports/{core}.json"
    if not download(report_path, required=False):
        report = {"buildStart": 1, "name": core, "options": {}}
    else:
        try:
            report = json.loads((DATA / report_path).read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            report = {"buildStart": 1, "name": core, "options": {}}
    if not isinstance(report, dict):
        report = {"buildStart": 1, "name": core, "options": {}}
    if not isinstance(report.get("options"), dict):
        report["options"] = {}
    original_default = bool(report["options"].get("defaultWebGL2", True))
    # Prefer the upstream rendering choice, unless that variant was unavailable.
    report["options"]["defaultWebGL2"] = (
        original_default if found["webgl2"] and found["legacy"]
        else bool(found["webgl2"])
    )
    report["buildStart"] = report.get("buildStart") or 1
    (DATA / report_path).write_text(json.dumps(report), encoding="utf-8")
    return core, {"threads": threaded, **found}

with ThreadPoolExecutor(max_workers=4) as pool:
    jobs = {pool.submit(fetch_core, core, thread): core for core, thread in CORES.items()}
    for future in as_completed(jobs):
        core, result = future.result()
        variants[core] = result

# Azahar is a threaded, WebGL2-only 3DS core.
azahar_report = "cores/reports/azahar.json"
if not download(azahar_report, required=False):
    (DATA / azahar_report).parent.mkdir(parents=True, exist_ok=True)
    (DATA / azahar_report).write_text(
        json.dumps({"buildStart": 1, "options": {"defaultWebGL2": True}}), encoding="utf-8"
    )
variants["azahar"] = {"threads": True, "webgl2": True, "legacy": False}
(DATA / "cores" / "webemu-variants.json").write_text(
    json.dumps(variants, indent=2, sort_keys=True), encoding="utf-8"
)

def fetch_license():
    url = "https://raw.githubusercontent.com/EmulatorJS/EmulatorJS/main/LICENSE"
    dest = ROOT / "vendor" / "emulatorjs" / "LICENSE-GPL-3.0.txt"
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = Request(url, headers={"User-Agent": "Web-Emu-offline-builder/2.0"})
    with urlopen(req, timeout=60) as source, dest.open("wb") as output:
        while chunk := source.read(64 * 1024):
            output.write(chunk)
    if dest.stat().st_size < 1000:
        raise RuntimeError("EmulatorJS license download incomplete")

fetch_license()
azahar_size = (DATA / "cores" / "azahar-thread-wasm.data").stat().st_size
if azahar_size < 1_000_000:
    raise RuntimeError("Azahar WASM archive too small")
print(f"Bundled {len(SYSTEMS)} classic console variants using {len(CORES)} unique libretro WASM cores plus Azahar ({azahar_size:,} bytes)", flush=True)
