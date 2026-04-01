/**
 * 自动更新页面到v4.0的脚本
 * 批量更新HTML文件使用新的幽灵维度设计
 */

import { readdirSync, readFileSync, writeFileSync, statSync } from 'fs';
import { join, extname } from 'path';

// 要处理的目录
const OEBPS_PATH = join(process.cwd(), 'OEBPS');
const STYLES_PATH = join(OEBPS_PATH, 'styles');
const SCRIPTS_PATH = join(OEBPS_PATH, 'scripts');

// v4.0的CSS和JS文件
const V4_CSS = 'ghost-v4.css';
const V4_JS = 'ghost-environment.js';
const QUANTUM_JS = 'quantum-content.js';
const GUIDE_JS = 'ghost-guide.js';

// 更新规则
const UPDATE_RULES = {
  // CSS文件替换
  css: {
    'ghost.css': V4_CSS,
    // emotion.css暂时保留，但可能会在后续更新
  },
  
  // body类名更新（移除预设情绪类）
  bodyClasses: ['curious', 'confused', 'excited', 'frustrated'],
  
  // 要移除的旧幽灵元素
  removeElements: [
    'data-stream',
    'dimension-overlay',
    'ghost-dimension-body',
    'ghost-assistant',
    'emotion-switcher',
    'dimension-switcher-enhanced',
    'shuttle-mode-switcher'
  ],
  
  // 要添加的新脚本
  addScripts: [
    `<script src="/scripts/${V4_JS}"></script>`,
    `<script src="/scripts/${QUANTUM_JS}"></script>`,
    `<script src="/scripts/${GUIDE_JS}"></script>`
  ]
};

// 递归查找所有HTML/XHTML文件
function findHtmlFiles(dir, fileList = []) {
  const files = readdirSync(dir);
  
  for (const file of files) {
    const filePath = join(dir, file);
    const stat = statSync(filePath);
    
    if (stat.isDirectory()) {
      // 跳过node_modules和其他不需要的目录
      if (!file.startsWith('.') && file !== 'node_modules') {
        findHtmlFiles(filePath, fileList);
      }
    } else if (extname(file).toLowerCase() === '.xhtml' || extname(file).toLowerCase() === '.html') {
      fileList.push(filePath);
    }
  }
  
  return fileList;
}

