# Web Emu

**Web Emu** is a browser-based emulator for Game Boy, Game Boy Color, Game Boy Advance, and an experimental browser version of Nintendo 2DS / 3DS emulation using Azahar through EmulatorJS.

**Offline 2DS/3DS support is available as a separate, complete Windows ZIP build.** Azahar needs threaded WebAssembly, cross-origin isolation and WebGL 2, so Windows runs a localhost-only web server automatically when you double-click the launcher. It works without an Internet connection after you download and extract the package. Standalone `file://` HTML cannot provide these features.

> **Development status: early alpha.** The interface and mGBA integration are under development. ROM boot, audio, and save persistence have **not yet passed end-to-end testing**. Do not treat the current build as reliable for important saves.

## Play completely offline on Windows (GB, GBC, GBA, 2DS, 3DS)

1. Open [Actions → Deploy Web Emu](https://github.com/Unborne-Fetus/Web-Emu/actions/workflows/pages.yml), select a **successful** run, and download **Web-Emu-Offline-All-Systems** from the artifacts.
2. **Extract the entire ZIP** to a folder, not just the launcher.
3. Double-click **`Start-Web-Emu.cmd`**. The included Node Windows runtime starts a local browser service and opens **http://127.0.0.1:8765/**.
4. Open the **2DS / 3DS** tab for a compatible `.3ds`, `.cci`, or `.cxi` game, or use the **GB / GBC / GBA** tab.
5. Keep the launcher window open while playing. Closing it stops the local server. **You can disconnect from the Internet and keep playing.**

**No installer, npm, Python, GitHub Pages, separate Node download, or Internet connection is required after extracting the completed ZIP.** No games or proprietary Nintendo keys/firmware are included. Use game images you are authorized to use.

The command window is intentional, not an error: it runs a small web server **bound only to your own computer (127.0.0.1)**. The local server sends COOP/COEP security headers so Azahar can use `SharedArrayBuffer` without a website. This does not publish anything to the Internet.

**Your save data:** browser storage is tied to the address **127.0.0.1:8765** and the browser profile. Keep the same browser and launcher port for saved games to reappear. Export your saves from the emulator's menu for backups; deleting browser site data can delete saves. Azahar browser save functionality is still experimental and has not been verified for every game.

**Limitations:** this offline Windows bundle is a **folder**, not a single `index.html`; it must keep its files together. It is intended for Windows 10/11 x64 and a WebGL 2-capable Chrome/Edge browser. Direct `.cia` installation and encrypted game images are not supported by this launcher. Real 3DS gameplay and battery-save restoration require additional end-to-end verification.

## Interface

The player screen is intentionally minimal:

- **Upper-left:** fullscreen button
- **Upper-right:** settings (pause/resume, reset, pixel filtering, states, screenshots, and opening another game)
- **Center of the empty screen:** **Open file**; you can also drag a `.gba` file onto the display
- **Bottom-left:** speed bar (currently locked to 1× until fast-forward is implemented)
- **Bottom-right:** volume slider
- **Touch controls:** on touch-capable devices
- **Keyboard:** arrow keys = D-pad, X = A, Z = B, A = L, S = R, Enter = Start, Right Shift = Select

Gamepads are intended to be supported through the emulator core.

## Play a game

1. Download the repository's `index.html`.
2. Double-click the file in a modern browser.
3. Choose **Open file** and select a GBA ROM you are authorized to use.

**At present, the default single-file launcher needs an internet connection** to download the mGBA browser runtime. The launcher does not intentionally upload your ROM. Loading the game into your browser is not the same as sending it to our server.

### Saving your game

Use the game's regular in-game **Save** option. The mGBA wrapper can persist battery-backed saves to browser storage (OPFS) when available. That storage is scoped to a particular browser origin and can be deleted when site data is cleared. **`file://` pages may not have dependable persistent storage**, even if the page opens successfully. Autosaving therefore remains **experimental** until tested in supported browsers.

Save states are separate from the game's battery save. Export any important save-state backup, and avoid relying on unverified automatic persistence.

## Nintendo 2DS / 3DS (Azahar browser runtime)

The **2DS / 3DS** tab (both hosted and offline Windows) uses the actual [Azahar](https://github.com/azahar-emu/azahar) emulator port bundled through [EmulatorJS](https://github.com/EmulatorJS/EmulatorJS). This is a **nightly, experimental threaded WASM core**, not a mock display. It is built into the **GitHub Pages deployment** by `.github/workflows/pages.yml` and intentionally not embedded in the one-file offline download.

- Open either the **hosted GitHub Pages site** through HTTPS **or the offline Windows package's localhost URL**, then choose **2DS / 3DS**.
- Select your own compatible **`.3ds`, `.cci` or `.cxi`** game image.
- Azahar loads inside its own iframe and provides its dual-screen layout, lower-screen touch input, controller mapping, and emulation menu.
- ROM data is handled locally in the browser; there is no ROM upload endpoint. EmulatorJS stores supported saves in the browser's own storage; back up important game progress with its export options.
- **`.cia` installer packages aren't supported** by this direct-ROM launcher. Files that require decryption will not launch as-is.
- Azahar requires `crossOriginIsolated === true`, `SharedArrayBuffer`, and **WebGL 2**. The bundled [coi-serviceworker](https://github.com/gzuidhof/coi-serviceworker) supplies COOP/COEP headers on GitHub Pages; the first hosted page load may reload once. The offline launcher supplies equivalent headers through its Node-based localhost server. A regular local server without those headers is insufficient.
- 3DS is **included in the complete offline Windows ZIP**, but not the old standalone offline index. Devices with little RAM, low WebGL support, or older mobile browsers may not work. Game compatibility and save persistence are **not yet verified end to end**.

**How the deploy works:** the Pages workflow downloads matching EmulatorJS nightly `loader.js`, frontend JS/CSS, archive helpers, and `azahar-thread-wasm.data` into `vendor/emulatorjs/data/`, checks their existence, and deploys them on the same origin as the website. No commercial games, official firmware, keys, or Nintendo BIOS data are bundled.

**Diagnostics:** if the 3DS tab reports missing WebAssembly core files, check the **Bundle threaded Azahar core** step in the latest [Deploy Web Emu](https://github.com/Unborne-Fetus/Web-Emu/actions/workflows/pages.yml) workflow. If it reports SharedArrayBuffer, use the HTTPS site and reload; if it reports WebGL 2, enable browser hardware acceleration or use supported hardware. Azahar's embedded UI controls saving and in-game settings.

## Experimental standalone offline build

GitHub Actions now attempts to generate **Web-Emu-Offline**, containing one `index.html` with mGBA JavaScript and WebAssembly embedded. This file is designed to be **double-clicked without an internet connection or local web server**.

To get it, open the repository's **Actions → Deploy Web Emu** workflow, select a successful run, and download the **Web-Emu-Offline** artifact. Extract the ZIP and double-click its `index.html`. Do not use the root repository `index.html` for offline testing; that source launcher can still depend on CDN files.

The offline build uses a compatibility audio path when browsers block AudioWorklets on `file://`. That path uses the legacy ScriptProcessor API, which is not guaranteed on every future browser. **This distribution is experimental: real GBA ROM boot, sound, speed switching, and battery-save restoration have not been verified across browsers.** Browser storage on local files is inconsistent. Export a `.sav` backup before closing important sessions.

If the offline artifact is missing, inspect the "Build standalone offline index" Actions step for its error; a successful website deployment does not guarantee the optional offline build succeeded.

## Offline roadmap

The project is moving toward two distribution formats:

| Format | Intended result | Status |
| --- | --- | --- |
| **Single `index.html` (GB/GBC/GBA only)** | Embedded mGBA, double-click offline | **Experimental Actions artifact; not boot-verified** |
| **Offline Windows folder (GB/GBC/GBA/3DS)** | Bundled Azahar + mGBA files and local runtime; double-click `Start-Web-Emu.cmd` | **Built by GitHub Actions; game boot not yet verified** |
| Hosted website | Open through HTTPS, with persistent browser storage where supported | **Early alpha** |

The launcher now checks for **`vendor/mgba-sdk.js`** and, when available, uses it together with **`vendor/mgba.js`** and **`vendor/mgba.wasm`**. If the local SDK is missing, it falls back to the pinned public CDN. These files must be a compatible, properly bundled release of the mGBA wrapper; copying arbitrary JavaScript or WASM files into `vendor/` will not work.

A true **one-file offline build** needs the browser SDK and WASM packaged into that HTML and verified from a `file://` page. A normal ES-module build is not sufficient by itself. We will also need to handle any generated module workers and audio worklets safely.

### Offline acceptance checklist

- [ ] Launch with no network connection
- [ ] Double-click `index.html` (no web server)
- [ ] Load and play a test `.gba` ROM
- [ ] Render graphics and produce audio
- [ ] Confirm controls, volume, and fullscreen
- [ ] Save in-game, close the browser, relaunch, and load the same ROM
- [ ] Confirm a supported backup/export option for local-file users
- [ ] Test on current Chrome, Edge, and Firefox
- [ ] Remove all CDN dependencies from the offline distribution

## Technology

- **Frontend:** HTML, CSS, vanilla JavaScript
- **GBA emulation:** [mGBA](https://github.com/mgba-emu/mgba), through [@wasm-gaming/mgba-wasm](https://github.com/wasm-gaming/mGBA-wasm) (pinned to 0.1.1 while integration is validated)
- **Display:** HTML Canvas, native GBA resolution of **240 × 160**
- **Audio:** browser audio interfaces provided by the emulator wrapper
- **Persistence:** Origin Private File System (OPFS) where supported

The mGBA wrapper can run GBA games without a supplied official BIOS using its built-in replacement. A few titles can have special requirements.

## Development priorities

1. Verify ROM loading, controls, rendering, sound, and core lifecycle.
2. Vendor all runtime files and demonstrate fully offline execution.
3. Package the runtime into a self-contained HTML download, if browser security restrictions permit.
4. Test and strengthen save persistence and provide portable backup/export.
5. Enable speed controls, refine touchscreen/gamepad support, and perform cross-browser testing.
6. Verify Azahar 3DS ROM boot, touch controls, audio, frame rate and saves on **both** the hosted site and offline Windows ZIP.

## Legal and credits

Web Emu does **not** distribute commercial ROMs, Nintendo firmware, keys or BIOS files. Use ROMs you have the rights to use.

GB/GBC/GBA emulation uses [mGBA](https://github.com/mgba-emu/mgba) and the [wasm-gaming mGBA browser wrapper](https://github.com/wasm-gaming/mGBA-wasm), licensed under **MPL-2.0**. 2DS/3DS emulation uses **Azahar through EmulatorJS**, which include **GPL-3.0-licensed components**; the Pages build includes the EmulatorJS GPL license file and the upstream project links provide source code. The [coi-serviceworker](https://github.com/gzuidhof/coi-serviceworker) is MIT licensed; its notice is in `licenses/`. Redistributors must comply with all applicable component licenses.

This project is independent of Nintendo and is not affiliated with or endorsed by Nintendo.
