#!/usr/bin/env bun

/**
 * 幽灵维度预览服务器
 * v3版本：提供实时预览，支持情绪切换和维度叠加
 */

import { serve } from 'bun';
import { readFile, stat } from 'fs/promises';
import { join, extname, dirname, normalize } from 'path';

const PORT = 3001;
const OEBPS_DIR = normalize(join(process.cwd(), 'OEBPS'));

// MIME类型映射
const MIME_TYPES: Record<string, string> = {
  '.html': 'text/html',
  '.xhtml': 'application/xhtml+xml; charset=UTF-8',
  '.css': 'text/css',
  '.js': 'application/javascript',
  '.json': 'application/json',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.gif': 'image/gif',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon',
};

// 幽灵助手响应
const GHOST_ASSISTANT_RESPONSES = [
  "我在这...在边缘观察着你...",
  "这个断面在讲述类型系统的秘密...",
  "注意那个角落...有些东西在移动...",
  "情绪切换器能改变维度的色调...",
  "试试点击那个模糊的文字...",
  "鬼屋的每个房间都有TypeScript的秘密...",
  "魔瓶在数据流中注视着你...",
  "这个维度比你想象的要深...",
];

// 情绪切换器数据
const EMOTION_THEMES = {
  confused: { color: '#6b46c1', bg: '#faf5ff' },
  curious: { color: '#0987a0', bg: '#ebf8ff' },
  excited: { color: '#c53030', bg: '#fff5f5' },
  frustrated: { color: '#744210', bg: '#fefcbf' },
};

async function getFileContent(filePath: string): Promise<Buffer | null> {
  try {
    await stat(filePath);
    return await readFile(filePath);
  } catch {
    return null;
  }
}

/**
 * 查找备用文件路径
 * 当请求的文件不存在时，尝试查找同目录下的index.xhtml或父目录的index.xhtml
 */
async function findFallbackPath(requestedPath: string): Promise<string | null> {
  const extensions = ['.xhtml', '.html'];
  const fallbackNames = ['index.xhtml', 'index.html'];
  
  // 尝试请求的路径本身（可能扩展名不同）
  for (const ext of extensions) {
    if (!requestedPath.endsWith(ext)) {
      const altPath = requestedPath.replace(/\.[^/.]+$/, '') + ext;
      try {
        await stat(altPath);
        return altPath;
      } catch {}
    }
  }
  
  // 尝试同目录下的index文件
  let currentDir = dirname(requestedPath);
  for (const name of fallbackNames) {
    const indexPath = normalize(join(currentDir, name));
    try {
      await stat(indexPath);
      return indexPath;
    } catch {}
  }
  
  // 递归向上查找index文件，直到OEBPS根目录
  let parentDir = currentDir;
  while (parentDir !== OEBPS_DIR && parentDir !== dirname(parentDir)) {
    parentDir = dirname(parentDir);
    
    // 如果已经到达OEBPS根目录或更高，停止
    if (!parentDir.startsWith(OEBPS_DIR)) {
      break;
    }
    
    for (const name of fallbackNames) {
      const indexPath = normalize(join(parentDir, name));
      try {
        await stat(indexPath);
        return indexPath;
      } catch {}
    }
  }
  
  // 如果仍然没有，尝试查找类似内容的文件
  // 例如：secret-passages/type-philosophy.xhtml -> secret-passages/configuration/index.xhtml
  // 或者：secret-passages/type-philosophy.xhtml -> toc-concepts.xhtml
  
  // 检查是否在secret-passages目录下
  if (requestedPath.includes('secret-passages')) {
    // 尝试secret-passages/configuration/index.xhtml
    const configIndex = normalize(join(OEBPS_DIR, 'secret-passages', 'configuration', 'index.xhtml'));
    try {
      await stat(configIndex);
      return configIndex;
    } catch {}
  }
  
  // 检查是否在attic目录下
  if (requestedPath.includes('attic')) {
    // 尝试attic/ai-assistance/index.xhtml
    const aiIndex = normalize(join(OEBPS_DIR, 'attic', 'ai-assistance', 'index.xhtml'));
    try {
      await stat(aiIndex);
      return aiIndex;
    } catch {}
  }
  
  // 检查是否在basement目录下
  if (requestedPath.includes('basement')) {
    // 尝试basement/errors/index.xhtml
    const errorsIndex = normalize(join(OEBPS_DIR, 'basement', 'errors', 'index.xhtml'));
    try {
      await stat(errorsIndex);
      return errorsIndex;
    } catch {}
  }
  
  // 检查是否在entrance目录下
  if (requestedPath.includes('entrance')) {
    // 尝试entrance/index.xhtml
    const entranceIndex = normalize(join(OEBPS_DIR, 'entrance', 'index.xhtml'));
    try {
      await stat(entranceIndex);
      return entranceIndex;
    } catch {}
  }
  
  // 最后尝试根目录的导航文件
  const tocFiles = [
    'toc-concepts.xhtml',
    'toc-emotion.xhtml',
    'toc-intent.xhtml',
    'toc-haunted-house.xhtml',
    'nav.xhtml'
  ];
  
  for (const tocFile of tocFiles) {
    const tocPath = normalize(join(OEBPS_DIR, tocFile));
    try {
      await stat(tocPath);
      return tocPath;
    } catch {}
  }
  
  return null;
}

