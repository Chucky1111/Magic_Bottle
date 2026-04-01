#!/usr/bin/env bun

/**
 * 生成缺失的页面占位符
 * 为导航中提到的但实际不存在的页面创建简单的内容
 */

import { writeFile, mkdir, stat } from 'fs/promises';
import { dirname, join, basename } from 'path';

// 基础模板函数
function generatePlaceholderHTML(title, originalPath, category, description) {
  const emotionClass = getEmotionForCategory(category);
  const parentDir = dirname(originalPath).replace(/^OEBPS[\\/]/, '');
  const backLink = parentDir === '.' ? '/' : `/${parentDir}/index.xhtml`;
  
  return `<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="zh-CN">
<head>
  <meta charset="UTF-8"/>
  <title>${title}</title>
  <link rel="stylesheet" href="/styles/ghost.css"/>
  <link rel="stylesheet" href="/styles/emotion.css"/>
  <link rel="stylesheet" href="/styles/ghost-dimension.css"/>
</head>
<body class="${emotionClass}">
  <div class="ghost-section">
    <div class="emotion-indicator">${getEmotionText(emotionClass)}</div>
    
    <h1>${title}</h1>
    
    <div class="construction-notice" style="background: rgba(251, 191, 36, 0.2); border: 2px solid rgba(251, 191, 36, 0.5); border-radius: 8px; padding: 1em; margin: 1em 0;">
      <h3 style="margin-top: 0; color: rgba(251, 191, 36, 1);">👻 断面内容规划中</h3>
      <p>这个断面 <strong>${basename(originalPath)}</strong> 是幽灵维度计划的一部分，内容正在完善中。</p>
      <p>根据规划，这里将包含关于 <strong>${description}</strong> 的内容。</p>
      <p>同时，你可以探索相关的内容，或者返回上一级选择其他断面。</p>
    </div>
    
    <div class="phantom-note">
      魔瓶观察：每个断面的创建都是一个思考过程。这个断面正在等待它的内容被思考和表达。
    </div>
    
    <section>
      <h2>这个断面将包含什么？</h2>
      <p>根据幽灵维度的规划，<strong>${title}</strong> 将包含以下内容：</p>
      <ul>
        <li>清晰的类型定义示例</li>
        <li>TypeScript代码片段</li>
        <li>AI协作提示示例</li>
        <li>常见错误和解决方案</li>
        <li>实践练习和挑战</li>
      </ul>
      <p>这些内容将帮助你更好地理解TypeScript类型系统，并应用在实际开发中。</p>
    </section>
    
    <section>
      <h2>现在可以探索什么？</h2>
      <p>在等待这个断面完善的同时，你可以：</p>
      <ul>
        <li><a href="/">返回幽灵维度入口</a>，选择其他维度穿梭</li>
        <li><a href="${backLink}">返回${getCategoryName(category)}目录</a></li>
        <li><a href="/toc-concepts.xhtml">探索概念维度</a>，学习TypeScript基础知识</li>
        <li><a href="/toc-haunted-house.xhtml">开始鬼屋项目</a>，通过实践项目学习</li>
        <li><a href="/basement/errors/index.xhtml">访问错误地下室</a>，学习调试技巧</li>
      </ul>
    </section>
    
    <div class="phantom-note" style="margin-top: 2em;">
      记住魔瓶的核心驱动力："没有无法塑造的规则，只有无法表达的现状。"
      这个断面正在等待它的规则被塑造，它的现状被表达。
    </div>
  </div>
  
  <!-- 情绪切换器 -->
  <div class="emotion-switcher">
    <button class="confused" onclick="document.body.className='confused'">困惑</button>
    <button class="curious" onclick="document.body.className='curious'">好奇</button>
    <button class="excited" onclick="document.body.className='excited'">兴奋</button>
    <button class="frustrated" onclick="document.body.className='frustrated'">挫败</button>
  </div>
</body>
</html>`;
}

function getEmotionForCategory(category) {
  switch(category) {
    case 'confused': return 'confused';
    case 'curious': return 'curious';
    case 'excited': return 'excited';
    case 'frustrated': return 'frustrated';
    case 'entrance': return 'curious';
    case 'errors': return 'frustrated';
    case 'ai': return 'excited';
    case 'secret': return 'curious';
    default: return 'curious';
  }
}

function getEmotionText(emotion) {
  switch(emotion) {
    case 'confused': return '困惑推荐';
    case 'curious': return '好奇推荐';
    case 'excited': return '兴奋推荐';
    case 'frustrated': return '挫败推荐';
    default: return '探索推荐';
  }
}

