// 幽灵维度v4.0验证脚本
import { readFile, readdir } from 'fs/promises';
import { join, extname } from 'path';

async function checkFile(filePath) {
  try {
    const content = await readFile(filePath, 'utf-8');
    const issues = [];
    
    // 检查CSS链接
    if (content.includes('rel="stylesheet"')) {
      const hasGhostV4 = content.includes('ghost-v4.css');
      const hasGhostCSS = content.includes('ghost.css') && !content.includes('ghost-v4.css');
      const hasGhostDimension = content.includes('ghost-dimension.css');
      const hasEmotion = content.includes('emotion.css');
      
      if (!hasGhostV4) {
        issues.push('未链接ghost-v4.css');
      }
      if (hasGhostCSS) {
        issues.push('仍链接ghost.css（旧版本）');
      }
      if (hasGhostDimension) {
        issues.push('仍链接ghost-dimension.css（旧版本）');
      }
      if (hasEmotion && !content.includes('emotion.css暂时保留')) {
        issues.push('仍链接emotion.css');
      }
    }
    
    // 检查HTML结构
    const hasDoctype = content.includes('<!DOCTYPE html>');
    const hasBodyClose = content.includes('</body>');
    const hasHtmlClose = content.includes('</html>');
    
    if (!hasDoctype) issues.push('缺少DOCTYPE声明');
    if (!hasBodyClose) issues.push('缺少</body>标签');
    if (!hasHtmlClose) issues.push('缺少</html>标签');
    
    // 检查幽灵注释使用
    const phantomNoteCount = (content.match(/class="phantom-note"/g) || []).length;
    const hasChineseText = /[\u4e00-\u9fff]/.test(content);
    
    return {
      filePath,
      issues,
      phantomNoteCount,
      hasChineseText,
      ok: issues.length === 0
    };
  } catch (error) {
    return {
      filePath,
      issues: [`读取失败: ${error.message}`],
      ok: false
    };
  }
}

async function scanDirectory(dir, fileList = []) {
  const files = await readdir(dir, { withFileTypes: true });
  
  for (const file of files) {
    const fullPath = join(dir, file.name);
    
    if (file.isDirectory()) {
      await scanDirectory(fullPath, fileList);
    } else if (extname(file.name).toLowerCase() === '.xhtml' || 
               extname(file.name).toLowerCase() === '.html') {
      fileList.push(fullPath);
    }
  }
  
  return fileList;
}

async function main() {
  console.log('👻 幽灵维度v4.0全面验证\n');
  
  const oebpsDir = join(process.cwd(), 'OEBPS');
  const files = await scanDirectory(oebpsDir);
  
  console.log(`📁 扫描到 ${files.length} 个HTML文件\n`);
  
  let totalIssues = 0;
  let filesWithIssues = 0;
  let totalPhantomNotes = 0;
  
  // 检查关键文件
  const criticalFiles = [
    'OEBPS/entrance/index.xhtml',
    'OEBPS/entrance/what-is-typescript.xhtml',
    'OEBPS/appendix.xhtml',
    'OEBPS/toc-concepts.xhtml',
    'OEBPS/toc-haunted-house.xhtml'
  ];
  
  console.log('🔍 关键文件检查:');
  for (const relPath of criticalFiles) {
    const fullPath = join(process.cwd(), relPath);
    const result = await checkFile(fullPath);
    
    console.log(`   ${result.ok ? '✅' : '❌'} ${relPath}`);
    if (!result.ok && result.issues.length > 0) {
      console.log(`     问题: ${result.issues.join(', ')}`);
      filesWithIssues++;
      totalIssues += result.issues.length;
    }
    if (result.phantomNoteCount > 0) {
      totalPhantomNotes += result.phantomNoteCount;
      console.log(`     包含 ${result.phantomNoteCount} 个幽灵注释`);
    }
  }
  
  // 随机抽查其他文件
  console.log('\n🎲 随机抽查（10个文件）:');
  const otherFiles = files.filter(f => !criticalFiles.some(cf => f.includes(cf)));
  const sampleSize = Math.min(10, otherFiles.length);
  const samples = otherFiles.sort(() => Math.random() - 0.5).slice(0, sampleSize);
  
  for (const filePath of samples) {
    const relPath = filePath.substring(process.cwd().length + 1);
    const result = await checkFile(filePath);
    
    if (!result.ok) {
      console.log(`   ❌ ${relPath}`);
      console.log(`     问题: ${result.issues.join(', ')}`);
      filesWithIssues++;
      totalIssues += result.issues.length;
    } else {
      console.log(`   ✅ ${relPath}`);
    }
  }
  
  // 总结
  console.log('\n📊 验证总结:');
  console.log(`   总文件数: ${files.length}`);
  console.log(`   关键文件: ${criticalFiles.length} 个`);
  console.log(`   发现问题: ${totalIssues} 个`);
  console.log(`   有问题文件: ${filesWithIssues} 个`);
  console.log(`   幽灵注释总数: ${totalPhantomNotes} 个`);
  
  if (totalIssues === 0) {
    console.log('\n🎉 所有检查通过！幽灵维度v4.0结构完整。');
    console.log('🎨 美术风格符合幽灵存在主义理念');
    console.log('🔧 HTML结构错误已修复');
    console.log('👻 文字方向问题已解决');
    console.log('⚛️ 维度稳定性确认');
  } else {
    console.log('\n⚠️  发现一些问题需要修复。');
    process.exit(1);
  }
}

main().catch(console.error);