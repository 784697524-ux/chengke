'use strict';

const fs = require('fs');
const path = require('path');

const PUBLIC_DIR = path.join(__dirname, 'public');
const INDEX_FILE = 'index.html';

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.webp': 'image/webp',
  '.ico': 'image/x-icon'
};

function parseEvent(event) {
  if (!event) return {};
  if (Buffer.isBuffer(event)) return JSON.parse(event.toString());
  if (typeof event === 'string') return JSON.parse(event);
  return event;
}

function getRequestPath(request) {
  const rawPath =
    request.rawPath ||
    request.path ||
    (request.requestContext && request.requestContext.http && request.requestContext.http.path) ||
    '/';

  const cleanPath = rawPath.split('?')[0] || '/';
  if (cleanPath === '/' || cleanPath.endsWith('/')) return INDEX_FILE;
  return decodeURIComponent(cleanPath.replace(/^\/+/, ''));
}

function resolveFile(requestPath) {
  const normalized = path.normalize(requestPath).replace(/^(\.\.[/\\])+/, '');
  const filePath = path.join(PUBLIC_DIR, normalized);
  if (!filePath.startsWith(PUBLIC_DIR)) return null;
  return filePath;
}

exports.handler = async function handler(event) {
  let request;
  try {
    request = parseEvent(event);
  } catch (error) {
    return {
      statusCode: 400,
      headers: { 'Content-Type': 'text/plain; charset=utf-8' },
      body: 'Bad request',
      isBase64Encoded: false
    };
  }

  const filePath = resolveFile(getRequestPath(request));
  const targetPath = filePath && fs.existsSync(filePath) && fs.statSync(filePath).isFile()
    ? filePath
    : path.join(PUBLIC_DIR, INDEX_FILE);

  const ext = path.extname(targetPath).toLowerCase();
  const isText = ['.html', '.js', '.json', '.css', '.svg'].includes(ext);
  const body = fs.readFileSync(targetPath);

  return {
    statusCode: filePath && targetPath === filePath ? 200 : 200,
    headers: {
      'Content-Type': MIME[ext] || 'application/octet-stream',
      'Cache-Control': isText ? 'no-cache' : 'public, max-age=3600'
    },
    body: isText ? body.toString('utf8') : body.toString('base64'),
    isBase64Encoded: !isText
  };
};