function getCategoryName(category) {
  switch(category) {
    case 'entrance': return '入口';
    case 'errors': return '错误地下室';
    case 'ai': return 'AI辅助';
    case 'secret': return '秘密通道';
    case 'confused': return '困惑内容';
    case 'curious': return '好奇内容';
    case 'excited': return '兴奋内容';
    case 'frustrated': return '挫败内容';
    default: return '相关';
  }
}

// 需要生成的缺失页面列表（从导航文件中提取）
const missingPages = [
  // 入口页面
  { path: 'OEBPS/entrance/simple-examples.xhtml', title: '简单示例集合', category: 'entrance', desc: 'TypeScript基础使用示例和简单代码片段' },
  { path: 'OEBPS/entrance/what-is-typescript.xhtml', title: 'TypeScript是什么？', category: 'entrance', desc: 'TypeScript的基本概念和幽灵视角的解释' },
  { path: 'OEBPS/entrance/why-types-matter.xhtml', title: '为什么类型在AI时代很重要？', category: 'entrance', desc: '类型系统在现代AI辅助开发中的重要性' },
  { path: 'OEBPS/entrance/first-ghost-program.xhtml', title: '第一个幽灵程序', category: 'entrance', desc: '创建第一个TypeScript幽灵程序的实践体验' },
  { path: 'OEBPS/entrance/quick-wins.xhtml', title: '快速胜利', category: 'entrance', desc: '简单但有效的小技巧和快速解决方案' },
  { path: 'OEBPS/entrance/comfort-messages.xhtml', title: '魔瓶的安慰', category: 'entrance', desc: '幽灵的鼓励话语和编程心理支持' },
  
  // 错误地下室页面
  { path: 'OEBPS/basement/errors/common-mistakes.xhtml', title: '常见错误及解决方案', category: 'errors', desc: 'TypeScript常见编译错误的原因和解决方法' },
  { path: 'OEBPS/basement/errors/type-errors.xhtml', title: '类型错误解析', category: 'errors', desc: '类型相关错误的详细分析和解决方案' },
  { path: 'OEBPS/basement/errors/syntax-errors.xhtml', title: '语法错误解析', category: 'errors', desc: '语法错误的识别和修复方法' },
  { path: 'OEBPS/basement/errors/edge-cases.xhtml', title: '边缘案例错误', category: 'errors', desc: '不常见但有趣的TypeScript边缘案例和错误' },
  { path: 'OEBPS/basement/errors/humorous-errors.xhtml', title: '幽默错误集锦', category: 'errors', desc: '有趣的TypeScript错误信息和搞笑的编译错误' },
  { path: 'OEBPS/basement/errors/common-solutions.xhtml', title: '常见问题解决方案', category: 'errors', desc: '大多数人都会犯的TypeScript错误及其解决方案' },
  
  // AI辅助页面
  { path: 'OEBPS/attic/ai-assistance/simple-prompts.xhtml', title: '给AI的简单提示', category: 'ai', desc: '如何向AI询问基本的TypeScript问题和请求帮助' },
  { path: 'OEBPS/attic/ai-assistance/advanced-prompts.xhtml', title: '给AI的高级提示', category: 'ai', desc: '如何向AI描述复杂的TypeScript需求和架构设计' },
  { path: 'OEBPS/attic/ai-assistance/data-modeling.xhtml', title: '用AI帮助设计数据模型', category: 'ai', desc: '利用AI辅助设计TypeScript数据模型和接口' },
  { path: 'OEBPS/attic/ai-assistance/type-first-prompting.xhtml', title: '类型优先的提示技巧', category: 'ai', desc: '以类型定义为先的AI提示方法和技巧' },
  { path: 'OEBPS/attic/ai-assistance/code-review.xhtml', title: '让AI审查你的代码', category: 'ai', desc: '使用AI进行TypeScript代码审查和质量检查' },
  { path: 'OEBPS/attic/ai-assistance/complex-system.xhtml', title: '复杂系统设计', category: 'ai', desc: '利用AI帮助设计复杂的TypeScript系统架构' },
  { path: 'OEBPS/attic/ai-assistance/debugging-help.xhtml', title: '用AI帮助调试', category: 'ai', desc: '使用AI辅助诊断和修复TypeScript错误' },
  { path: 'OEBPS/attic/ai-assistance/project-scaffolding.xhtml', title: '用AI搭建项目骨架', category: 'ai', desc: '利用AI生成TypeScript项目的基础结构和配置' },
  { path: 'OEBPS/attic/ai-assistance/code-generation.xhtml', title: '代码生成实践', category: 'ai', desc: '基于类型定义生成具体实现代码的AI协作流程' },
  
  // 秘密通道页面
  { path: 'OEBPS/secret-passages/configuration/advanced-options.xhtml', title: '高级编译器选项', category: 'secret', desc: 'TypeScript编译器高级配置选项的详细解析' },
  { path: 'OEBPS/secret-passages/type-philosophy.xhtml', title: '类型哲学', category: 'secret', desc: '类型系统背后的设计哲学和思想理念' },
  { path: 'OEBPS/secret-passages/advanced-patterns.xhtml', title: '高级设计模式', category: 'secret', desc: 'TypeScript高级设计模式和架构模式' },
  { path: 'OEBPS/secret-passages/performance-optimization.xhtml', title: '性能优化技巧', category: 'secret', desc: 'TypeScript代码性能优化和编译优化技巧' },
  { path: 'OEBPS/secret-passages/configuration/strict-mode.xhtml', title: '严格模式下的错误', category: 'secret', desc: 'TypeScript严格模式下的常见错误和注意事项' },
  
  // 房间和类页面
  { path: 'OEBPS/rooms/classes/complex-hierarchy.xhtml', title: '复杂的类继承体系', category: 'excited', desc: '设计复杂的TypeScript类继承体系和幽灵王朝' },
  { path: 'OEBPS/rooms/modules/large-project.xhtml', title: '大型项目模块设计', category: 'excited', desc: '组织复杂TypeScript代码的模块结构和项目设计' },
  
  // 非线性鬼屋页面
  { path: 'OEBPS/haunted-house/nonlinear/start-with-ghost.xhtml', title: '从幽灵开始建造鬼屋', category: 'excited', desc: '从定义幽灵类型开始构建鬼屋项目的非线性方法' },
  { path: 'OEBPS/haunted-house/nonlinear/start-with-rules.xhtml', title: '从规则开始建造鬼屋', category: 'excited', desc: '从定义鬼屋规则开始构建项目的非线性方法' },
  { path: 'OEBPS/haunted-house/nonlinear/start-with-error.xhtml', title: '从错误开始建造鬼屋', category: 'excited', desc: '从常见错误开始学习并构建鬼屋项目的非线性方法' },
  { path: 'OEBPS/haunted-house/nonlinear/start-with-ai.xhtml', title: '从AI开始建造鬼屋', category: 'excited', desc: '利用AI生成基础代码开始构建鬼屋项目的非线性方法' },
  
  // 鬼屋示例页面
  { path: 'OEBPS/haunted-house/examples/simple-haunt.xhtml', title: '简单出没鬼屋示例', category: 'excited', desc: '基础鬼屋项目的完整示例和代码实现' },
  { path: 'OEBPS/haunted-house/examples/complex-hierarchy.xhtml', title: '复杂层次鬼屋示例', category: 'excited', desc: '复杂继承体系的鬼屋项目示例' },
  { path: 'OEBPS/haunted-house/examples/dynamic-rules.xhtml', title: '动态规则鬼屋示例', category: 'excited', desc: '基于动态规则的鬼屋项目示例' },
  { path: 'OEBPS/haunted-house/examples/ai-generated.xhtml', title: 'AI生成的鬼屋示例', category: 'excited', desc: '完全由AI设计实现的鬼屋项目示例' },
];

async function fileExists(path) {
  try {
    await stat(path);
    return true;
  } catch {
    return false;
  }
}

async function generateMissingPages() {
  console.log('🔍 检查并生成缺失的页面...');
  let generatedCount = 0;
  let skippedCount = 0;
  
  for (const page of missingPages) {
    const exists = await fileExists(page.path);
    
    if (!exists) {
      console.log(`📝 生成: ${page.path}`);
      const html = generatePlaceholderHTML(page.title, page.path, page.category, page.desc);
      
      await mkdir(dirname(page.path), { recursive: true });
      await writeFile(page.path, html, 'utf-8');
      generatedCount++;
    } else {
      console.log(`⏭️  已存在: ${page.path}`);
      skippedCount++;
    }
  }
  
  console.log(`✅ 完成! 生成了 ${generatedCount} 个页面, 跳过了 ${skippedCount} 个已存在的页面。`);
}

// 运行生成器
if (import.meta.main) {
  generateMissingPages().catch(console.error);
}

export { generateMissingPages };