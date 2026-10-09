#!/usr/bin/env python3
"""Apply file:// compatibility changes to the mGBA wrapper before bundling."""
from pathlib import Path
p = Path("upstream/src/mgba.sdk.ts")
s = p.read_text()
def once(before, after):
    global s
    if s.count(before) != 1:
        raise RuntimeError("Upstream SDK changed: " + repr(before[:90]))
    s = s.replace(before, after)

# Offline single-file builds embed Emscripten's classic runtime beforehand.
once("  await loadClassicScriptOnce(jsUrl);",
     "  if (typeof (globalThis as { createMgbaModule?: unknown }).createMgbaModule !== 'function') await loadClassicScriptOnce(jsUrl);")

before = """  const workletUrl = URL.createObjectURL(
    new Blob([WORKLET_SOURCE], { type: 'application/javascript' }),
  );
  await audioCtx.audioWorklet.addModule(workletUrl);
  URL.revokeObjectURL(workletUrl);

  const sink = new AudioWorkletNode(audioCtx, 'mgba-sink', {
    numberOfInputs: 0,
    numberOfOutputs: 1,
    outputChannelCount: [2],
  });"""
after = """  let sink: AudioWorkletNode | (ScriptProcessorNode & {port: {postMessage: (message: unknown, transfer?: Transferable[]) => void}});
  if (location.protocol !== 'file:' && audioCtx.audioWorklet) {
    try {
      const workletUrl = URL.createObjectURL(
        new Blob([WORKLET_SOURCE], { type: 'application/javascript' }),
      );
      try {
        await audioCtx.audioWorklet.addModule(workletUrl);
      } finally {
        URL.revokeObjectURL(workletUrl);
      }
      sink = new AudioWorkletNode(audioCtx, 'mgba-sink', {
        numberOfInputs: 0,
        numberOfOutputs: 1,
        outputChannelCount: [2],
      });
    } catch (error) {
      console.warn('AudioWorklet unavailable; using compatibility audio.', error);
      sink = createFallbackAudio(audioCtx);
    }
  } else {
    sink = createFallbackAudio(audioCtx);
  }"""
once(before, after)

# Main-thread fallback to avoid blob:null AudioWorklet module imports on file://.
# Source frames are consumed in the audio callback; keep the original SDK's pacing counters.
fallback = """
function createFallbackAudio(ctx: AudioContext): ScriptProcessorNode & {
  port: { postMessage(message: unknown, transfer?: Transferable[]): void };
} {
  const node = ctx.createScriptProcessor(2048, 0, 2) as ScriptProcessorNode & {
    port: { postMessage(message: unknown, transfer?: Transferable[]): void };
  };
  const cap = 32768;
  const buffer = new Float32Array(cap * 2);
  let written = 0;
  let cursor = 0;
  let ratio = 1;
  node.port = {
    postMessage(message: unknown) {
      if (message && typeof message === 'object' && 'reset' in message) {
        written = 0; cursor = 0;
        return;
      }
      if (message && typeof message === 'object' && 'rate' in message) {
        const rate = Number((message as {rate: number}).rate);
        ratio = Math.max(0.01, rate / ctx.sampleRate);
        return;
      }
      if (!(message instanceof Int16Array)) return;
      for (let i = 0; i < message.length / 2; i++) {
        if (written - cursor >= cap - 2) break;
        const pos = (written % cap) * 2;
        buffer[pos] = message[i * 2] / 32768;
        buffer[pos + 1] = message[i * 2 + 1] / 32768;
        written++;
      }
    },
  };
  node.onaudioprocess = (event) => {
    const l = event.outputBuffer.getChannelData(0);
    const r = event.outputBuffer.getChannelData(1);
    for (let i = 0; i < l.length; i++) {
      if (cursor + 1 < written) {
        const base = Math.floor(cursor);
        const f = cursor - base;
        const j = (base % cap) * 2;
        const k = ((base + 1) % cap) * 2;
        l[i] = buffer[j] + (buffer[k] - buffer[j]) * f;
        r[i] = buffer[j+1] + (buffer[k+1] - buffer[j+1]) * f;
        cursor += ratio;
      } else {
        l[i] = 0; r[i] = 0;
      }
    }
    const consumed = Math.floor(cursor);
    if (node.onFallbackConsumed) node.onFallbackConsumed(consumed);
  };
  return node;
}
"""
# Fallback needs to report consumption to the SDK counters.
fallback=fallback.replace("  node.onaudioprocess =", "  (node as any).onFallbackConsumed = null;\n  node.onaudioprocess =")
once("const scriptLoadCache = new Map<string, Promise<void>>();", fallback+"\nconst scriptLoadCache = new Map<string, Promise<void>>();")
once("  sink.port.onmessage = (e: MessageEvent<number>) => {\n    consumedFrames = e.data;\n  };",
"""  sink.port.onmessage = (e: MessageEvent<number>) => {
    consumedFrames = e.data;
  };
  if ('onFallbackConsumed' in sink) {
    (sink as any).onFallbackConsumed = (frames: number) => { consumedFrames = frames; };
  }""")
p.write_text(s)
print("Offline audio and embedded runtime support patched.")
