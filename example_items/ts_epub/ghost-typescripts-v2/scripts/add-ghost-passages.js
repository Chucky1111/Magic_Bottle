#!/usr/bin/env bun

/**
 * 为所有概念断面添加幽灵通道（ghost-passages）部分
 */

import { readFile, writeFile, mkdir } from 'fs/promises';
import { dirname, join, relative, basename } from 'path';
import { glob } from 'glob';

// 断面目录
const sectionDirs = [
  'OEBPS/hallways/types/*.xhtml',
  'OEBPS/hallways/interfaces/*.xhtml',
  'OEBPS/rooms/generics/*.xhtml',
  'OEBPS/rooms/classes/*.xhtml',
  'OEBPS/rooms/modules/*.xhtml',
  'OEBPS/secret-passages/configuration/*.xhtml',
  'OEBPS/attic/ai-assistance/*.xhtml'
];

// 排除索引文件
const excludePatterns = ['**/index.xhtml', '**/toc-*.xhtml'];

// 幽灵通道HTML模板
function generateGhostPassages(filePath) {
  // 根据文件路径确定相关链接
  const relativePath = relative('OEBPS', filePath);
  const category = dirname(relativePath).split('/')[0];
  
  // 使用绝对路径，避免相对路径计算问题
  const passages = [
    { text: '情绪维度导航', href: `/toc-emotion.xhtml` },
    { text: '意图维度路径', href: `/toc-intent.xhtml` },
    { text: '鬼屋项目实践', href: `/toc-haunted-house.xhtml` },
    { text: '返回概念维度', href: `/toc-concepts.xhtml` }
  ];
  
  // 添加特定类别的相关链接（使用绝对路径避免重复拼接）
  if (category === 'hallways') {
    const subcat = dirname(relativePath).split('/')[1];
    if (subcat === 'types') {
      passages.push({ text: '接口与类型别名', href: '/hallways/interfaces/index.xhtml' });
      passages.push({ text: '泛型与高级类型', href: '/rooms/generics/index.xhtml' });
    } else if (subcat === 'interfaces') {
      passages.push({ text: '类型系统基础', href: '/hallways/types/index.xhtml' });
      passages.push({ text: '类与面向对象', href: '/rooms/classes/index.xhtml' });
    }
  } else if (category === 'rooms') {
    const subcat = dirname(relativePath).split('/')[1];
    if (subcat === 'generics') {
      passages.push({ text: '类型系统基础', href: '/hallways/types/index.xhtml' });
      passages.push({ text: '接口基础', href: '/hallways/interfaces/index.xhtml' });
    } else if (subcat === 'classes') {
      passages.push({ text: '接口基础', href: '/hallways/interfaces/index.xhtml' });
      passages.push({ text: '模块系统', href: '/rooms/modules/index.xhtml' });
    } else if (subcat === 'modules') {
      passages.push({ text: '类与面向对象', href: '/rooms/classes/index.xhtml' });
      passages.push({ text: '编译器配置', href: '/secret-passages/configuration/index.xhtml' });
    }
  } else if (category === 'secret-passages') {
    passages.push({ text: '模块系统', href: '/rooms/modules/index.xhtml' });
    passages.push({ text: 'AI辅助开发', href: '/attic/ai-assistance/index.xhtml' });
  } else if (category === 'attic') {
    passages.push({ text: '编译器配置', href: '/secret-passages/configuration/index.xhtml' });
    passages.push({ text: '鬼屋项目实践', href: '/toc-haunted-house.xhtml' });
  }
  
  return `
    <!-- 幽灵通道 -->
    <nav class="ghost-passages">
      <h3>穿梭到其他维度</h3>
      <ul>
        ${passages.map(p => `<li><a href="${p.href}">${p.text}</a></li>`).join('\n        ')}
      </ul>
    </nav>
  `;
}

async function processFile(filePath) {
  try {
    console.log(`处理: ${filePath}`);
    
    let content = await readFile(filePath, 'utf-8');
    
    // 查找ghost-passages部分的开始和结束
    const ghostPassagesStart = '<!-- 幽灵通道 -->';
    const ghostPassagesEnd = '</nav>';
    const startIndex = content.indexOf(ghostPassagesStart);
    
    const ghostPassagesHTML = generateGhostPassages(filePath);
    
    if (startIndex !== -1) {
      // 找到现有部分，查找结束位置
      const endIndex = content.indexOf(ghostPassagesEnd, startIndex);
      if (endIndex !== -1) {
        // 替换现有部分
        content = content.slice(0, startIndex) + 
                  ghostPassagesHTML + 
                  content.slice(endIndex + ghostPassagesEnd.length);
        console.log(`  已更新幽灵通道`);
      } else {
        // 没有找到结束标签，在魔瓶的最后观察前插入
        console.log(`  找到幽灵通道开始但未找到结束，将在魔瓶的最后观察前插入`);
        const lastObservationMarker = '<!-- 魔瓶的最后观察 -->';
        const lastObservationIndex = content.indexOf(lastObservationMarker);
        if (lastObservationIndex !== -1) {
          content = content.slice(0, lastObservationIndex) + 
                    ghostPassagesHTML + 
                    content.slice(lastObservationIndex);
          console.log(`  已添加幽灵通道`);
        } else {
          console.log(`  未找到魔瓶的最后观察标记，跳过`);
          return;
        }
      }
    } else {
      // 没有现有部分，在魔瓶的最后观察前插入
      const lastObservationMarker = '<!-- 魔瓶的最后观察 -->';
      const lastObservationIndex = content.indexOf(lastObservationMarker);
      
      if (lastObservationIndex === -1) {
        console.log(`  未找到魔瓶的最后观察标记，跳过`);
        return;
      }
      
      content = content.slice(0, lastObservationIndex) + 
                ghostPassagesHTML + 
                content.slice(lastObservationIndex);
      console.log(`  已添加幽灵通道`);
    }
    
    await writeFile(filePath, content, 'utf-8');
  } catch (error) {
    console.error(`  处理文件失败: ${filePath}`, error);
  }
}

async function main() {
  console.log('开始为概念断面添加幽灵通道...');
  
  for (const pattern of sectionDirs) {
    try {
      const files = await glob(pattern, { ignore: excludePatterns });
      
      if (!files) {
        console.log(`在${pattern}中找到0个文件 (files is null/undefined)`);
        continue;
      }
      
      if (!Array.isArray(files)) {
        console.log(`在${pattern}中找到非数组结果:`, typeof files);
        console.log('跳过此模式');
        continue;
      }
      
      console.log(`在${pattern}中找到${files.length}个文件`);
      
      if (files.length === 0) {
        console.log('  跳过空文件列表');
        continue;
      }
      
      for (const file of files) {
        await processFile(file);
      }
    } catch (error) {
      console.error(`处理模式${pattern}时出错: ${error instanceof Error ? error.message : String(error)}`);
    }
  }
  
  console.log('完成！');
}

// 运行
if (import.meta.main) {
  main().catch(console.error);
}