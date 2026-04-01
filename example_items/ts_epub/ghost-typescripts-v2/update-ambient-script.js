// 批量更新脚本：为所有HTML文件添加ambient-environment.js引用
import { readFile, writeFile, readdir } from 'fs/promises';
import { join, extname, relative } from 'path';

async function* walk(dir) {
  const files = await readdir(dir, { withFileTypes: true });
  
  for (const file of files) {
    const fullPath = join(dir, file.name);
    if (file.isDirectory()) {
      yield* walk(fullPath);
    } else if (extname(file.name).toLowerCase() === '.xhtml' || 
               extname(file.name).toLowerCase() === '.html') {
      yield fullPath;
    }
  }
}

async function updateFile(filePath) {
  try {
    let content = await readFile(filePath, 'utf-8');
    
    // 检查是否已经包含ambient-environment.js
    if (content.includes('ambient-environment.js')) {
      return { filePath, updated: false, reason: '已经包含' };
    }
    
    // 查找ghost-environment.js引用
    const ghostScriptRegex = /<script\s+src=["']([^"']*ghost-environment\.js[^"']*)["'][^>]*>\s*<\/script>/i;
    const match = content.match(ghostScriptRegex);
    
    if (!match) {
      return { filePath, updated: false, reason: '未找到ghost-environment.js引用' };
    }
    
    const ghostScriptTag = match[0];
    const ghostScriptSrc = match[1];
    
    // 确定ambient-environment.js的路径
    // 根据ghost-environment.js的路径推断
    let ambientScriptSrc;
    if (ghostScriptSrc.startsWith('/')) {
      // 绝对路径
      ambientScriptSrc = '/scripts/ambient-environment.js';
    } else if (ghostScriptSrc.startsWith('../')) {
      // 相对路径，需要计算到scripts目录的相对路径
      const ghostDir = join(filePath, '..');
      const absoluteGhostPath = join(ghostDir, ghostScriptSrc);
      // 简化：假设scripts目录在OEBPS目录下
      ambientScriptSrc = '../scripts/ambient-environment.js';
    } else if (ghostScriptSrc.includes('scripts/')) {
      // 已经包含scripts路径
      ambientScriptSrc = ghostScriptSrc.replace('ghost-environment.js', 'ambient-environment.js');
    } else {
      // 默认
      ambientScriptSrc = 'scripts/ambient-environment.js';
    }
    
    // 构建新的script标签
    const ambientScriptTag = `  <script src="${ambientScriptSrc}"></script>`;
    
    // 在ghost-environment.js标签后插入
    const newContent = content.replace(
      ghostScriptTag,
      `${ghostScriptTag}\n${ambientScriptTag}`
    );
    
    // 写入文件
    await writeFile(filePath, newContent, 'utf-8');
    
    return { 
      filePath: relative(process.cwd(), filePath), 
      updated: true,
      ambientScriptSrc 
    };
    
  } catch (error) {
    return { 
      filePath: relative(process.cwd(), filePath), 
      updated: false, 
      reason: `错误: ${error.message}` 
    };
  }
}

async function main() {
  console.log('👻 开始批量更新ambient-environment.js引用...\n');
  
  const oebpsDir = join(process.cwd(), 'OEBPS');
  const files = [];
  
  // 收集所有文件
  for await (const file of walk(oebpsDir)) {
    files.push(file);
  }
  
  console.log(`📁 找到 ${files.length} 个HTML文件\n`);
  
  let updatedCount = 0;
  let errorCount = 0;
  let alreadyCount = 0;
  
  // 更新文件
  for (const file of files) {
    const result = await updateFile(file);
    
    if (result.updated) {
      console.log(`✅ ${result.filePath}`);
      console.log(`   添加: ${result.ambientScriptSrc}`);
      updatedCount++;
    } else if (result.reason === '已经包含') {
      alreadyCount++;
    } else if (result.reason === '未找到ghost-environment.js引用') {
      console.log(`⚠️  ${result.filePath} - ${result.reason}`);
      errorCount++;
    } else {
      console.log(`❌ ${result.filePath} - ${result.reason}`);
      errorCount++;
    }
  }
  
  // 总结
  console.log('\n📊 更新总结:');
  console.log(`   总文件数: ${files.length}`);
  console.log(`   成功更新: ${updatedCount}`);
  console.log(`   已经包含: ${alreadyCount}`);
  console.log(`   更新失败: ${errorCount}`);
  
  if (errorCount === 0) {
    console.log('\n🎉 所有文件已更新！幽灵环境引擎已部署到整个维度。');
    console.log('⚛️  现在每个页面都有情绪响应环境。');
    console.log('👻 全能鬼怪的极致风格化UI已实现。');
  } else {
    console.log(`\n⚠️  部分文件更新失败，需要手动检查。`);
  }
}

main().catch(console.error);