// 更新单个文件
function updateFile(filePath) {
  console.log(`正在更新: ${filePath}`);
  
  try {
    let content = readFileSync(filePath, 'utf8');
    const originalContent = content;
    
    // 1. 更新CSS引用
    for (const [oldCss, newCss] of Object.entries(UPDATE_RULES.css)) {
      const oldLink = `href="styles/${oldCss}"`;
      const newLink = `href="styles/${newCss}"`;
      
      // 替换直接引用
      content = content.replace(new RegExp(oldLink, 'g'), newLink);
      
      // 替换相对路径引用
      const oldLinkRel = `href="/styles/${oldCss}"`;
      const newLinkRel = `href="/styles/${newCss}"`;
      content = content.replace(new RegExp(oldLinkRel, 'g'), newLinkRel);
      
      // 替换../styles/引用
      const oldLinkParent = `href="../styles/${oldCss}"`;
      const newLinkParent = `href="../styles/${newCss}"`;
      content = content.replace(new RegExp(oldLinkParent, 'g'), newLinkParent);
      
      // 通用替换：任意层级的相对路径
      const oldLinkGeneric = new RegExp(`href="(\\.\\.\\/)*styles\\/${oldCss}"`, 'g');
      const newLinkGeneric = `href="$1styles/${newCss}"`;
      content = content.replace(oldLinkGeneric, newLinkGeneric);
    }
    
    // 额外通用替换：捕获任意路径中的ghost.css（包括没有styles/目录的情况）
    const ghostCssRegex = /href="([^"]*?)ghost\.css"/gi;
    content = content.replace(ghostCssRegex, (match, path) => {
      return `href="${path}ghost-v4.css"`;
    });
    
    // 2. 移除body上的预设情绪类
    for (const className of UPDATE_RULES.bodyClasses) {
      const bodyClassRegex = new RegExp(`<body[^>]*class="[^"]*\\b${className}\\b[^"]*"`, 'g');
      content = content.replace(bodyClassRegex, (match) => {
        // 移除特定的类名
        return match.replace(new RegExp(`\\b${className}\\b`, 'g'), '').replace(/\s+/g, ' ').trim();
      });
      
      // 也处理没有引号的情况
      const bodyClassRegex2 = new RegExp(`<body[^>]*class=[^\\s>]*\\b${className}\\b[^\\s>]*`, 'g');
      content = content.replace(bodyClassRegex2, (match) => {
        return match.replace(new RegExp(`\\b${className}\\b`, 'g'), '').replace(/\s+/g, ' ').trim();
      });
    }
    
    // 3. 添加v4.0脚本
    // 检查是否已添加幽灵指南脚本，如果没有则添加所有脚本
    if (!content.includes(GUIDE_JS)) {
      // 在head结束前添加
      const headEndRegex = /<\/head>/i;
      if (headEndRegex.test(content)) {
        const scriptsToAdd = UPDATE_RULES.addScripts.join('\n  ');
        content = content.replace(headEndRegex, `  ${scriptsToAdd}\n</head>`);
      }
    }
    
    // 4. 移除旧的幽灵元素
    for (const element of UPDATE_RULES.removeElements) {
      // 移除整个元素
      const elementRegex = new RegExp(`<[^>]*class="[^"]*\\b${element}\\b[^"]*"[^>]*>.*?</[^>]+>`, 'gis');
      content = content.replace(elementRegex, '');
      
      // 移除空元素
      const emptyElementRegex = new RegExp(`<[^>]*class="[^"]*\\b${element}\\b[^"]*"[^>]*>\\s*</[^>]+>`, 'gis');
      content = content.replace(emptyElementRegex, '');
      
      // 移除自闭合元素
      const selfClosingRegex = new RegExp(`<[^>]*class="[^"]*\\b${element}\\b[^"]*"[^>]*/>`, 'gis');
      content = content.replace(selfClosingRegex, '');
    }
    
    // 5. 更新标题中的版本号
    const titleRegex = /<title>([^<]*)<\/title>/i;
    const match = content.match(titleRegex);
    if (match && !match[1].includes('v4.0') && !match[1].includes('v4')) {
      content = content.replace(titleRegex, `<title>$1 v4.0</title>`);
    }
    
    // 6. 清理多余的空白
    content = content.replace(/\n\s*\n\s*\n/g, '\n\n');
    
    // 只有在内容实际改变时才写入
    if (content !== originalContent) {
      writeFileSync(filePath, content, 'utf8');
      console.log(`  已更新`);
    } else {
      console.log(`  无需更新`);
    }
    
  } catch (error) {
    console.error(`  更新失败: ${error.message}`);
  }
}

// 主函数
function main() {
  console.log('开始批量更新到v4.0...');
  
  // 查找所有HTML文件
  const htmlFiles = findHtmlFiles(OEBPS_PATH);
  console.log(`找到 ${htmlFiles.length} 个HTML/XHTML文件`);
  
  // 更新每个文件
  let updatedCount = 0;
  for (const file of htmlFiles) {
    updateFile(file);
    updatedCount++;
  }
  
  console.log(`\n完成！更新了 ${updatedCount} 个文件`);
  console.log('\n注意事项:');
  console.log('1. 手动检查入口页面和其他关键页面的特殊更新');
  console.log('2. 某些页面可能需要手动调整布局');
  console.log('3. 验证所有链接和资源路径是否正确');
  console.log('4. 测试环境响应系统是否正常工作');
}

// 执行
// if (import.meta.url === `file://${process.argv[1]}`) {
//   main();
// }
main();

export { findHtmlFiles, updateFile };