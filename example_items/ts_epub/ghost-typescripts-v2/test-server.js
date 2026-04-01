// 简单测试服务器
import { serve } from 'bun';
import { readFile } from 'fs/promises';
import { join, extname } from 'path';

const PORT = 3003;
const OEBPS_DIR = join(process.cwd(), 'OEBPS');

const MIME_TYPES = {
  '.html': 'text/html',
  '.xhtml': 'application/xhtml+xml; charset=UTF-8',
  '.css': 'text/css',
  '.js': 'application/javascript',
  '.json': 'application/json',
};

async function handleRequest(request) {
  const url = new URL(request.url);
  let pathname = url.pathname;
  
  // 移除开头的/OEBPS（如果存在）
  if (pathname.startsWith('/OEBPS')) {
    pathname = pathname.substring('/OEBPS'.length);
  }
  
  // 默认页面
  if (pathname === '/') {
    pathname = '/entrance/index.xhtml';
  }
  
  // 确保路径安全
  if (!pathname.startsWith('/')) {
    pathname = '/' + pathname;
  }
  
  let filePath = join(OEBPS_DIR, pathname);
  
  try {
    const content = await readFile(filePath);
    const ext = extname(filePath).toLowerCase();
    const contentType = MIME_TYPES[ext] || 'text/plain';
    
    return new Response(content, {
      headers: { 'Content-Type': contentType },
    });
  } catch (error) {
    console.error('Error serving file:', filePath, error.message);
    return new Response('File not found', { status: 404 });
  }
}

console.log(`测试服务器运行在 http://localhost:${PORT}`);
console.log('按 Ctrl+C 停止服务器');

serve({
  port: PORT,
  fetch: handleRequest,
});