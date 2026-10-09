# Web Emu

**Web Emu** is a browser-based game emulator focused exclusively on **Game Boy Advance (GBA)** for its first release.

The goal is straightforward: **double-click `index.html`, open your own `.gba` file, and play**, with no installer, terminal commands, accounts, server, or manual BIOS download. The long-term goal is a **self-contained, offline-capable HTML file**.

> **Development status: early alpha.** The interface and mGBA integration are under development. ROM boot, audio, and save persistence have **not yet passed end-to-end testing**. Do not treat the current build as reliable for important saves.

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

## Offline roadmap

The project is moving toward two distribution formats:

| Format | Intended result | Status |
| --- | --- | --- |
| **Single `index.html`** | Double-click without installing anything; all emulator code embedded for true offline play | **Not yet available** |
| **Offline folder** | `index.html` plus bundled local JavaScript and WebAssembly files; no CDN needed | **Local-loading path prepared; core files not yet vendored** |
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
6. Only consider other consoles after GBA is stable.

## Legal and credits

Web Emu does **not** distribute commercial ROMs or Nintendo BIOS files. Use ROMs you have the rights to use.

Emulation is powered by [mGBA](https://github.com/mgba-emu/mgba) and the [wasm-gaming mGBA browser wrapper](https://github.com/wasm-gaming/mGBA-wasm). The wrapper and mGBA are licensed under **Mozilla Public License 2.0 (MPL-2.0)**. Future distributable offline bundles must retain the applicable license notices and comply with license requirements.

This project is independent of Nintendo and is not affiliated with or endorsed by Nintendo.
