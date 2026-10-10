// Shared EmulatorJS adapter for nine offline retro console families.
// ROMs stay on the user's device. The matching libretro WASM core is local.
const runtimeRoot = new URL("../vendor/emulatorjs/data/", import.meta.url);
const playerUrl = new URL("./retro-player.html", import.meta.url);
export const SYSTEMS = Object.freeze({
  nds: { label: "Nintendo DS", core: "desmume", extensions: ["nds"] },
  nes: { label: "NES", core: "fceumm", extensions: ["nes"] },
  snes: { label: "SNES", core: "snes9x", extensions: ["sfc", "smc"] },
  n64: { label: "Nintendo 64", core: "mupen64plus_next", extensions: ["n64", "z64", "v64"] },
  segaMD: { label: "Sega Genesis", core: "genesis_plus_gx", extensions: ["md", "gen", "bin"] },
  segaGG: { label: "Game Gear", core: "genesis_plus_gx", extensions: ["gg"] },
  segaMS: { label: "Sega Master System", core: "genesis_plus_gx", extensions: ["sms"] },
  atari2600: { label: "Atari 2600", core: "stella2014", extensions: ["a26"] },
  vb: { label: "Virtual Boy", core: "beetle_vb", extensions: ["vb"] }
});

export async function checkRetroAvailability(system) {
  const config = SYSTEMS[system];
  if (!config) throw new Error("Unsupported console.");
  if (location.protocol === "file:") throw new Error("Launch the complete offline package using Start-Web-Emu.cmd, or open the hosted site.");
  const files = ["loader.js", "emulator.min.js", "emulator.min.css", "cores/" + config.core + "-wasm.data"];
  for (const path of files) {
    const response = await fetch(new URL(path, runtimeRoot), { method: "HEAD" });
    if (!response.ok) throw new Error("Missing bundled " + config.label + " file: " + path);
  }
  return true;
}

export async function createRetroEmulator({ mount, system, file, onStatus = () => {} }) {
  const config = SYSTEMS[system];
  if (!config) throw new Error("Unsupported console.");
  if (!(file instanceof File) || !config.extensions.some(ext => file.name.toLowerCase().endsWith("." + ext)) || !file.size) {
    throw new Error("Choose a nonempty " + config.label + " game file (" + config.extensions.map(ext => "." + ext).join(", ") + ").");
  }
  await checkRetroAvailability(system);
  const frame = document.createElement("iframe");
  frame.className = "three-ds-frame";
  frame.title = config.label + " emulator";
  frame.allow = "fullscreen; gamepad";
  frame.setAttribute("allowfullscreen", "");
  frame.src = playerUrl.href;
  const session = "retro-" + crypto.randomUUID();
  const origin = location.origin;
  let disposed = false;
  let ready = false;
  let resolveStart, rejectStart;
  const startup = new Promise((resolve, reject) => { resolveStart = resolve; rejectStart = reject; });
  const timeout = setTimeout(() => fail(new Error(config.label + " emulator startup timed out.")), 90000);
  function cleanup() {
    if (disposed) return;
    disposed = true;
    clearTimeout(timeout);
    window.removeEventListener("message", onMessage);
    frame.remove();
    mount.hidden = true;
  }
  function fail(error) {
    if (disposed) return;
    if (!ready) rejectStart(error);
    else onStatus(error.message);
    cleanup();
  }
  function onMessage(event) {
    if (event.source !== frame.contentWindow || event.origin !== origin) return;
    const msg = event.data;
    if (!msg || msg.emulator !== "webemu-retro" || msg.session !== session) return;
    if (msg.type === "ready") {
      ready = true;
      clearTimeout(timeout);
      onStatus(config.label + " ready. Use the emulator's Play button if needed.");
      resolveStart();
    } else if (msg.type === "playing") {
      onStatus("Playing " + file.name + " · " + config.label);
    } else if (msg.type === "error") {
      fail(new Error(String(msg.message || "Emulator error")));
    } else if (msg.type === "status") {
      onStatus(String(msg.message || ""));
    }
  }
  window.addEventListener("message", onMessage);
  frame.addEventListener("load", () => {
    if (!disposed) frame.contentWindow.postMessage({ emulator: "webemu-retro", type: "start", session, system, file }, origin);
  }, { once: true });
  frame.addEventListener("error", () => fail(new Error("Failed to load the bundled player.")), { once: true });
  mount.replaceChildren(frame);
  mount.hidden = false;
  try { await startup; } catch (error) { cleanup(); throw error; }
  return {
    async stop() {
      if (disposed) return;
      try { frame.contentWindow.postMessage({ emulator: "webemu-retro", type: "stop", session }, origin); } catch (_) {}
      await new Promise(resolve => setTimeout(resolve, 700));
      cleanup();
    },
    fullscreen() { return mount.requestFullscreen?.(); }
  };
}
