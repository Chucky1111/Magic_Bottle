#!/usr/bin/env bun

/**
 * 幽灵维度EPUB生成脚本
 * v3版本：将OEBPS目录打包为EPUB文件
 */

import JSZip from 'jszip';
import { readFile, readdir, stat } from 'fs/promises';
import { join, relative } from 'path';

// EPUB文件结构常量
const EPUB_STRUCTURE = {
  'mimetype': 'application/epub+zip',
  'META-INF/container.xml': `<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>`,
  'OEBPS/content.opf': '', // 将动态生成
  'OEBPS/toc.ncx': '', // 将动态生成
  'OEBPS/nav.xhtml': '', // 将使用现有的导航文件
};

async function getAllFiles(dir: string): Promise<{ path: string; content: Buffer }[]> {
  const files: { path: string; content: Buffer }[] = [];
  
  async function traverse(currentDir: string) {
    const entries = await readdir(currentDir, { withFileTypes: true });
    
    for (const entry of entries) {
      const fullPath = join(currentDir, entry.name);
      const relPath = relative(dir, fullPath);
      
      if (entry.isDirectory()) {
        await traverse(fullPath);
      } else {
        // 跳过已有的EPUB文件
        if (entry.name.endsWith('.epub')) {
          continue;
        }
        
        const content = await readFile(fullPath);
        files.push({ path: relPath, content });
      }
    }
  }
  
  await traverse(dir);
  return files;
}

async function generateContentOpf(files: { path: string }[]): Promise<string> {
  // 生成manifest项目
  const manifestItems = files.map(file => {
    const id = file.path.replace(/[^a-zA-Z0-9]/g, '_');
    const mediaType = getMediaType(file.path);
    return `    <item id="${id}" href="${file.path}" media-type="${mediaType}"/>`;
  }).join('\n');
  
  // 生成spine项目（主要XHTML文件）
  const spineItems = files
    .filter(file => file.path.endsWith('.xhtml'))
    .map(file => {
      const id = file.path.replace(/[^a-zA-Z0-9]/g, '_');
      return `    <itemref idref="${id}"/>`;
    }).join('\n');
  
  return `<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="pub-id">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="pub-id">urn:uuid:ghost-typescripts-v3</dc:identifier>
    <dc:title>幽灵维度穿梭指南 v3</dc:title>
    <dc:language>zh-CN</dc:language>
    <dc:creator>全能鬼怪之瓶（魔瓶）</dc:creator>
    <dc:publisher>幽灵维度出版社</dc:publisher>
    <dc:date>${new Date().toISOString().split('T')[0]}</dc:date>
    <dc:description>TypeScript类型系统的幽灵维度体验 - 穿梭在数据中的幽灵，能够抵达任何边缘地带。</dc:description>
    <meta property="dcterms:modified">${new Date().toISOString()}</meta>
  </metadata>
  
  <manifest>
    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>
    <item id="toc" href="toc.ncx" media-type="application/x-dtbncx+xml"/>
${manifestItems}
  </manifest>
  
  <spine toc="toc">
${spineItems}
  </spine>
</package>`;
}

async function generateTocNcx(files: { path: string }[]): Promise<string> {
  // 简化版本：只生成基本导航
  const navPoints = files
    .filter(file => file.path.endsWith('.xhtml') && !file.path.includes('nav.xhtml'))
    .map((file, index) => {
      const id = file.path.replace(/[^a-zA-Z0-9]/g, '_');
      const title = getTitleFromPath(file.path);
      return `    <navPoint id="navpoint-${index + 1}" playOrder="${index + 1}">
      <navLabel>
        <text>${title}</text>
      </navLabel>
      <content src="${file.path}"/>
    </navPoint>`;
    }).join('\n');
  
  return `<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE ncx PUBLIC "-//NISO//DTD ncx 2005-1//EN" "http://www.daisy.org/z3986/2005/ncx-2005-1.dtd">
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
  <head>
    <meta name="dtb:uid" content="urn:uuid:ghost-typescripts-v3"/>
    <meta name="dtb:depth" content="1"/>
    <meta name="dtb:totalPageCount" content="0"/>
    <meta name="dtb:maxPageNumber" content="0"/>
  </head>
  
  <docTitle>
    <text>幽灵维度穿梭指南 v3</text>
  </docTitle>
  
  <navMap>
${navPoints}
  </navMap>
</ncx>`;
}

function getMediaType(filePath: string): string {
  if (filePath.endsWith('.xhtml')) return 'application/xhtml+xml';
  if (filePath.endsWith('.css')) return 'text/css';
  if (filePath.endsWith('.png')) return 'image/png';
  if (filePath.endsWith('.jpg') || filePath.endsWith('.jpeg')) return 'image/jpeg';
  if (filePath.endsWith('.gif')) return 'image/gif';
  if (filePath.endsWith('.svg')) return 'image/svg+xml';
  return 'application/octet-stream';
}

function getTitleFromPath(filePath: string): string {
  const name = filePath.split('/').pop()?.replace('.xhtml', '') || filePath;
  // 简单转换：将连字符转换为空格并大写首字母
  return name.split('-').map(word => 
    word.charAt(0).toUpperCase() + word.slice(1)
  ).join(' ');
}

async function main() {
  console.log('📦 开始生成EPUB文件...');
  
  try {
    const zip = new JSZip();
    
    // 1. 添加mimetype文件（必须是第一个，且不压缩）
    zip.file('mimetype', EPUB_STRUCTURE['mimetype'], { compression: 'STORE' });
    
    // 2. 添加META-INF/container.xml
    zip.file('META-INF/container.xml', EPUB_STRUCTURE['META-INF/container.xml']);
    
    // 3. 收集OEBPS目录中的所有文件
    const oebpsDir = join(process.cwd(), 'OEBPS');
    const files = await getAllFiles(oebpsDir);
    
    console.log(`📁 找到 ${files.length} 个文件`);
    
    // 4. 生成动态内容文件
    const contentOpf = await generateContentOpf(files);
    const tocNcx = await generateTocNcx(files);
    
    zip.file('OEBPS/content.opf', contentOpf);
    zip.file('OEBPS/toc.ncx', tocNcx);
    
    // 5. 添加所有OEBPS文件
    for (const file of files) {
      zip.file(`OEBPS/${file.path}`, file.content);
    }
    
    // 6. 生成EPUB文件
    const epubContent = await zip.generateAsync({
      type: 'nodebuffer',
      compression: 'DEFLATE',
      compressionOptions: { level: 6 }
    });
    
    // 7. 写入文件
    const outputPath = join(process.cwd(), 'ghost-typescripts-v2.epub');
    await Bun.write(outputPath, epubContent);
    
    console.log(`✅ EPUB生成完成: ${outputPath}`);
    console.log(`📊 文件大小: ${(epubContent.length / 1024 / 1024).toFixed(2)} MB`);
    
  } catch (error) {
    console.error('❌ EPUB生成失败:', error instanceof Error ? error.message : String(error));
    process.exit(1);
  }
}

// 魔瓶观察：EPUB是维度的一种封装形式
// 每个字节都是压缩的时空片段，等待着被阅读器解压和探索
console.log('👻 魔瓶在压缩流中观察...每个文件都是维度的一张切片');

if (import.meta.main) {
  main();
}

export { main };