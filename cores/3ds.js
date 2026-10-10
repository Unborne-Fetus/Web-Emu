// Browser adapter for the threaded Azahar libretro core distributed by EmulatorJS.
// Runs in its own iframe: EmulatorJS owns its DOM and combines both 3DS screens.
const runtimeRoot = new URL("../vendor/emulatorjs/data/", import.meta.url);
const playerUrl = new URL("./3ds-player.html", import.meta.url);

export async function check3dsAvailability() {
  if (location.protocol !== "https:" && location.hostname !== "localhost" && location.hostname !== "127.0.0.1") {
    throw new Error("3DS emulation requires the hosted HTTPS site (or localhost); a double-clicked index.html cannot run the threaded Azahar core.");
  }
  if (!self.crossOriginIsolated || typeof SharedArrayBuffer === "undefined") {
    throw new Error("3DS needs cross-origin isolation and SharedArrayBuffer. Reload the hosted site once to activate its isolation service worker, then try again.");
  }
  if (!document.createElement("canvas").getContext("webgl2")) {
    throw new Error("Azahar requires WebGL 2. Enable hardware acceleration or use a compatible browser/device.");
  }
  const files = ["loader.js", "emulator.min.js", "emulator.min.css", "cores/azahar-thread-wasm.data"];
  for (const path of files) {
    let response;
    try {
      response = await fetch(new URL(path, runtimeRoot), { method: "HEAD", cache: "no-store" });
    } catch (error) {
      throw new Error("Cannot reach the bundled Azahar runtime: " + error.message);
    }
    if (!response.ok) throw new Error("Azahar runtime file is missing: " + path + " (HTTP " + response.status + "). Check the GitHub Pages build.");
  }
  return true;
}

export async function create3dsEmulator({ mount, file, onStatus = () => {} }) {
  if (!(file instanceof File) || !/\.(3ds|cci|cxi)$/i.test(file.name)) {
    throw new Error("Choose a compatible .3ds, .cci, or .cxi game file. CIA packages cannot be launched directly.");
  }
  if (!mount) throw new Error("Missing 3DS display container");
  await check3dsAvailability();
  const frame = document.createElement("iframe");
  frame.title = "Azahar Nintendo 3DS emulator";
  frame.className = "three-ds-frame";
  frame.setAttribute("allow", "fullscreen; gamepad; cross-origin-isolated");
  frame.setAttribute("allowfullscreen", "");
  frame.src = playerUrl.href;
  const session = "azahar-" + Math.random().toString(36).slice(2) + Date.now().toString(36);
  const origin = location.origin;
  let disposed = false;
  let ready = false;
  let resolveStart, rejectStart;
  const startup = new Promise((resolve, reject) => { resolveStart = resolve; rejectStart = reject; });
  const timeout = setTimeout(() => {
    if (!ready && !disposed) fail(new Error("Azahar did not finish initializing. Check browser console and your device's WebAssembly memory support."));
  }, 90000);
  function fail(error) {
    if (disposed) return;
    clearTimeout(timeout);
    if (!ready) rejectStart(error);
    else onStatus("3DS error: " + error.message);
    cleanup();
  }
  function onMessage(event) {
    if (event.source !== frame.contentWindow || event.origin !== origin) return;
    const msg = event.data;
    if (!msg || msg.session !== session || msg.emulator !== "webemu-azahar") return;
    if (msg.type === "ready") {
      ready = true;
      clearTimeout(timeout);
      onStatus("Azahar is ready. Start the game with its on-screen Play button if needed.");
      resolveStart();
    } else if (msg.type === "playing") {
      onStatus("Playing " + file.name + " · Azahar 3DS");
    } else if (msg.type === "status" && typeof msg.message === "string") {
      onStatus(msg.message);
    } else if (msg.type === "error") {
      fail(new Error(String(msg.message || "Unknown Azahar error")));
    }
  }
  function cleanup() {
    if (disposed) return;
    disposed = true;
    clearTimeout(timeout);
    window.removeEventListener("message", onMessage);
    frame.remove();
    mount.hidden = true;
  }
  window.addEventListener("message", onMessage);
  frame.addEventListener("load", () => {
    if (!disposed) frame.contentWindow.postMessage({ emulator: "webemu-azahar", type: "start", session, file }, origin);
  }, { once: true });
  frame.addEventListener("error", () => fail(new Error("Could not load 3DS player page")), { once: true });
  mount.replaceChildren(frame);
  mount.hidden = false;
  try {
    await startup;
  } catch (error) {
    cleanup();
    throw error;
  }
  return {
    async stop() {
      if (disposed) return;
      try { frame.contentWindow.postMessage({ emulator: "webemu-azahar", type: "stop", session }, origin); } catch (_) {}
      // Give the core time to flush its browser save before removing the iframe.
      await new Promise(resolve => setTimeout(resolve, 700));
      cleanup();
    },
    fullscreen() {
      return mount.requestFullscreen?.();
    }
  };
}