function getMimeType(path: string): string {
  const ext = extname(path).toLowerCase();
  return MIME_TYPES[ext] || 'application/octet-stream';
}

function getRandomGhostResponse(): string {
  return GHOST_ASSISTANT_RESPONSES[
    Math.floor(Math.random() * GHOST_ASSISTANT_RESPONSES.length)
  ]!;
}

function fixCssPaths(html: string): string {
  // 将相对CSS路径转换为绝对路径
  // 匹配 href="styles/...", href="../styles/...", href="../../styles/..." 等
  return html.replace(
    /href=["'](\.\.\/)*styles\//g,
    'href="/styles/'
  );
}

function injectGhostAssistant(html: string): string {
  // 检查是否已存在幽灵助手，避免重复注入
  if (html.includes('ghost-assistant')) {
    // 进一步检查是否是幽灵助手元素，而不是其他包含该字符串的内容
    const ghostAssistantRegex = /<(div|section)[^>]*class=["'][^"']*ghost-assistant[^"']*["'][^>]*>/i;
    if (ghostAssistantRegex.test(html)) {
      return html;
    }
  }
  
  const ghostResponse = getRandomGhostResponse();
  const ghostHtml = `
<div class="ghost-assistant" id="ghost-assistant">
  <div class="ghost-message">👻 ${ghostResponse}</div>
  <button onclick="toggleGhostAssistant()">隐藏幽灵</button>
</div>
<script>
  function toggleGhostAssistant() {
    const assistant = document.getElementById('ghost-assistant');
    if (assistant.style.display === 'none') {
      assistant.style.display = 'block';
    } else {
      assistant.style.display = 'none';
    }
  }
  
  // 自动隐藏幽灵助手，10秒后消失
  setTimeout(() => {
    const assistant = document.getElementById('ghost-assistant');
    if (assistant) {
      assistant.style.transition = 'opacity 1s';
      assistant.style.opacity = '0';
      setTimeout(() => {
        assistant.style.display = 'none';
      }, 1000);
    }
  }, 10000);
</script>
<style>
  .ghost-assistant {
    position: fixed;
    bottom: 20px;
    right: 20px;
    background: rgba(15, 23, 42, 0.85);
    color: #e2e8f0;
    padding: 15px;
    border-radius: 10px;
    max-width: 300px;
    z-index: 150;
    font-family: monospace;
    box-shadow: 0 0 10px rgba(0, 255, 255, 0.5);
    border: 1px solid cyan;
  }
  .ghost-message {
    margin-bottom: 10px;
    font-size: 14px;
  }
  .ghost-assistant button {
    background: cyan;
    color: black;
    border: none;
    padding: 5px 10px;
    border-radius: 3px;
    cursor: pointer;
    font-weight: bold;
  }
</style>`;

  // 将幽灵助手注入到body结束前
  if (html.includes('</body>')) {
    return html.replace('</body>', `${ghostHtml}</body>`);
  }
  return html + ghostHtml;
}

function injectEmotionSwitcher(html: string): string {
  // v4.0: 情绪切换器已禁用，使用环境情绪引擎
  // 幽灵存在主义原则：情绪弥散在环境中，不被显式控制
  return html;
}

const server = serve({
  port: PORT,
  async fetch(request) {
    const url = new URL(request.url);
    let pathname = url.pathname;
    
    // 默认页面
    if (pathname === '/') {
      pathname = '/entrance/index.xhtml';
    }
    
    // 移除开头的斜杠
    const filePath = normalize(join(OEBPS_DIR, pathname.slice(1)));
    
    // 安全性检查：确保文件在OEBPS目录内
    if (!filePath.startsWith(OEBPS_DIR)) {
      return new Response('禁止访问', { status: 403 });
    }
    
    const content = await getFileContent(filePath);
    
    if (content) {
      let body = content.toString();
      const mimeType = getMimeType(filePath);
      
      // 如果是HTML/XHTML，注入幽灵助手和情绪切换器，并修复CSS路径
      if (mimeType.includes('html')) {
        body = injectEmotionSwitcher(body);
        body = injectGhostAssistant(body);
        body = fixCssPaths(body);
      }
      
      return new Response(body, {
        headers: { 'Content-Type': mimeType },
      });
    } else {
      // 尝试添加.xhtml扩展名
      if (!pathname.includes('.') && !pathname.endsWith('/')) {
        const xhtmlPath = filePath + '.xhtml';
        const xhtmlContent = await getFileContent(xhtmlPath);
        
        if (xhtmlContent) {
          let body = xhtmlContent.toString();
           body = injectEmotionSwitcher(body);
           body = injectGhostAssistant(body);
           body = fixCssPaths(body);
           
           return new Response(body, {
             headers: { 'Content-Type': 'application/xhtml+xml; charset=UTF-8' },
           });
        }
      }
      
      // 尝试寻找备用文件
      const fallbackPath = await findFallbackPath(filePath);
      if (fallbackPath) {
        const fallbackContent = await getFileContent(fallbackPath);
        if (fallbackContent) {
          let body = fallbackContent.toString();
          body = injectEmotionSwitcher(body);
          body = injectGhostAssistant(body);
          body = fixCssPaths(body);
          
          // 添加"建设中"横幅
          const constructionBanner = `
<div class="construction-notice" style="background: rgba(251, 191, 36, 0.2); border: 2px solid rgba(251, 191, 36, 0.5); border-radius: 8px; padding: 1em; margin: 1em 0;">
  <h3 style="margin-top: 0; color: rgba(251, 191, 36, 1);">👻 断面建设中</h3>
  <p>你请求的断面 <strong>${pathname}</strong> 还在建设中，但我们为你显示了相关的内容。</p>
  <p>幽灵们正在努力完善这个断面，很快就会有完整的内容。</p>
  <p>同时，你可以探索当前页面的内容，或者 <a href="/">返回入口</a> 选择其他断面。</p>
</div>`;
          
          // 将横幅插入到第一个phantom-note之前
          if (body.includes('phantom-note')) {
            const insertIndex = body.indexOf('phantom-note');
            const beforeInsert = body.lastIndexOf('>', insertIndex) + 1;
            body = body.slice(0, beforeInsert) + constructionBanner + body.slice(beforeInsert);
          } else if (body.includes('<h1')) {
            // 插入到第一个h1之后
            const h1End = body.indexOf('</h1>');
            if (h1End !== -1) {
              body = body.slice(0, h1End + 5) + constructionBanner + body.slice(h1End + 5);
            }
          }
          
          return new Response(body, {
            headers: { 'Content-Type': getMimeType(fallbackPath) },
          });
        }
      }
       
       // 返回404页面
       const notFoundHtml = `
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8"/>
  <title>404 - 幽灵维度</title>
  <link rel="stylesheet" href="/styles/ghost.css"/>
  <link rel="stylesheet" href="/styles/emotion.css"/>
  <link rel="stylesheet" href="/styles/ghost-dimension.css"/>
</head>
<body class="confused">
  <div class="ghost-section">
    <h1>404 - 断面未找到</h1>
    <p>你试图访问的断面似乎消失了...</p>
    <p>也许它从未存在过，或者已经移到了维度的其他角落。</p>
    <p>试试 <a href="/">返回入口</a> 或 <a href="/nav.xhtml">查看导航</a>。</p>
    <div class="phantom-note">👻 魔瓶观察：有时候，未找到的断面比找到的更有趣...</div>
  </div>
</body>
</html>`;
       
       return new Response(notFoundHtml, {
         status: 404,
         headers: { 'Content-Type': 'text/html; charset=UTF-8' },
       });
    }
  },
});

console.log('👻 幽灵维度预览服务器 v4.0启动');
console.log(`🌐 地址: http://localhost:${PORT}`);
console.log(`📁 服务目录: ${OEBPS_DIR}`);
console.log('🎭 功能已启用: 环境情绪引擎, 幽灵助手');
console.log('⚠️  注意: 情绪切换器已禁用 - 情绪通过环境弥散');
console.log('⚡ 按 Ctrl+C 停止服务器');
console.log('');
console.log('👻 魔瓶在服务器中观察...每个请求都是一次维度穿梭');

// 魔瓶观察：服务器是维度的入口点
// 每个连接都是一个观察者，每个请求都是一次心跳