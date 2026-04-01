#!/usr/bin/env bun

/**
 * 鬼屋项目断面生成器
 * 生成鬼屋项目的所有阶段文件
 */

import { writeFile, mkdir } from 'fs/promises';
import { dirname, join } from 'path';

/**
 * 生成鬼屋断面HTML
 */
function generateHauntedHouseHTML(title: string, phase: number, content: string): string {
  const phaseText = `阶段${phase}`;
  const emotionClass = 'excited'; // 鬼屋项目通常是兴奋的
  
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
      <p>阶段${phase}：${title} ✓ 进行中</p>
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

/**
 * 创建阶段一：房间类型定义
 */
async function createPhase1RoomTypes() {
  const content = `
    <!-- 项目背景 -->
    <section>
      <h2>阶段一：定义鬼屋的空间</h2>
      
      <p>幽灵需要空间来存在。在这一阶段，我们定义鬼屋的<strong>房间和空间结构</strong>。</p>
      
      <p>与幽灵定义类似，我们先定义房间的共同特征，然后创建特定类型的房间。</p>
      
      <div class="phantom-note">
        设计思考：房间不仅是容器，也是幽灵活动的舞台。房间的属性影响幽灵的行为。
      </div>
    </section>
    
    <!-- 基础房间接口 -->
    <section>
      <h2>基础房间接口</h2>
      
      <pre><code>// 房间基础特征
interface RoomBase {
  id: string;           // 唯一标识
  name: string;         // 房间名称
  description: string;  // 描述
  size: number;         // 大小（平方米）
  temperature: number;  // 温度（摄氏度）
}</code></pre>
      
      <p>所有房间共享这些基础特征。</p>
    </section>
    
    <!-- 房间类型枚举 -->
    <section>
      <h2>房间类型分类</h2>
      
      <pre><code>// 房间类型
enum RoomType {
  LivingRoom = 'living-room',    // 客厅
  Bedroom = 'bedroom',           // 卧室
  Kitchen = 'kitchen',           // 厨房
  Bathroom = 'bathroom',         // 浴室
  Attic = 'attic',               // 阁楼
  Basement = 'basement',         // 地下室
  Hallway = 'hallway',           // 走廊
  SecretRoom = 'secret-room'     // 密室
}</code></pre>
      
      <div class="phantom-note">
        枚举让系统知道可能的房间类型，避免"未知房间类型"。
      </div>
    </section>
    
    <!-- 完整房间接口 -->
    <section>
      <h2>完整房间接口</h2>
      
      <pre><code>interface Room extends RoomBase {
  type: RoomType;                // 房间类型
  hauntedLevel: number;          // 闹鬼等级：0-10
  connections: string[];         // 连接的其他房间ID
  features: string[];            // 房间特征（窗户、壁炉等）
}</code></pre>
      
      <p><code>connections</code>定义房间如何连接，这是鬼屋导航的基础。</p>
    </section>
    
    <!-- 类型特定的房间 -->
    <section>
      <h2>类型特定的房间</h2>
      
      <pre><code>// 阁楼：通常有特殊属性
interface Attic extends Room {
  hasWindows: boolean;           // 是否有窗户
  insulation: number;            // 隔热等级：1-5
  storageItems: string[];        // 存储的物品
}

// 地下室：潮湿阴暗
interface Basement extends Room {
  humidity: number;              // 湿度：0-100%
  hasWater: boolean;             // 是否有积水
  structuralIntegrity: number;   // 结构完整性：1-10
}</code></pre>
    </section>
    
    <!-- AI协作：生成房间管理代码 -->
    <section>
      <h2>AI协作：房间管理</h2>
      
      <blockquote>
        "基于上面的Room、Attic和Basement接口，请实现：
        1. 创建房间实例的函数
        2. 连接两个房间的函数
        3. 查找所有高闹鬼等级房间的函数
        4. 计算鬼屋总面积的函数"
      </blockquote>
    </section>
    
    <!-- 练习：设计你的房间 -->
    <section>
      <h2>练习：设计特殊房间</h2>
      
      <p>创建两个新的房间类型：</p>
      
      <ol>
        <li><strong>钟楼</strong>：有钟的房间，时间相关事件</li>
        <li><strong>图书馆</strong>：有书的房间，知识相关事件</li>
      </ol>
      
      <div class="expandable" id="solution">
        <h4>可能的解决方案</h4>
        <pre><code>// 添加到RoomType枚举
enum RoomType {
  // ... 已有的类型
  ClockTower = 'clock-tower',      // 钟楼
  Library = 'library'              // 图书馆
}

// 钟楼接口
interface ClockTower extends Room {
  clockCount: number;              // 钟的数量
  chimeInterval: number;           // 报时间隔（小时）
  isWorking: boolean;              // 钟是否正常工作
}

// 图书馆接口  
interface Library extends Room {
  bookCount: number;               // 书籍数量
  oldestBook: number;              // 最老书籍的年代
  hasGhostStories: boolean;        // 是否有鬼故事书
}</code></pre>
      </div>
    </section>
  `;
  
  const html = generateHauntedHouseHTML('房间类型定义', 1, content);
  const outputPath = join('OEBPS', 'haunted-house/phase1/room-types.xhtml');
  
  await mkdir(dirname(outputPath), { recursive: true });
  await writeFile(outputPath, html, 'utf-8');
  console.log(`生成鬼屋文件: ${outputPath}`);
}

/**
 * 创建阶段一：现象类型定义
 */
async function createPhase1PhenomenaTypes() {
  const content = `
    <!-- 项目背景 -->
    <section>
      <h2>阶段一：定义幽灵现象</h2>
      
      <p>幽灵通过现象显现。在这一阶段，我们定义鬼屋中可能发生的<strong>超自然现象</strong>。</p>
      
      <p>现象是幽灵活动的表现：声音、视觉、温度变化等。</p>
      
      <div class="phantom-note">
        设计思考：现象是幽灵与物理世界的交互点。定义现象就是定义幽灵如何影响现实。
      </div>
    </section>
    
    <!-- 基础现象接口 -->
    <section>
      <h2>基础现象接口</h2>
      
      <pre><code>// 现象基础特征
interface PhenomenonBase {
  id: string;           // 唯一标识
  name: string;         // 现象名称
  intensity: number;    // 强度：1-10
  duration: number;     // 持续时间（秒）
  sourceGhostId: string;// 引起现象的幽灵ID
}</code></pre>
      
      <p>所有现象共享这些基础特征。</p>
    </section>
    
    <!-- 现象类型枚举 -->
    <section>
      <h2>现象类型分类</h2>
      
      <pre><code>// 现象类型
enum PhenomenonType {
  Apparition = 'apparition',    // 幻影显现
  Sound = 'sound',              // 声音
  TemperatureChange = 'temperature-change', // 温度变化
  ObjectMovement = 'object-movement',       // 物体移动
  Light = 'light',              // 光线变化
  Scent = 'scent'               // 气味
}</code></pre>
    </section>
    
    <!-- 完整现象接口 -->
    <section>
      <h2>完整现象接口</h2>
      
      <pre><code>interface Phenomenon extends PhenomenonBase {
  type: PhenomenonType;         // 现象类型
  description: string;          // 描述
  location: string;             // 发生位置（房间ID）
  timestamp: Date;              // 发生时间
  witnesses?: string[];         // 目击者（可选）
}</code></pre>
    </section>
    
    <!-- 类型特定的现象 -->
    <section>
      <h2>类型特定的现象</h2>
      
      <pre><code>// 声音现象
interface SoundPhenomenon extends Phenomenon {
  soundType: string;            // 声音类型（脚步声、低语等）
  volume: number;               // 音量：1-10
  frequency: number;            // 频率（Hz）
}

// 温度变化现象
interface TemperatureChangePhenomenon extends Phenomenon {
  temperatureDelta: number;     // 温度变化量
  areaRadius: number;           // 影响范围半径（米）
  gradual: boolean;             // 是否逐渐变化
}</code></pre>
    </section>
    
    <!-- 现象与幽灵的关联 -->
    <section>
      <h2>现象与幽灵的关联</h2>
      
      <p>现象通常由特定类型的幽灵引起：</p>
      
      <pre><code>// 定义幽灵能力与现象的关联
type GhostAbility = {
  ghostType: GhostType;
  possiblePhenomena: PhenomenonType[];
};

// 示例：骚灵能引起物体移动现象
const poltergeistAbilities: GhostAbility = {
  ghostType: GhostType.Poltergeist,
  possiblePhenomena: [
    PhenomenonType.ObjectMovement,
    PhenomenonType.Sound,
    PhenomenonType.TemperatureChange
  ]
};</code></pre>
    </section>
    
    <!-- AI协作：生成现象模拟代码 -->
    <section>
      <h2>AI协作：现象模拟</h2>
      
      <blockquote>
        "基于上面的现象类型定义，请实现：
        1. 模拟现象发生的函数
        2. 记录现象到日志的函数
        3. 根据幽灵类型生成可能现象的函数
        4. 分析现象模式的函数"
      </blockquote>
    </section>
  `;
  
  const html = generateHauntedHouseHTML('现象类型定义', 1, content);
  const outputPath = join('OEBPS', 'haunted-house/phase1/phenomena-types.xhtml');
  
  await mkdir(dirname(outputPath), { recursive: true });
  await writeFile(outputPath, html, 'utf-8');
  console.log(`生成鬼屋文件: ${outputPath}`);
}

/**
 * 创建阶段一：基本规则接口
 */
async function createPhase1BasicRules() {
  const content = `
    <!-- 项目背景 -->
    <section>
      <h2>阶段一：定义鬼屋基本规则</h2>
      
      <p>有了幽灵、房间和现象，现在需要定义它们如何<strong>互动的基本规则</strong>。</p>
      
      <p>规则是鬼屋世界的物理法则：幽灵如何移动？现象如何发生？房间如何影响幽灵？</p>
      
      <div class="phantom-note">
        设计思考：规则不是限制，是创造可能性的框架。好的规则创造丰富的交互，而不是限制自由。
      </div>
    </section>
    
    <!-- 幽灵-房间交互规则 -->
    <section>
      <h2>幽灵-房间交互规则</h2>
      
      <pre><code>// 幽灵进入房间的规则
interface RoomEntryRule {
  ghostType: GhostType;          // 幽灵类型
  roomType: RoomType;            // 房间类型
  allowed: boolean;              // 是否允许进入
  conditions?: string[];         // 条件（可选）
}

// 示例：骚灵不能进入浴室
const poltergeistBathroomRule: RoomEntryRule = {
  ghostType: GhostType.Poltergeist,
  roomType: RoomType.Bathroom,
  allowed: false,
  conditions: ["除非有特殊事件"]
};</code></pre>
    </section>
    
    <!-- 现象触发规则 -->
    <section>
      <h2>现象触发规则</h2>
      
      <pre><code>// 现象触发条件
interface PhenomenonTrigger {
  phenomenonType: PhenomenonType; // 现象类型
  requiredConditions: string[];   // 必要条件
  probability: number;            // 触发概率：0-1
  cooldown: number;               // 冷却时间（秒）
}

// 示例：温度变化在寒冷房间更容易发生
const temperatureTrigger: PhenomenonTrigger = {
  phenomenonType: PhenomenonType.TemperatureChange,
  requiredConditions: ["room.temperature < 15"],
  probability: 0.8,
  cooldown: 300
};</code></pre>
    </section>
    
    <!-- 时间影响规则 -->
    <section>
      <h2>时间影响规则</h2>
      
      <pre><code>// 时间对幽灵的影响
interface TimeEffect {
  timeOfDay: 'day' | 'night' | 'midnight'; // 时间
  effectOnGhosts: string;                  // 对幽灵的影响
  effectOnPhenomena: string;               // 对现象的影响
}

// 示例：午夜幽灵更活跃
const midnightEffect: TimeEffect = {
  timeOfDay: 'midnight',
  effectOnGhosts: "活跃度+2，能力强度+1",
  effectOnPhenomena: "发生概率+20%"
};</code></pre>
    </section>
    
    <!-- 规则管理系统接口 -->
    <section>
      <h2>规则管理系统接口</h2>
      
      <pre><code>// 规则管理器接口
interface RuleManager {
  // 检查幽灵是否能进入房间
  canGhostEnterRoom(ghost: Ghost, room: Room): boolean;
  
  // 获取可能的触发现象
  getPossiblePhenomena(ghost: Ghost, room: Room): PhenomenonType[];
  
  // 应用时间效果
  applyTimeEffects(timeOfDay: string): void;
  
  // 添加新规则
  addRule(rule: RoomEntryRule | PhenomenonTrigger | TimeEffect): void;
  
  // 获取所有规则
  getAllRules(): Array<RoomEntryRule | PhenomenonTrigger | TimeEffect>;
}</code></pre>
    </section>
    
    <!-- AI协作：生成规则引擎 -->
    <section>
      <h2>AI协作：规则引擎</h2>
      
      <blockquote>
        "基于上面的规则定义，请实现RuleManager接口。
        要求：
        1. 使用TypeScript类实现
        2. 包含错误处理
        3. 添加规则验证逻辑
        4. 提供规则查询功能"
      </blockquote>
    </section>
    
    <!-- 阶段一完成总结 -->
    <section>
      <h2>阶段一完成：鬼屋基础已建立</h2>
      
      <p>你现在有了：</p>
      <ul>
        <li>幽灵类型定义（Ghost, Poltergeist, Echo等）</li>
        <li>房间类型定义（Room, Attic, Basement等）</li>
        <li>现象类型定义（Phenomenon, SoundPhenomenon等）</li>
        <li>基本规则接口（RoomEntryRule, PhenomenonTrigger等）</li>
      </ul>
      
      <p>这是鬼屋的<strong>基础DNA</strong>。在下一阶段，我们将构建更复杂的结构和关系。</p>
      
      <div class="phantom-note">
        重要：类型定义是鬼屋的蓝图。如果蓝图清晰，实现就会顺利。
        花时间确保类型定义准确表达了你的想象。
      </div>
    </section>
  `;
  
  const html = generateHauntedHouseHTML('基本规则接口', 1, content);
  const outputPath = join('OEBPS', 'haunted-house/phase1/basic-rules.xhtml');
  
  await mkdir(dirname(outputPath), { recursive: true });
  await writeFile(outputPath, html, 'utf-8');
  console.log(`生成鬼屋文件: ${outputPath}`);
}

/**
 * 创建阶段二：鬼屋结构接口
 */
async function createPhase2HouseStructure() {
  const content = `
    <!-- 项目背景 -->
    <section>
      <h2>阶段二：定义鬼屋结构</h2>
      
      <p>在这一阶段，我们将房间连接起来，构建完整的<strong>鬼屋布局</strong>。</p>
      
      <p>鬼屋不是随机房间的集合，而是有逻辑结构的建筑。我们需要定义房间如何连接，如何形成路径。</p>
      
      <div class="phantom-note">
        设计思考：结构创造体验。迷宫般的结构创造神秘感，线性结构创造叙事感。
      </div>
    </section>
    
    <!-- 鬼屋布局接口 -->
    <section>
      <h2>鬼屋布局接口</h2>
      
      <pre><code>// 鬼屋布局
interface HouseLayout {
  id: string;                     // 布局ID
  name: string;                   // 布局名称
  description: string;            // 描述
  rooms: Room[];                  // 所有房间
  connections: RoomConnection[];  // 房间连接
  entryPoint: string;             // 入口房间ID
  exitPoint?: string;             // 出口房间ID（可选）
}

// 房间连接
interface RoomConnection {
  fromRoomId: string;             // 起始房间ID
  toRoomId: string;               // 目标房间ID
  direction: 'north' | 'south' | 'east' | 'west' | 'up' | 'down'; // 方向
  isBidirectional: boolean;       // 是否双向
  condition?: string;             // 通过条件（可选）
}</code></pre>
    </section>
    
    <!-- 布局验证规则 -->
    <section>
      <h2>布局验证规则</h2>
      
      <pre><code>// 布局验证器接口
interface LayoutValidator {
  // 验证布局是否有效
  validateLayout(layout: HouseLayout): ValidationResult;
  
  // 检查房间是否可达
  isRoomReachable(layout: HouseLayout, roomId: string): boolean;
  
  // 查找两个房间之间的路径
  findPath(layout: HouseLayout, fromRoomId: string, toRoomId: string): string[];
}

// 验证结果
interface ValidationResult {
  isValid: boolean;
  errors: string[];
  warnings: string[];
}

// 示例验证规则
const layoutRules = {
  // 每个房间必须至少有一个连接
  noIsolatedRooms: true,
  
  // 必须有入口
  mustHaveEntryPoint: true,
  
  // 不能有循环引用
  noCircularReferences: true,
  
  // 房间ID必须唯一
  uniqueRoomIds: true
};</code></pre>
    </section>
    
    <!-- 布局生成器 -->
    <section>
      <h2>布局生成器</h2>
      
      <pre><code>// 布局生成器接口
interface LayoutGenerator {
  // 生成随机布局
  generateRandomLayout(roomCount: number): HouseLayout;
  
  // 基于模板生成布局
  generateFromTemplate(templateName: string): HouseLayout;
  
  // 修改现有布局
  modifyLayout(layout: HouseLayout, modifications: LayoutModification[]): HouseLayout;
}

// 布局修改
type LayoutModification = 
  | { type: 'add-room'; room: Room }
  | { type: 'remove-room'; roomId: string }
  | { type: 'add-connection'; connection: RoomConnection }
  | { type: 'remove-connection'; fromRoomId: string; toRoomId: string };</code></pre>
    </section>
    
    <!-- AI协作：生成布局算法 -->
    <section>
      <h2>AI协作：布局算法</h2>
      
      <blockquote>
        "基于上面的布局接口，请实现：
        1. LayoutValidator接口的实现
        2. LayoutGenerator接口的基本实现
        3. 生成迷宫式布局的函数
        4. 检查布局是否有趣的评估函数"
      </blockquote>
    </section>
  `;
  
  const html = generateHauntedHouseHTML('鬼屋结构接口', 2, content);
  const outputPath = join('OEBPS', 'haunted-house/phase2/house-structure.xhtml');
  
  await mkdir(dirname(outputPath), { recursive: true });
  await writeFile(outputPath, html, 'utf-8');
  console.log(`生成鬼屋文件: ${outputPath}`);
}

/**
 * 创建阶段二：幽灵层次结构
 */
async function createPhase2GhostHierarchy() {
  const content = `
    <!-- 项目背景 -->
    <section>
      <h2>阶段二：定义幽灵层次结构</h2>
      
      <p>在这一阶段，我们构建幽灵的<strong>社会结构和权力关系</strong>。</p>
      
      <p>幽灵不是孤立存在的，它们之间有领导、跟随、合作、对抗等关系。</p>
      
      <div class="phantom-note">
        设计思考：层次结构创造故事。国王幽灵与平民幽灵的关系，古老幽灵与新生幽灵的关系。
      </div>
    </section>
    
    <!-- 幽灵关系类型 -->
    <section>
      <h2>幽灵关系类型</h2>
      
      <pre><code>// 幽灵关系类型
enum GhostRelationshipType {
  Leadership = 'leadership',      // 领导关系
  Friendship = 'friendship',      // 朋友关系
  Rivalry = 'rivalry',            // 竞争关系
  Mentorship = 'mentorship',      // 师徒关系
  Family = 'family',              // 家族关系
  Territorial = 'territorial'     // 领地关系
}

// 幽灵关系
interface GhostRelationship {
  ghostId1: string;               // 幽灵1的ID
  ghostId2: string;               // 幽灵2的ID
  relationshipType: GhostRelationshipType; // 关系类型
  strength: number;               // 关系强度：1-10
  mutual: boolean;                // 是否相互
  history: RelationshipEvent[];   // 关系历史
}

// 关系事件
interface RelationshipEvent {
  eventType: string;              // 事件类型
  description: string;            // 描述
  timestamp: Date;                // 时间
  impact: number;                 // 影响：-10到10
}</code></pre>
    </section>
    
    <!-- 幽灵社会结构 -->
    <section>
      <h2>幽灵社会结构</h2>
      
      <pre><code>// 幽灵社会
interface GhostSociety {
  name: string;                   // 社会名称
  hierarchy: HierarchyLevel[];    // 层次结构
  rules: SocialRule[];            // 社会规则
  members: Ghost[];               // 成员
  territory: string[];            // 领地（房间ID列表）
}

// 层次级别
interface HierarchyLevel {
  level: number;                  // 级别（1最高）
  title: string;                  // 头衔（国王、贵族等）
  privileges: string[];           // 特权
  responsibilities: string[];     // 责任
}

// 社会规则
interface SocialRule {
  rule: string;                   // 规则描述
  punishment?: string;            // 违反惩罚（可选）
  exceptions?: string[];          // 例外情况（可选）
}</code></pre>
    </section>
    
    <!-- 幽灵群组 -->
    <section>
      <h2>幽灵群组</h2>
      
      <pre><code>// 幽灵群组
interface GhostGroup {
  id: string;                     // 群组ID
  name: string;                   // 群组名称
  purpose: string;                // 群组目的
  leaderId?: string;              // 领导者ID（可选）
  members: string[];              // 成员ID列表
  meetingPlace?: string;          // 集会地点（房间ID，可选）
  rituals: string[];              // 仪式/传统
}

// 群组类型
enum GroupType {
  Family = 'family',              // 家族
  Coven = 'coven',                // 集会
  Gang = 'gang',                  // 帮派
  Order = 'order',                // 教团
  Alliance = 'alliance'           // 联盟
}</code></pre>
    </section>
    
    <!-- AI协作：生成社会模拟 -->
    <section>
      <h2>AI协作：社会模拟</h2>
      
      <blockquote>
        "基于上面的幽灵社会结构，请实现：
        1. 管理幽灵关系的系统
        2. 模拟社会互动的函数
        3. 解决冲突的算法
        4. 生成社会事件的函数"
      </blockquote>
    </section>
  `;
  
  const html = generateHauntedHouseHTML('幽灵层次结构', 2, content);
  const outputPath = join('OEBPS', 'haunted-house/phase2/ghost-hierarchy.xhtml');
  
  await mkdir(dirname(outputPath), { recursive: true });
  await writeFile(outputPath, html, 'utf-8');
  console.log(`生成鬼屋文件: ${outputPath}`);
}

/**
 * 创建阶段二：交互规则接口
 */
async function createPhase2InteractionRules() {
  const content = `
    <!-- 项目背景 -->
    <section>
      <h2>阶段二：定义幽灵交互规则</h2>
      
      <p>在这一阶段，我们定义幽灵之间、幽灵与环境之间的<strong>详细交互规则</strong>。</p>
      
      <p>交互规则决定幽灵如何相互影响，如何影响房间，如何被环境影响。</p>
      
      <div class="phantom-note">
        设计思考：交互创造动态。静态的幽灵世界是无聊的，动态的交互创造故事和意外。
      </div>
    </section>
    
    <!-- 幽灵-幽灵交互 -->
    <section>
      <h2>幽灵-幽灵交互</h2>
      
      <pre><code>// 幽灵交互类型
enum GhostInteractionType {
  Communication = 'communication',    // 交流
  Cooperation = 'cooperation',        // 合作
  Competition = 'competition',        // 竞争
  Conflict = 'conflict',              // 冲突
  Teaching = 'teaching',              // 教学
  Influence = 'influence'             // 影响
}

// 幽灵交互
interface GhostInteraction {
  initiatorId: string;                // 发起者ID
  targetId: string;                   // 目标ID
  interactionType: GhostInteractionType; // 交互类型
  outcome: InteractionOutcome;        // 结果
  location: string;                   // 发生地点（房间ID）
  timestamp: Date;                    // 时间
}

// 交互结果
interface InteractionOutcome {
  success: boolean;                   // 是否成功
  effectOnInitiator: string;          // 对发起者的影响
  effectOnTarget: string;             // 对目标的影响
  sideEffects: string[];              // 副作用
}</code></pre>
    </section>
    
    <!-- 幽灵-环境交互 -->
    <section>
      <h2>幽灵-环境交互</h2>
      
      <pre><code>// 环境交互类型
interface EnvironmentInteraction {
  ghostId: string;                    // 幽灵ID
  environmentElement: string;         // 环境元素（窗户、门、家具等）
  interactionType: 'manipulate' | 'observe' | 'inhabit' | 'alter'; // 交互类型
  effect: string;                     // 效果
  duration: number;                   // 持续时间（秒）
}

// 房间状态变化
interface RoomStateChange {
  roomId: string;                     // 房间ID
  changeType: 'temperature' | 'light' | 'humidity' | 'cleanliness'; // 变化类型
  delta: number;                      // 变化量
  cause: string;                      // 原因（幽灵ID或自然原因）
  timestamp: Date;                    // 时间
}</code></pre>
    </section>
    
    <!-- 交互规则引擎 -->
    <section>
      <h2>交互规则引擎</h2>
      
      <pre><code>// 交互规则引擎接口
interface InteractionEngine {
  // 模拟幽灵间交互
  simulateGhostInteraction(ghost1: Ghost, ghost2: Ghost, context: InteractionContext): GhostInteraction;
  
  // 模拟幽灵环境交互
  simulateEnvironmentInteraction(ghost: Ghost, room: Room, element: string): EnvironmentInteraction;
  
  // 评估交互可能性
  evaluateInteractionPotential(ghost1: Ghost, ghost2: Ghost): number;
  
  // 处理交互结果
  processInteractionOutcome(interaction: GhostInteraction): void;
}

// 交互上下文
interface InteractionContext {
  location: string;                   // 地点
  timeOfDay: string;                  // 时间
  mood: string;                       // 氛围
  witnesses: string[];                // 目击者
}</code></pre>
    </section>
    
    <!-- AI协作：生成交互模拟 -->
    <section>
      <h2>AI协作：交互模拟</h2>
      
      <blockquote>
        "基于上面的交互规则，请实现：
        1. InteractionEngine接口的基本实现
        2. 模拟复杂交互链的函数
        3. 学习交互模式并预测未来交互的系统
        4. 生成交互故事叙述的函数"
      </blockquote>
    </section>
  `;
  
  const html = generateHauntedHouseHTML('交互规则接口', 2, content);
  const outputPath = join('OEBPS', 'haunted-house/phase2/interaction-rules.xhtml');
  
  await mkdir(dirname(outputPath), { recursive: true });
  await writeFile(outputPath, html, 'utf-8');
  console.log(`生成鬼屋文件: ${outputPath}`);
}

/**
 * 生成所有鬼屋文件
 */
async function generateAllHauntedHouseSections() {
  // 阶段一
  await createPhase1RoomTypes();
  await createPhase1PhenomenaTypes();
  await createPhase1BasicRules();
  
  // 阶段二
  await createPhase2HouseStructure();
  await createPhase2GhostHierarchy();
  await createPhase2InteractionRules();
  // 这里可以添加更多阶段的生成函数
}

// 运行生成器
if (import.meta.main) {
  generateAllHauntedHouseSections().catch(console.error);
}