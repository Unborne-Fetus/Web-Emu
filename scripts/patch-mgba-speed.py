#!/usr/bin/env python3
"""Patch a pinned copy of mGBA's browser SDK with 1–32× clock control."""
from pathlib import Path
p=Path("upstream/src/mgba.sdk.ts")
s=p.read_text()
def replace_once(before,after):
    global s
    if s.count(before)!=1:
        raise RuntimeError(f"SDK changed; expected one match for {before[:70]!r}, got {s.count(before)}")
    s=s.replace(before,after)
replace_once("  let coreRate = 0;","  let coreRate = 0;\n  let speedMultiplier = 1;\n  let autoSaveEnabled = true;\n  let lastDrawTime = 0;")
replace_once("sink.port.postMessage({ rate });","sink.port.postMessage({ rate: rate * speedMultiplier });")
# Reset worklet buffers on every speed transition: stale 32× audio must not poison 1× pacing.
replace_once("      if (msg && msg.rate) {", "      if (msg && msg.reset) {\\n        this.pos = 0; this.w = 0; this.lastPost = 0;\\n        return;\\n      }\\n      if (msg && msg.rate) {")
replace_once("const MAX_FRAMES_PER_TICK = 5;","const MAX_FRAMES_PER_TICK = 24;")
replace_once("Math.round(rate * TARGET_SECONDS) - buffered","Math.round(rate * speedMultiplier * TARGET_SECONDS) - buffered")

replace_once("Math.floor(((now - wallClockStart) / 1000) * framerate)","Math.floor(((now - wallClockStart) / 1000) * framerate * speedMultiplier)")
replace_once("  const instance: MgbaInstance = {","  const instance: MgbaInstance & { setSpeed(multiplier: number): void } = {\n    setSpeed(multiplier: number) {\n      const nextSpeed = Math.max(1, Math.min(32, Math.round(multiplier)));\n      if (nextSpeed === speedMultiplier) return;\n      speedMultiplier = nextSpeed;\n      // Discard high-speed samples and reset counters as one transition.\n      enqueuedFrames = 0; consumedFrames = 0;\n      sink.port.postMessage({ reset: true });\n      const rate = syncCoreRate();\n      if (rate) sink.port.postMessage({ rate: rate * speedMultiplier });\n      wallClockStart = 0; wallClockFrames = 0;\n      audioClockWall = performance.now();\n      lastDrawTime = 0;\n    },")

# Expose verified SRAM flushing and portable battery save backup.
replace_once(
    "  const persistSram = async (): Promise<void> => {",
    "  let persistQueue = Promise.resolve();\n  const persistSram = async (): Promise<void> => {"
)
replace_once(
    "    if (!persistEnabled) return;\n    const bytes = cloneSram();\n    if (!bytes) return;\n    const dir = await opfsDir(namespace, true);\n    if (!dir) return;\n    try {\n      const handle = await dir.getFileHandle('sram.bin', { create: true });\n      const writable = await handle.createWritable();\n      await writable.write(bytes);\n      await writable.close();\n    } catch {\n      // persistence is best-effort\n    }",
    "    if (!persistEnabled) return;\n    const bytes = cloneSram();\n    if (!bytes) throw new Error('Battery save data unavailable');\n    const write = async () => {\n      const dir = await opfsDir(namespace, true);\n      if (!dir) throw new Error('Browser save storage unavailable');\n      const handle = await dir.getFileHandle('sram.bin', { create: true });\n      const writable = await handle.createWritable();\n      try { await writable.write(bytes); await writable.close(); }\n      catch (e) { await writable.abort().catch(() => {}); throw e; }\n    };\n    const next = persistQueue.then(write);\n    persistQueue = next.catch(() => {});\n    return next;"
)
replace_once(
    "  const instance: MgbaInstance & { setSpeed(multiplier: number): void } = {",
    "  const instance: MgbaInstance & { setSpeed(multiplier: number): void; flushSave(): Promise<void>; exportSave(): Uint8Array; importSave(bytes: Uint8Array): Promise<void> } = {\n    async flushSave() { await persistSram(); },\n    exportSave() { const data = cloneSram(); if (!data) throw new Error('No battery save available'); return data; },\n    async importSave(data: Uint8Array) {\n      if (!data.length) throw new Error('Empty save file');\n      const ptr = heapAlloc(mod, data);\n      try { if (!mod._mgbawasm_sram_load(ptr, data.length)) throw new Error('Incompatible save file'); }\n      finally { mod._free(ptr); }\n      await persistSram();\n    },"
)

replace_once("setInterval(() => void persistSram(), 15000)", "setInterval(() => { if (autoSaveEnabled) void persistSram().catch(console.warn); }, 15000)")
if s.count("      void persistSram();") != 2: raise RuntimeError("SDK save hooks changed")
s=s.replace("      void persistSram();", "      if (autoSaveEnabled) void persistSram().catch(console.warn);")
replace_once("      renderFrame();\n    }\n\n    if (!fpsWindowStart)", "      if (speedMultiplier <= 2 || now - lastDrawTime >= (speedMultiplier <= 4 ? 32 : 65)) {\n        renderFrame();\n        lastDrawTime = now;\n      }\n    }\n\n    if (!fpsWindowStart)")\np.write_text(s)
print("mGBA browser SDK patched successfully")
