#!/usr/bin/env python3
"""Package Web Emu as a single HTML file that loads from file:// without CDNs."""
from pathlib import Path
from base64 import b64encode

root = Path(".")
html = (root / "index.html").read_text(encoding="utf-8")
sdk = (root / "vendor/mgba-sdk-offline.js").read_text(encoding="utf-8")
runtime = (root / "vendor/mgba.js").read_text(encoding="utf-8")
wasm = (root / "vendor/mgba.wasm").read_bytes()
if wasm[:4] != bytes([0,97,115,109]):
    raise RuntimeError("Invalid mGBA WebAssembly binary")

# The generated SDK is bundled as a global IIFE; mGBA classic runtime is inline.
# HTML-safe inline scripts require escaping literal closing tags.
def inline_script(source):
    return '<script>' + chr(10) + source.replace('</script', '<' + chr(92) + '/script') + chr(10) + '</script>' + chr(10)

wasm_url = "data:application/wasm;base64," + b64encode(wasm).decode("ascii")
bootstrap = inline_script("window.__WEB_EMU_OFFLINE__ = {wasmUrl: " + repr(wasm_url) + "};")
bootstrap += inline_script(runtime)
bootstrap += inline_script(sdk)
html = html.replace('<script type="module">', '<script>', 1)
if '<script type="module">' in html:
    raise RuntimeError("Unexpected additional module script; offline bundling incomplete")
if html.count('<script>') < 1:
    raise RuntimeError("Missing launcher script")
html = html.replace('<script>' + chr(10) + 'const BUILD_VERSION=', bootstrap + '<script>' + chr(10) + 'const BUILD_VERSION=', 1)
# Detect variants where the launcher starts directly with the version constant.
if html.count("window.__WEB_EMU_OFFLINE__ = {wasmUrl:") != 1:
    raise RuntimeError("Failed to inject offline runtime")
out = root / "dist-offline"
out.mkdir(exist_ok=True)
(out / "index.html").write_text(html, encoding="utf-8")
print(f"Offline index.html: {(out / 'index.html').stat().st_size:,} bytes")
