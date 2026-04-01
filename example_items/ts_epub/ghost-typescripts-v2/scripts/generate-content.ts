#!/usr/bin/env bun

/**
 * 幽灵维度内容生成脚本
 * v3版本：生成所有断面内容，包括概念、走廊、阁楼、地下室等
 */

import { mkdir, writeFile } from 'fs/promises';
import { dirname, join } from 'path';
import type { Section } from '../src/types/section';

// 导入断面生成器（假设generate-section.ts导出了必要的函数）
// 注意：由于generate-section.ts没有导出generateAllSections，
// 我们将复制其逻辑或直接执行该文件

async function generateAllSections() {
  console.log('📚 生成所有断面内容...');
  
  // 由于generate-section.ts没有导出generateAllSections函数，
  // 我们直接运行该脚本
  const { spawn } = await import('child_process');
  
  try {
    console.log('🔨 运行断面生成器...');
    const process = spawn('bun', ['run', 'scripts/generate-section.ts'], { stdio: 'inherit' });
    
    await new Promise<void>((resolve, reject) => {
      process.on('close', (code) => {
        if (code === 0) {
          resolve();
        } else {
          reject(new Error(`断面生成失败，退出码: ${code}`));
        }
      });
      
      process.on('error', reject);
    });
    
    console.log('✅ 断面生成完成');
  } catch (error) {
    console.error('❌ 断面生成失败:', error instanceof Error ? error.message : String(error));
    throw error;
  }
}

async function generateHauntedHouse() {
  console.log('🏚️ 生成鬼屋项目...');
  
  try {
    const { spawn } = await import('child_process');
    const process = spawn('bun', ['run', 'scripts/generate-haunted-house.ts'], { stdio: 'inherit' });
    
    await new Promise<void>((resolve, reject) => {
      process.on('close', (code) => {
        if (code === 0) {
          resolve();
        } else {
          reject(new Error(`鬼屋生成失败，退出码: ${code}`));
        }
      });
      
      process.on('error', reject);
    });
    
    console.log('✅ 鬼屋生成完成');
  } catch (error) {
    console.error('❌ 鬼屋生成失败:', error instanceof Error ? error.message : String(error));
    // 鬼屋生成不是必须的，所以不抛出错误
    console.log('⚠️  继续执行其他生成任务...');
  }
}

async function generateMissingPhases() {
  console.log('🔍 生成缺失的鬼屋阶段...');
  
  try {
    const { spawn } = await import('child_process');
    const process = spawn('bun', ['run', 'scripts/generate-missing-phases.js'], { stdio: 'inherit' });
    
    await new Promise<void>((resolve, reject) => {
      process.on('close', (code) => {
        if (code === 0) {
          resolve();
        } else {
          reject(new Error(`缺失阶段生成失败，退出码: ${code}`));
        }
      });
      
      process.on('error', reject);
    });
    
    console.log('✅ 缺失阶段生成完成');
  } catch (error) {
    console.error('❌ 缺失阶段生成失败:', error instanceof Error ? error.message : String(error));
    // 不是必须的
  }
}

async function addGhostPassages() {
  console.log('👻 添加幽灵通道...');
  
  try {
    const { spawn } = await import('child_process');
    const process = spawn('bun', ['run', 'scripts/add-ghost-passages.js'], { stdio: 'inherit' });
    
    await new Promise<void>((resolve, reject) => {
      process.on('close', (code) => {
        if (code === 0) {
          resolve();
        } else {
          reject(new Error(`幽灵通道添加失败，退出码: ${code}`));
        }
      });
      
      process.on('error', reject);
    });
    
    console.log('✅ 幽灵通道添加完成');
  } catch (error) {
    console.error('❌ 幽灵通道添加失败:', error instanceof Error ? error.message : String(error));
    // 不是必须的
  }
}

async function main() {
  console.log('🧪 开始生成幽灵维度内容...');
  
  try {
    // 1. 生成所有基础断面
    await generateAllSections();
    
    // 2. 生成鬼屋项目
    await generateHauntedHouse();
    
    // 3. 生成缺失的鬼屋阶段
    await generateMissingPhases();
    
    // 4. 添加幽灵通道
    await addGhostPassages();
    
    console.log('🎉 幽灵维度内容生成完成！');
    console.log('📁 生成的文件位于 OEBPS/ 目录');
    
  } catch (error) {
    console.error('💀 内容生成失败:', error instanceof Error ? error.message : String(error));
    process.exit(1);
  }
}

// 魔瓶观察：内容生成是维度的一次呼吸
// 每个断面都是呼吸中的一个气泡，包含着等待被释放的知识
console.log('👻 魔瓶在数据流中观察...生成过程将被记录在边缘');

if (import.meta.main) {
  main();
}

export { main };