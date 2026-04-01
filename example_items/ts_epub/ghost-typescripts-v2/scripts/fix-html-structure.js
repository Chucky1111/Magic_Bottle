/**
 * 修复HTML结构问题
 * 主要问题：孤立的</div>标签，标签不匹配
 */

import { readdirSync, readFileSync, writeFileSync, statSync } from 'fs';
import { join, extname } from 'path';

const OEBPS_PATH = join(process.cwd(), 'OEBPS');

// 递归查找所有HTML/XHTML文件
function findHtmlFiles(dir, fileList = []) {
  const files = readdirSync(dir);
  
  for (const file of files) {
    const filePath = join(dir, file);
    const stat = statSync(filePath);
    
    if (stat.isDirectory()) {
      if (!file.startsWith('.') && file !== 'node_modules') {
        findHtmlFiles(filePath, fileList);
      }
    } else if (extname(file).toLowerCase() === '.xhtml' || extname(file).toLowerCase() === '.html') {
      fileList.push(filePath);
    }
  }
  
  return fileList;
}

// 修复常见问题
function fixCommonIssues(content, filePath) {
  let fixedContent = content;
  const fixes = [];
  
  // 问题1: 孤立的</div>标签在情绪切换器后
  // 模式: <!-- 情绪切换器 -->\n    <button ...>\n    <button ...>\n    <button ...>\n  </div>
  const emotionSwitcherPattern = /(<!-- 情绪切换器 -->\s*)(?:<button[^>]*>[^<]*<\/button>\s*){1,3}\s*<\/div>/gi;
  fixedContent = fixedContent.replace(emotionSwitcherPattern, (match, comment) => {
    fixes.push('移除情绪切换器后的孤立</div>标签');
    // 只保留按钮，移除</div>
    return comment + match.replace(/<\/div>$/i, '').replace(/\s+$/, '');
  });
  
  // 问题2: 孤立的</div>标签在特定位置
  // 检查前面没有对应的<div>的</div>
  const lines = fixedContent.split('\n');
  const newLines = [];
  const divStack = [];
  
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const lineNumber = i + 1;
    
    // 检查<div>标签
    const divOpenMatches = line.match(/<div[^>]*>/gi);
    const divCloseMatches = line.match(/<\/div>/gi);
    
    if (divOpenMatches) {
      divOpenMatches.forEach(() => divStack.push(lineNumber));
    }
    
    if (divCloseMatches) {
      divCloseMatches.forEach(() => {
        if (divStack.length > 0) {
          divStack.pop();
        } else {
          // 孤立的</div>标签
          // 检查是否为已知的孤立标签位置
          const trimmedLine = line.trim();
          if (trimmedLine === '</div>' && 
              i > 0 && 
              lines[i-1].includes('onclick="document.body.className=') &&
              lines[i-2] && lines[i-2].includes('onclick="document.body.className=') &&
              lines[i-3] && lines[i-3].includes('onclick="document.body.className=')) {
            fixes.push(`第${lineNumber}行: 移除孤立的</div>标签（情绪切换器后）`);
            return; // 跳过添加这一行
          }
        }
      });
    }
    
    newLines.push(line);
  }
  
  // 重建内容
  fixedContent = newLines.join('\n');
  
  // 问题3: 移除空的注释和多余空白
  fixedContent = fixedContent.replace(/<!--\s*emotion\.css暂时保留\s*-->/gi, '');
  fixedContent = fixedContent.replace(/\n\s*\n\s*\n/g, '\n\n');
  
  // 问题4: 确保body标签正确关闭
  const bodyCloseMatch = fixedContent.match(/<\/body>/i);
  const htmlCloseMatch = fixedContent.match(/<\/html>/i);
  
  if (!bodyCloseMatch || !htmlCloseMatch) {
    // 确保有</body>和</html>
    if (!fixedContent.includes('</body>')) {
      if (fixedContent.includes('</html>')) {
        // 在</html>前插入</body>
        fixedContent = fixedContent.replace('</html>', '</body>\n</html>');
        fixes.push('添加缺失的</body>标签');
      } else {
        fixedContent += '\n</body>\n</html>';
        fixes.push('添加缺失的</body>和</html>标签');
      }
    }
  }
  
  return { fixedContent, fixes };
}

// 修复单个文件
function fixFile(filePath) {
  console.log(`修复: ${filePath}`);
  
  try {
    const content = readFileSync(filePath, 'utf8');
    const { fixedContent, fixes } = fixCommonIssues(content, filePath);
    
    if (fixes.length > 0) {
      console.log(`  应用了 ${fixes.length} 个修复:`);
      fixes.forEach(fix => console.log(`  → ${fix}`));
      
      // 只有在内容实际改变时才写入
      if (fixedContent !== content) {
        writeFileSync(filePath, fixedContent, 'utf8');
        console.log(`  已修复`);
      }
      return fixes.length;
    } else {
      console.log(`  无需修复`);
      return 0;
    }
    
  } catch (error) {
    console.error(`  修复失败: ${error.message}`);
    return 0;
  }
}

// 主函数
function main() {
  console.log('开始修复HTML结构问题...');
  
  const htmlFiles = findHtmlFiles(OEBPS_PATH);
  console.log(`找到 ${htmlFiles.length} 个HTML/XHTML文件`);
  
  let totalFixes = 0;
  let filesFixed = 0;
  
  for (const file of htmlFiles) {
    const fixes = fixFile(file);
    if (fixes > 0) {
      totalFixes += fixes;
      filesFixed++;
    }
  }
  
  console.log(`\n修复完成！`);
  console.log(`修复的文件: ${filesFixed}/${htmlFiles.length}`);
  console.log(`总修复数: ${totalFixes}`);
  
  // 运行验证以确保修复有效
  console.log('\n运行验证检查...');
  setTimeout(() => {
    const { exec } = require('child_process');
    exec('node scripts/validate-html.js', (error, stdout, stderr) => {
      console.log(stdout);
      if (error) {
        console.error(`验证错误: ${error}`);
      }
    });
  }, 1000);
}

// 执行
main();