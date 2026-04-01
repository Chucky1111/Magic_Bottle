/**
 * 修复脚本标签问题：移除孤立的</script>标签，清理旧CSS
 */

import { readdirSync, readFileSync, writeFileSync, statSync } from 'fs';
import { join, extname } from 'path';

const OEBPS_PATH = join(process.cwd(), 'OEBPS');

// 要移除的旧CSS文件
const OLD_CSS_FILES = [
  'emotion.css',
  'ghost-dimension.css',
  'ghost.css'  // 如果有的话
];

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

// 修复单个文件
function fixFile(filePath) {
  console.log(`修复: ${filePath}`);
  
  try {
    let content = readFileSync(filePath, 'utf8');
    const originalContent = content;
    
    // 1. 移除孤立的</script>标签（前面没有对应的<script>）
    // 匹配孤立的</script>标签（不在完整的<script>...</script>内）
    content = content.replace(/^\s*<\/script>\s*$/gm, '');
    
    // 2. 移除完整的重复脚本标签（包括内容）
    const scripts = ['ghost-environment.js', 'quantum-content.js', 'ghost-guide.js'];
    scripts.forEach(script => {
      const scriptRegex = new RegExp(`(<script[^>]*src="[^"]*${script}"[^>]*>\\s*</script>\\s*)`, 'gi');
      const matches = content.match(scriptRegex);
      if (matches && matches.length > 1) {
        // 保留第一个，移除后面的
        const firstMatch = matches[0];
        let foundFirst = false;
        
        content = content.replace(scriptRegex, (match) => {
          if (!foundFirst) {
            foundFirst = true;
            return match;
          }
          return '';
        });
        console.log(`  → 修复重复的 ${script} 标签`);
      }
    });
    
    // 3. 移除旧CSS文件引用
    OLD_CSS_FILES.forEach(cssFile => {
      const cssRegex = new RegExp(`<link[^>]*href="[^"]*${cssFile}"[^>]*>`, 'gi');
      if (cssRegex.test(content)) {
        content = content.replace(cssRegex, '');
        console.log(`  → 移除 ${cssFile} 引用`);
      }
    });
    
    // 4. 确保有ghost-v4.css引用
    const v4CssRegex = /<link[^>]*href="[^"]*ghost-v4\.css"[^>]*>/i;
    if (!v4CssRegex.test(content)) {
      // 如果没有，在title后添加
      const titleRegex = /(<title>[^<]*<\/title>)/i;
      if (titleRegex.test(content)) {
        content = content.replace(titleRegex, '$1\n  <link rel="stylesheet" href="styles/ghost-v4.css"/>');
        console.log(`  → 添加 ghost-v4.css 引用`);
      }
    }
    
    // 5. 清理多余的空行
    content = content.replace(/\n\s*\n\s*\n/g, '\n\n');
    content = content.replace(/^\s*[\r\n]/gm, '');
    
    // 只有在内容实际改变时才写入
    if (content !== originalContent) {
      writeFileSync(filePath, content, 'utf8');
      console.log(`  已修复`);
    } else {
      console.log(`  无需修复`);
    }
    
  } catch (error) {
    console.error(`  修复失败: ${error.message}`);
  }
}

// 主函数
function main() {
  console.log('开始修复脚本标签和CSS引用...');
  
  // 查找所有HTML文件
  const htmlFiles = findHtmlFiles(OEBPS_PATH);
  console.log(`找到 ${htmlFiles.length} 个HTML/XHTML文件`);
  
  // 修复每个文件
  let fixedCount = 0;
  for (const file of htmlFiles) {
    fixFile(file);
    fixedCount++;
  }
  
  console.log(`\n完成！修复了 ${fixedCount} 个文件`);
}

// 执行
main();