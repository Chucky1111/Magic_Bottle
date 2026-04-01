/**
 * 清理重复脚本标签和旧样式引用
 */

import { readdirSync, readFileSync, writeFileSync, statSync } from 'fs';
import { join, extname } from 'path';

const OEBPS_PATH = join(process.cwd(), 'OEBPS');

// 要处理的脚本文件
const V4_SCRIPTS = [
  'ghost-environment.js',
  'quantum-content.js', 
  'ghost-guide.js'
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

// 清理单个文件
function cleanupFile(filePath) {
  console.log(`清理: ${filePath}`);
  
  try {
    let content = readFileSync(filePath, 'utf8');
    const originalContent = content;
    
    // 1. 移除emotion.css引用
    const emotionCssRegex = /<link[^>]*href="[^"]*emotion\.css"[^>]*>/gi;
    content = content.replace(emotionCssRegex, '');
    
    // 2. 确保只有一个ghost-v4.css引用（不移除，但要检查路径正确性）
    const v4CssRegex = /<link[^>]*href="[^"]*ghost-v4\.css"[^>]*>/gi;
    const v4Matches = content.match(v4CssRegex);
    if (v4Matches && v4Matches.length > 1) {
      // 如果有多个，只保留第一个
      const firstMatch = v4Matches[0];
      content = content.replace(v4CssRegex, (match, offset) => {
        return offset === content.indexOf(firstMatch) ? firstMatch : '';
      });
    }
    
    // 3. 清理重复的脚本标签
    for (const script of V4_SCRIPTS) {
      const scriptRegex = new RegExp(`<script[^>]*src="[^"]*${script}"[^>]*>`, 'gi');
      const matches = content.match(scriptRegex);
      
      if (matches && matches.length > 1) {
        // 保留第一个，移除后面的
        const firstMatch = matches[0];
        let foundFirst = false;
        
        content = content.replace(scriptRegex, (match) => {
          if (!foundFirst) {
            foundFirst = true;
            return match; // 保留第一个
          }
          return ''; // 移除后续的
        });
        
        console.log(`  → 移除重复的 ${script} 标签`);
      }
    }
    
    // 4. 清理空的script标签行
    content = content.replace(/<script[^>]*src=""[^>]*>/gi, '');
    content = content.replace(/\n\s*\n\s*\n/g, '\n\n');
    
    // 5. 移除body上的情绪类（如果还有的话）
    const emotionClasses = ['confused', 'curious', 'excited', 'frustrated'];
    emotionClasses.forEach(className => {
      const bodyClassRegex = new RegExp(`<body[^>]*class="[^"]*\\b${className}\\b[^"]*"`, 'g');
      content = content.replace(bodyClassRegex, (match) => {
        return match.replace(new RegExp(`\\b${className}\\b`, 'g'), '').replace(/\s+/g, ' ').trim();
      });
    });
    
    // 6. 确保body类为空或只有必要的类
    const bodyRegex = /<body[^>]*class="([^"]*)"[^>]*>/;
    const match = content.match(bodyRegex);
    if (match) {
      const classes = match[1].trim();
      if (!classes) {
        // 如果类名为空，移除class属性
        content = content.replace(bodyRegex, '<body>');
      }
    }
    
    // 只有在内容实际改变时才写入
    if (content !== originalContent) {
      writeFileSync(filePath, content, 'utf8');
      console.log(`  已清理`);
    } else {
      console.log(`  无需清理`);
    }
    
  } catch (error) {
    console.error(`  清理失败: ${error.message}`);
  }
}

// 主函数
function main() {
  console.log('开始清理重复标签和旧样式...');
  
  // 查找所有HTML文件
  const htmlFiles = findHtmlFiles(OEBPS_PATH);
  console.log(`找到 ${htmlFiles.length} 个HTML/XHTML文件`);
  
  // 清理每个文件
  let cleanedCount = 0;
  for (const file of htmlFiles) {
    cleanupFile(file);
    cleanedCount++;
  }
  
  console.log(`\n完成！清理了 ${cleanedCount} 个文件`);
  console.log('\n清理内容:');
  console.log('1. 移除了emotion.css引用');
  console.log('2. 移除了重复的脚本标签');
  console.log('3. 清理了body上的情绪类');
  console.log('4. 移除了空的脚本标签');
}

// 执行
main();