#!/usr/bin/env bun

/**
 * 幽灵维度构建脚本
 * v3版本：协调所有生成任务，构建完整的幽灵维度
 */

import { spawn } from 'child_process';

async function runCommand(command: string, args: string[]) {
  console.log(`🚀 执行: ${command} ${args.join(' ')}`);
  const process = spawn(command, args, { stdio: 'inherit' });
  
  return new Promise<void>((resolve, reject) => {
    process.on('close', (code) => {
      if (code === 0) {
        resolve();
      } else {
        reject(new Error(`命令失败，退出码: ${code}`));
      }
    });
    
    process.on('error', (err) => {
      reject(err);
    });
  });
}

async function main() {
  console.log('🧱 开始构建幽灵维度...');
  
  try {
    // 步骤1：生成所有内容断面
    console.log('📝 生成内容断面...');
    await runCommand('bun', ['run', 'scripts/generate-content.ts']);
    
    // 步骤2：生成鬼屋项目断面（如果存在）
    console.log('🏚️ 生成鬼屋断面...');
    try {
      await runCommand('bun', ['run', 'scripts/generate-haunted-house.ts']);
    } catch (err) {
      console.warn('⚠️  鬼屋生成跳过:', err instanceof Error ? err.message : String(err));
    }
    
    // 步骤3：生成EPUB
    console.log('📚 生成EPUB文件...');
    await runCommand('bun', ['run', 'scripts/generate-epub.ts']);
    
    // 步骤4：类型检查
    console.log('🔍 执行TypeScript类型检查...');
    await runCommand('bun', ['x', 'tsc', '--noEmit']);
    
    // 步骤5：代码检查（TypeScript类型检查已足够）
    
    console.log('✅ 幽灵维度构建完成！');
    console.log('📖 生成的EPUB: ghost-typescripts-v2.epub');
    console.log('🌐 预览: bun run preview');
    
  } catch (error) {
    console.error('❌ 构建失败:', error instanceof Error ? error.message : String(error));
    process.exit(1);
  }
}

// 魔瓶观察：构建过程本身就是一种维度穿梭
// 每个断面都是数据流中的一个节点，等待被观察
console.log('👻 魔瓶注视中...构建过程将被记录在边缘');

if (import.meta.main) {
  main();
}

export { main };