'use strict';

/**
 * Self-contained, zero-dependency offline HTTP server for Web Emu.
 *
 * Azahar requires cross-origin isolation to use SharedArrayBuffer threads;
 * file:// does not provide the needed HTTP headers. This loopback-only server
 * serves the already-bundled assets without making any Internet connections.
 * The Windows ZIP includes node.exe, so the user does not need to install Node.
 */

const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const { execFile } = require('node:child_process');

const root = path.resolve(__dirname, '..');
const host = '127.0.0.1';
const port = 8765; // Keep fixed: browser battery saves are scoped to this origin.
const url = `http://${host}:${port}/`;

const types = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.mjs': 'text/javascript; charset=utf-8',
  '.cjs': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.wasm': 'application/wasm',
  '.data': 'application/octet-stream',
  '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
  '.gif': 'image/gif', '.svg': 'image/svg+xml', '.webp': 'image/webp',
  '.ico': 'image/x-icon', '.woff': 'font/woff', '.woff2': 'font/woff2',
  '.ttf': 'font/ttf', '.otf': 'font/otf',
  '.txt': 'text/plain; charset=utf-8',
  '.map': 'application/json',
};

function errorPage(response, code, message, isHead = false) {
  response.statusCode = code;
  response.setHeader('Content-Type', 'text/plain; charset=utf-8');
  response.end(isHead ? undefined : message);
}

const server = http.createServer((request, response) => {
  // Required to keep WebAssembly threads available on a local HTTP origin.
  response.setHeader('Cross-Origin-Opener-Policy', 'same-origin');
  response.setHeader('Cross-Origin-Embedder-Policy', 'require-corp');
  response.setHeader('Cross-Origin-Resource-Policy', 'same-origin');
  response.setHeader('X-Content-Type-Options', 'nosniff');
  response.setHeader('Cache-Control', 'no-cache');
  response.setHeader('Referrer-Policy', 'no-referrer');

  if (request.method !== 'GET' && request.method !== 'HEAD') {
    response.setHeader('Allow', 'GET, HEAD');
    return errorPage(response, 405, 'Only GET and HEAD are allowed.');
  }
  const isHead = request.method === 'HEAD';

  let pathname;
  try {
    pathname = decodeURIComponent(new URL(request.url, url).pathname);
    if (!pathname.startsWith('/') || pathname.includes('\\') || pathname.includes('\0')) {
      throw new Error('Invalid path');
    }
  } catch (_) {
    return errorPage(response, 400, 'Invalid URL path', isHead);
  }

  // Static files only; forbid traversal and symlink escapes.
  let target = path.resolve(root, '.' + pathname);
  if (target !== root && !target.startsWith(root + path.sep)) {
    return errorPage(response, 403, 'Forbidden path', isHead);
  }
  try {
    let stat = fs.statSync(target);
    if (stat.isDirectory()) {
      target = path.join(target, 'index.html');
      stat = fs.statSync(target);
    }
    const actual = fs.realpathSync(target);
    if (actual !== root && !actual.startsWith(root + path.sep)) {
      return errorPage(response, 403, 'Forbidden path', isHead);
    }
    if (!stat.isFile()) return errorPage(response, 404, 'Not a file', isHead);
    response.statusCode = 200;
    response.setHeader('Content-Type', types[path.extname(target).toLowerCase()] || 'application/octet-stream');
    response.setHeader('Content-Length', stat.size);
    if (isHead) return response.end();
    const stream = fs.createReadStream(target);
    stream.on('error', error => {
      console.error('File read error:', error.message);
      if (!response.headersSent) errorPage(response, 500, 'File read failed');
      else response.destroy(error);
    });
    stream.pipe(response);
  } catch (error) {
    if (error.code === 'ENOENT' || error.code === 'ENOTDIR') {
      return errorPage(response, 404, 'File not found', isHead);
    }
    console.error('File server error:', error.message);
    return errorPage(response, 500, 'Internal file server error', isHead);
  }
});

server.on('error', error => {
  if (error.code === 'EADDRINUSE') {
    console.error('Web Emu is already using port ' + port + '. Close the other offline Web Emu window, then launch again.');
  } else {
    console.error('Could not start Web Emu:', error.message);
  }
  process.exitCode = 1;
});

server.listen(port, host, () => {
  console.log('=======================================================');
  console.log(' WEB EMU - OFFLINE (32 CONSOLE VARIANTS)');
  console.log('=======================================================');
  console.log('Open in your browser: ' + url);
  console.log('Everything is served from this extracted folder.');
  console.log('No Internet connection, hosting account, or ROM upload needed.');
  console.log('Keep this window open while playing. Close it to stop.');
  console.log('Save important games using the emulator\'s save/export menu.');
  console.log('');

  if (process.env.WEB_EMU_NO_BROWSER === '1') return;
  if (process.platform === 'win32') {
    execFile('rundll32.exe', ['url.dll,FileProtocolHandler', url], { windowsHide: true }, error => {
      if (error) console.log('Open this address manually: ' + url);
    });
  } else {
    console.log('Open the link above in a browser.');
  }
});
process.on('SIGINT', () => server.close());
