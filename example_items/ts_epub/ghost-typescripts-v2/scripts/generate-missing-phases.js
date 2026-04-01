#!/usr/bin/env bun

/**
 * 生成缺失的鬼屋阶段文件（阶段三至阶段六）
 */

import { writeFile, mkdir } from 'fs/promises';
import { dirname, join } from 'path';

/**
 * 生成鬼屋断面HTML（简化版）
 */
function generateHauntedHouseHTML(title, phase, content) {
  const phaseText = `阶段${phase}`;
  const emotionClass = 'excited';
  
  return `<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="zh-CN">
<head>
  <meta charset="UTF-8"/>
  <title>鬼屋${phaseText}：${title}</title>
  <link rel="stylesheet" href="../../styles/ghost.css"/>
  <link rel="stylesheet" href="../../styles/emotion.css"/>
  <link rel="stylesheet" href="../../styles/ghost-dimension.css"/>
</head>
<body class="${emotionClass}">
  <!-- 魔瓶环境设定：鬼屋建造现场，类型定义的蓝图在空中展开，逐步转化为具体的结构 -->
  
  <div class="ghost-section">
    <div class="emotion-indicator">兴奋推荐</div>
    
    <h1>鬼屋${phaseText}：${title}</h1>
    
    <div class="phantom-note">
      幽灵观察：你不是在写代码，是在建造数字鬼屋。每个类型定义是一块砖，每个接口是一面墙。
    </div>
    
    ${content}
    
    <!-- 鬼屋项目导航 -->
    <nav class="ghost-passages">
      <h3>鬼屋项目导航</h3>
      <ul>
        <li><a href="../../toc-haunted-house.xhtml">鬼屋项目总览</a></li>
        ${phase > 1 ? `<li><a href="../phase${phase-1}/index.xhtml">上一阶段</a></li>` : ''}
        ${phase < 6 ? `<li><a href="../phase${phase+1}/index.xhtml">下一阶段</a></li>` : ''}
        <li><a href="../../entrance/index.xhtml">返回入口</a></li>
      </ul>
    </nav>
    
    <!-- 项目进度追踪 -->
    <div class="project-progress">
      <h3>鬼屋项目进度</h3>
      <p>${phaseText}：${title} ✓ 进行中</p>
      <p><a href="../../toc-haunted-house.xhtml">查看完整进度</a></p>
    </div>
    
    <!-- 魔瓶的最后观察 -->
    <div class="phantom-note" style="margin-top: 2em;">
      记住魔瓶的世界观："没有无法塑造的规则，只有无法表达的现状。"
      鬼屋建造不是技术练习，是用类型表达想象中的世界。
      如果你能想象一个幽灵规则，你就能用类型定义它。
      如果你能用类型定义它，你就能用代码实现它。
      如果你能用代码实现它，你就能观察它如何运行。
      
      这是AI时代的创造循环：想象 → 定义 → 实现 → 观察。
    </div>
  </div>
  
  <!-- 情绪切换器 -->
  <div class="emotion-switcher">
    <button class="confused" onclick="document.body.className='confused'">困惑</button>
    <button class="curious" onclick="document.body.className='curious'">好奇</button>
    <button class="excited" onclick="document.body.className='excited'">兴奋</button>
    <button class="frustrated" onclick="document.body.className='frustrated'">挫败</button>
  </div>
  
  <style>
    .project-progress {
      background: rgba(64, 224, 208, 0.1);
      border: 1px solid rgba(64, 224, 208, 0.3);
      border-radius: 8px;
      padding: 1em;
      margin: 2em 0;
    }
  </style>
</body>
</html>`;
}

// 阶段三文件
const phase3Files = [
  { name: 'generic-phenomena.xhtml', title: '泛型现象系统' },
  { name: 'conditional-rules.xhtml', title: '条件规则类型' },
  { name: 'utility-types.xhtml', title: '实用工具类型' },
  { name: 'event-system.xhtml', title: '事件系统类型' }
];

// 阶段四文件
const phase4Files = [
  { name: 'module-structure.xhtml', title: '模块结构设计' },
  { name: 'tsconfig.xhtml', title: '项目配置' },
  { name: 'ai-integration.xhtml', title: 'AI集成配置' },
  { name: 'testing-setup.xhtml', title: '测试配置' }
];

// 阶段五文件
const phase5Files = [
  { name: 'ai-prompting.xhtml', title: '给AI的鬼屋提示' },
  { name: 'code-generation.xhtml', title: '代码生成实践' },
  { name: 'error-handling.xhtml', title: '错误处理与调试' },
  { name: 'testing.xhtml', title: '测试幽灵行为' }
];

// 阶段六文件
const phase6Files = [
  { name: 'performance-optimization.xhtml', title: '性能优化' },
  { name: 'advanced-patterns.xhtml', title: '高级设计模式' },
  { name: 'extensibility.xhtml', title: '可扩展性设计' },
  { name: 'deployment.xhtml', title: '部署与分享' }
];

