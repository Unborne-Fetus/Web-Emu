#!/usr/bin/env python3
"""Patch a pinned copy of mGBA's browser SDK with 1–4× clock control."""
from pathlib import Path
p=Path("upstream/src/mgba.sdk.ts")
s=p.read_text()
def replace_once(before,after):
    global s
    if s.count(before)!=1:
        raise RuntimeError(f"SDK changed; expected one match for {before[:70]!r}, got {s.count(before)}")
    s=s.replace(before,after)
replace_once("  let coreRate = 0;","  let coreRate = 0;\n  let speedMultiplier = 1;")
replace_once("sink.port.postMessage({ rate });","sink.port.postMessage({ rate: rate * speedMultiplier });")
replace_once("const MAX_FRAMES_PER_TICK = 5;","const MAX_FRAMES_PER_TICK = 24;")
replace_once("const perEmulatedFrame = rate / framerate;","const perEmulatedFrame = rate / framerate;")
replace_once("Math.floor(((now - wallClockStart) / 1000) * framerate)","Math.floor(((now - wallClockStart) / 1000) * framerate * speedMultiplier)")
replace_once("  const instance: MgbaInstance = {","  const instance: MgbaInstance & { setSpeed(multiplier: number): void } = {\n    setSpeed(multiplier: number) {\n      speedMultiplier = Math.max(1, Math.min(4, Math.round(multiplier)));\n      const rate = syncCoreRate();\n      if (rate) sink.port.postMessage({ rate: rate * speedMultiplier });\n      // Restart wall-clock fallback when switching speed.\n      wallClockStart = 0;\n    },")
p.write_text(s)
print("mGBA browser SDK patched successfully")
