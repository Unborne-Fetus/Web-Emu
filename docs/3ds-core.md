# Nintendo 2DS / 3DS browser core integration

Web Emu's 2DS/3DS tab is wired to an **optional** browser core module at `cores/3ds.js`. **No 3DS emulator binary is bundled.** Installing this adapter alone does not enable gameplay.

The module must export `async function create3dsEmulator({ topCanvas, bottomCanvas, rom })`. It receives two HTML canvas elements (400x240, 320x240) and the game's Uint8Array ROM bytes. The function must initialize the emulator, start actual game execution, paint both screens, handle touch input as appropriate, and return an object with an asynchronous `stop()` method to clean up core resources. Additional implementation-specific controls can be added later.

The loader handles `.3ds`, `.cci`, and `.cxi` cartridge images. `.cia` packages are recognized separately, **not installed**. Encrypted ROMs and console system data may require capabilities the eventual core doesn't provide.

## Core selection and limitations

[Azahar](https://github.com/azahar-emu/azahar) is a maintained 3DS emulator for desktop and Android. Its currently documented releases are not a drop-in WebAssembly/browser SDK. Porting Azahar/Citra to the web would require dedicated C++/Emscripten/WebGL work and testing, including CPU emulation, GPU APIs, multithreading, filesystem, audio, and compatible ROM formats. No working 3DS browser core has been verified for this repository.

**Do not put placeholder renderers in `cores/3ds.js` and advertise them as emulation.** Once a real browser engine is built and legally distributable, supply the module and appropriate binaries under `cores/`, respecting its open-source licensing and notices. The GitHub Pages workflow currently publishes that directory unchanged.

Existing GB/GBC/GBA via mGBA is unaffected.
