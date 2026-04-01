/**
 * 清理重复的注释
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

// 清理重复注释
function cleanupFile(filePath) {
  console.log(`清理: ${filePath}`);
  
  try {
    let content = readFileSync(filePath, 'utf8');
    const originalContent = content;
    
    // 清理重复的"情绪切换器"注释
    content = content.replace(/<!-- 情绪切换器 -->\s*<!-- 情绪切换器 -->/g, '<!-- 情绪切换器 -->');
    
    // 清理孤立的情绪切换器按钮（v4.0中不需要）
    // v4.0使用环境响应系统，不需要手动情绪切换
    const emotionSwitcherPattern = /<!-- 情绪切换器 -->\s*(?:<button[^>]*onclick="document\.body\.className='[^']*'"[^>]*>[^<]*<\/button>\s*){1,3}/g;
    if (emotionSwitcherPattern.test(content)) {
      // 移除整个情绪切换器区块
      content = content.replace(emotionSwitcherPattern, '');
      console.log(`  → 移除情绪切换器按钮（v4.0中已过时）`);
    }
    
    // 清理多余空白
    content = content.replace(/\n\s*\n\s*\n/g, '\n\n');
    
    if (content !== originalContent) {
      writeFileSync(filePath, content, 'utf8');
      console.log(`  已清理`);
      return 1;
    } else {
      console.log(`  无需清理`);
      return 0;
    }
    
  } catch (error) {
    console.error(`  清理失败: ${error.message}`);
    return 0;
  }
}

// 主函数
function main() {
  console.log('开始清理重复注释和过时元素...');
  
  const htmlFiles = findHtmlFiles(OEBPS_PATH);
  console.log(`找到 ${htmlFiles.length} 个HTML/XHTML文件`);
  
  let cleanedCount = 0;
  for (const file of htmlFiles) {
    cleanedCount += cleanupFile(file);
  }
  
  console.log(`\n完成！清理了 ${cleanedCount} 个文件`);
}

main();