/**
 * 简单HTML结构验证脚本
 * 检查标签匹配和基本结构
 */

import { readdirSync, readFileSync, statSync } from 'fs';
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

// 简单标签匹配验证
function validateTags(content, filePath) {
  const lines = content.split('\n');
  const tagStack = [];
  const errors = [];
  
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const lineNumber = i + 1;
    
    // 查找所有标签
    const tagMatches = line.match(/<(\/?)([a-zA-Z][a-zA-Z0-9]*)(?:\s[^>]*)?>/g);
    
    if (tagMatches) {
      for (const tag of tagMatches) {
        const isClosing = tag.startsWith('</');
        const tagNameMatch = tag.match(/<(\/?)([a-zA-Z][a-zA-Z0-9]*)/);
        if (!tagNameMatch) continue;
        
        const tagName = tagNameMatch[2].toLowerCase();
        
        // 忽略自闭合标签
        if (tag.endsWith('/>') || ['meta', 'link', 'br', 'hr', 'img', 'input'].includes(tagName)) {
          continue;
        }
        
        if (isClosing) {
          if (tagStack.length === 0) {
            errors.push(`第${lineNumber}行: 多余的关闭标签 </${tagName}>，没有对应的打开标签`);
          } else {
            const lastTag = tagStack[tagStack.length - 1];
            if (lastTag.tagName === tagName) {
              tagStack.pop();
            } else {
              errors.push(`第${lineNumber}行: 标签不匹配，期望 </${lastTag.tagName}>，实际为 </${tagName}>`);
            }
          }
        } else {
          tagStack.push({
            tagName,
            line: lineNumber
          });
        }
      }
    }
  }
  
  // 检查未关闭的标签
  if (tagStack.length > 0) {
    for (const tag of tagStack) {
      errors.push(`第${tag.line}行: 标签 <${tag.tagName}> 未关闭`);
    }
  }
  
  return errors;
}

// 验证单个文件
function validateFile(filePath) {
  console.log(`\n验证: ${filePath}`);
  
  try {
    const content = readFileSync(filePath, 'utf8');
    const errors = validateTags(content, filePath);
    
    if (errors.length > 0) {
      console.log(`  发现 ${errors.length} 个错误:`);
      errors.forEach(error => console.log(`  → ${error}`));
      return errors.length;
    } else {
      console.log(`  ✓ 通过验证`);
      return 0;
    }
    
  } catch (error) {
    console.error(`  读取失败: ${error.message}`);
    return 1;
  }
}

// 主函数
function main() {
  console.log('开始HTML结构验证...');
  
  const htmlFiles = findHtmlFiles(OEBPS_PATH);
  console.log(`找到 ${htmlFiles.length} 个HTML/XHTML文件`);
  
  let totalErrors = 0;
  let filesWithErrors = 0;
  
  for (const file of htmlFiles) {
    const errors = validateFile(file);
    if (errors > 0) {
      totalErrors += errors;
      filesWithErrors++;
    }
  }
  
  console.log(`\n验证完成！`);
  console.log(`有错误的文件: ${filesWithErrors}/${htmlFiles.length}`);
  console.log(`总错误数: ${totalErrors}`);
  
  if (totalErrors > 0) {
    console.log('\n常见问题:');
    console.log('1. 检查未关闭的<div>、<section>、<table>等标签');
    console.log('2. 检查标签嵌套顺序是否正确');
    console.log('3. 确保每个打开标签都有对应的关闭标签');
  }
}

// 执行
main();