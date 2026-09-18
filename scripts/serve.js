// Minimal static file server to serve the LifeHub folder locally.
// Usage: node scripts/serve.js [port]
const http = require('http');
const fs = require('fs');
const path = require('path');
const port = process.argv[2] ? parseInt(process.argv[2], 10) : 8080;
const root = process.cwd();

const mime = {
  '.html': 'text/html',
  '.js': 'application/javascript',
  '.css': 'text/css',
  '.json': 'application/json',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.svg': 'image/svg+xml',
  '.txt': 'text/plain'
};

const server = http.createServer((req, res) => {
  try {
    let filePath = path.join(root, decodeURIComponent(req.url.split('?')[0]));
    if (filePath.endsWith(path.sep)) filePath = path.join(filePath, 'dashboard.html');
    fs.stat(filePath, (err, stats) => {
      if (err) {
        res.writeHead(404);
        res.end('Not found');
        return;
      }
      if (stats.isDirectory()) filePath = path.join(filePath, 'dashboard.html');
      const ext = path.extname(filePath).toLowerCase();
      const contentType = mime[ext] || 'application/octet-stream';
      res.writeHead(200, { 'Content-Type': contentType });
      const stream = fs.createReadStream(filePath);
      stream.pipe(res);
    });
  } catch (e) {
    res.writeHead(500);
    res.end('Server error');
  }
});

server.listen(port, () => {
  console.log(`LifeHub static server running at http://127.0.0.1:${port}/ (root: ${root})`);
  console.log('Press Ctrl+C to stop');
});
