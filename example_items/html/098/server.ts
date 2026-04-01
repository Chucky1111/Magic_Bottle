import { serve } from 'bun';
import { resolve, join, extname } from 'path';
import { readFileSync, existsSync } from 'fs';

const port = 3001;
const publicDir = process.cwd();

// MIME类型映射
const mimeTypes: Record<string, string> = {
  '.html': 'text/html',
  '.css': 'text/css',
  '.js': 'application/javascript',
  '.ts': 'application/javascript', // TypeScript文件编译后作为JS发送
  '.json': 'application/json',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.gif': 'image/gif',
  '.svg': 'image/svg+xml',
};

// 编译TypeScript文件
async function compileTypeScript(filePath: string): Promise<string> {
  try {
    // 使用Bun的转译器编译TypeScript
    const result = await Bun.build({
      entrypoints: [filePath],
      target: 'browser',
      minify: false,
      sourcemap: 'none',
    });
    
    if (result.success && result.outputs.length > 0) {
      const output = result.outputs[0];
      if (output) {
        return await output.text();
      }
    } else {
      console.error('编译失败:', result.logs);
      return `console.error('TypeScript编译失败');`;
    }
  } catch (error) {
    console.error('编译错误:', error);
    return `console.error('编译错误: ${error}');`;
  }
  
  // 默认返回空模块
  return 'export {};';
}

// 处理请求
async function handleRequest(request: Request): Promise<Response> {
  const url = new URL(request.url);
  let filePath = url.pathname;
  
  // 默认页面
  if (filePath === '/') {
    filePath = '/index.html';
  }
  
  // 解析实际文件路径
  const fullPath = resolve(join(publicDir, filePath.substring(1)));
  
  // 安全检查：确保文件在publicDir内
  if (!fullPath.startsWith(publicDir)) {
    return new Response('禁止访问', { status: 403 });
  }
  
  // 检查文件是否存在
  if (!existsSync(fullPath)) {
    return new Response('文件未找到', { status: 404 });
  }
  
  // 获取文件扩展名
  const ext = extname(fullPath);
  const contentType = mimeTypes[ext] || 'application/octet-stream';
  
  try {
    // 处理TypeScript文件：编译后返回
    if (ext === '.ts') {
      const compiled = await compileTypeScript(fullPath);
      return new Response(compiled, {
        status: 200,
        headers: { 'Content-Type': 'application/javascript' },
      });
    }
    
    // 处理其他静态文件
    const fileContent = readFileSync(fullPath);
    return new Response(fileContent, {
      status: 200,
      headers: { 'Content-Type': contentType },
    });
  } catch (error) {
    console.error('文件读取错误:', error);
    return new Response('服务器错误', { status: 500 });
  }
}

console.log(`🚀 服务器运行在 http://localhost:${port}`);
console.log(`📁 服务目录: ${publicDir}`);

serve({
  port,
  fetch: handleRequest,
});