// 为每个文件生成内容
const fileContents = {
  // 阶段三
  'generic-phenomena.xhtml': `
    <section>
      <h2>泛型现象系统</h2>
      <p>使用泛型创建可重用的幽灵现象模板。泛型让你可以定义类型参数，创建灵活的模板。</p>
      <pre><code>interface Phenomenon<T> {
  id: string;
  type: T;
  intensity: number;
}</code></pre>
    </section>
  `,
  'conditional-rules.xhtml': `
    <section>
      <h2>条件规则类型</h2>
      <p>基于条件的幽灵行为。使用条件类型定义规则，根据幽灵状态改变行为。</p>
      <pre><code>type Behavior<T> = T extends 'angry' ? AttackBehavior : CalmBehavior;</code></pre>
    </section>
  `,
  'utility-types.xhtml': `
    <section>
      <h2>实用工具类型</h2>
      <p>鬼屋专用的类型工具，简化常见操作。</p>
      <pre><code>type HauntedRoom = Room & { ghostCount: number };</code></pre>
    </section>
  `,
  'event-system.xhtml': `
    <section>
      <h2>事件系统类型</h2>
      <p>定义幽灵事件的触发与处理系统。</p>
      <pre><code>interface GhostEvent {
  type: string;
  source: string;
  timestamp: Date;
}</code></pre>
    </section>
  `,
  // 阶段四
  'module-structure.xhtml': `
    <section>
      <h2>模块结构设计</h2>
      <p>组织鬼屋代码结构，划分模块边界。</p>
      <pre><code>// src/ghosts/
// src/rooms/
// src/phenomena/</code></pre>
    </section>
  `,
  'tsconfig.xhtml': `
    <section>
      <h2>项目配置</h2>
      <p>配置TypeScript编译器以适应鬼屋项目需求。</p>
      <pre><code>{
  "compilerOptions": {
    "strict": true
  }
}</code></pre>
    </section>
  `,
  'ai-integration.xhtml': `
    <section>
      <h2>AI集成配置</h2>
      <p>配置AI工具以帮助实现鬼屋功能。</p>
      <pre><code>// AI提示模板
const ghostPrompt = "Create a TypeScript class for a ghost...";</code></pre>
    </section>
  `,
  'testing-setup.xhtml': `
    <section>
      <h2>测试配置</h2>
      <p>设置测试环境以验证鬼屋规则。</p>
      <pre><code>describe('Ghost behavior', () => {
  test('should haunt room', () => { ... });
});</code></pre>
    </section>
  `,
  // 阶段五
  'ai-prompting.xhtml': `
    <section>
      <h2>给AI的鬼屋提示</h2>
      <p>如何向AI描述幽灵世界需求以获得高质量的代码。</p>
      <pre><code>"请创建一个TypeScript类型系统，描述一个幽灵..."</code></pre>
    </section>
  `,
  'code-generation.xhtml': `
    <section>
      <h2>代码生成实践</h2>
      <p>基于类型定义生成具体的实现代码。</p>
      <pre><code>// AI生成的代码
class Ghost implements IGhost { ... }</code></pre>
    </section>
  `,
  'error-handling.xhtml': `
    <section>
      <h2>错误处理与调试</h2>
      <p>处理鬼屋实现中的错误和异常情况。</p>
      <pre><code>try {
  ghost.haunt(room);
} catch (error) {
  console.error('Haunting failed:', error);
}</code></pre>
    </section>
  `,
  'testing.xhtml': `
    <section>
      <h2>测试幽灵行为</h2>
      <p>编写测试以验证幽灵行为符合类型定义。</p>
      <pre><code>test('ghost should be invisible at day', () => {
  expect(ghost.isVisible).toBe(false);
});</code></pre>
    </section>
  `,
  // 阶段六
  'performance-optimization.xhtml': `
    <section>
      <h2>性能优化</h2>
      <p>优化鬼屋模拟性能，确保流畅运行。</p>
      <pre><code>// 使用缓存
const ghostCache = new Map<string, Ghost>();</code></pre>
    </section>
  `,
  'advanced-patterns.xhtml': `
    <section>
      <h2>高级设计模式</h2>
      <p>应用高级设计模式实现复杂的幽灵行为。</p>
      <pre><code>// 观察者模式：幽灵观察房间变化
interface Observer { update(): void; }</code></pre>
    </section>
  `,
  'extensibility.xhtml': `
    <section>
      <h2>可扩展性设计</h2>
      <p>设计鬼屋系统以轻松添加新的幽灵类型和现象。</p>
      <pre><code>interface IGhostExtension {
  register(ghost: Ghost): void;
}</code></pre>
    </section>
  `,
  'deployment.xhtml': `
    <section>
      <h2>部署与分享</h2>
      <p>将完成的鬼屋项目部署并分享给他人体验。</p>
      <pre><code>npm run build
npm publish</code></pre>
    </section>
  `
};

async function generatePhaseFiles(phase, files) {
  for (const file of files) {
    const content = fileContents[file.name] || `<section><h2>${file.title}</h2><p>内容待完善。</p></section>`;
    const html = generateHauntedHouseHTML(file.title, phase, content);
    const outputPath = join('OEBPS', `haunted-house/phase${phase}`, file.name);
    
    await mkdir(dirname(outputPath), { recursive: true });
    await writeFile(outputPath, html, 'utf-8');
    console.log(`生成鬼屋文件: ${outputPath}`);
  }
}

async function generateAllMissingPhases() {
  console.log('生成阶段三...');
  await generatePhaseFiles(3, phase3Files);
  
  console.log('生成阶段四...');
  await generatePhaseFiles(4, phase4Files);
  
  console.log('生成阶段五...');
  await generatePhaseFiles(5, phase5Files);
  
  console.log('生成阶段六...');
  await generatePhaseFiles(6, phase6Files);
  
  console.log('所有缺失阶段已生成！');
}

// 运行生成器
if (import.meta.main) {
  generateAllMissingPhases().catch(console.error);
}