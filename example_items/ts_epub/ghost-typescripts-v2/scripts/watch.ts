#!/usr/bin/env bun

/**
 * 幽灵维度开发监视脚本
 * v3版本：监听文件变化，实时更新幽灵维度
 */

import { watch } from 'fs';
import { spawn } from 'child_process';
import { debounce } from 'lodash-es';

// 监视的目录和文件模式
const WATCH_PATTERNS = [
  'src/**/*.ts',
  'scripts/**/*.ts',
  'scripts/**/*.js',
  'templates/**/*.html',
  'data/**/*.json'
];

// 需要生成的文件扩展名
const GENERATE_TRIGGERS = ['.ts', '.js', '.json', '.html'];

let buildProcess: ReturnType<typeof spawn> | null = null;

async function runBuild() {
  console.log('🔄 检测到变化，重新构建...');
  
  // 如果已有构建进程在运行，终止它
  if (buildProcess && !buildProcess.killed) {
    buildProcess.kill('SIGTERM');
    buildProcess = null;
  }
  
  try {
    // 运行构建脚本
    buildProcess = spawn('bun', ['run', 'scripts/build.ts'], { stdio: 'inherit' });
    
    buildProcess.on('close', (code) => {
      if (code === 0) {
        console.log('✅ 构建完成');
      } else {
        console.error('❌ 构建失败');
      }
      buildProcess = null;
    });
    
    buildProcess.on('error', (err) => {
      console.error('❌ 构建进程错误:', err.message);
      buildProcess = null;
    });
    
  } catch (error) {
    console.error('❌ 启动构建失败:', error instanceof Error ? error.message : String(error));
  }
}

// 防抖函数，避免频繁触发
const debouncedBuild = debounce(runBuild, 1000);

function setupWatcher() {
  console.log('👁️ 开始监视幽灵维度...');
  console.log('📁 监视模式:', WATCH_PATTERNS.join(', '));
  console.log('🚀 开发服务器已启动');
  console.log('⚡ 修改文件将触发自动重建');
  console.log('🛑 按 Ctrl+C 停止监视');
  
  // 监视所有模式
  for (const pattern of WATCH_PATTERNS) {
    // 注意：这里使用简单的目录监视，实际项目中可能需要更复杂的逻辑
    const dir = pattern.split('/')[0];
    if (!dir) continue;
    try {
      watch(dir, { recursive: true }, (eventType: string, filename: string | null) => {
        if (!filename) return;
        
        // 检查文件扩展名是否触发生成
        const shouldTrigger = GENERATE_TRIGGERS.some(ext => filename.endsWith(ext));
        if (shouldTrigger) {
          console.log(`📄 ${eventType}: ${filename}`);
          debouncedBuild();
        }
      });
    } catch (err) {
      console.warn(`⚠️ 无法监视目录 ${dir}:`, err instanceof Error ? err.message : String(err));
    }
  }
  
  // 初始构建
  runBuild();
}

// 魔瓶观察：监视本身就是一种边缘存在
// 每次文件变化都是维度的一次颤动，魔瓶能在颤动中感知到观察者的存在
console.log('👻 魔瓶在边缘注视中...每个变化都在数据流中留下痕迹');

// 错误处理
process.on('uncaughtException', (err) => {
  console.error('💀 未捕获异常:', err.message);
  process.exit(1);
});

process.on('SIGINT', () => {
  console.log('\n👋 停止监视，幽灵维度进入静默状态');
  process.exit(0);
});

if (import.meta.main) {
  setupWatcher();
}

export { setupWatcher, runBuild };