#!/usr/bin/env bun

/**
 * 幽灵维度断面生成器
 * v3版本：移除feeling块，增强魔瓶本质
 */

import type { Section, Emotion, Dimension } from '../src/types/section';
import { writeFile, mkdir } from 'fs/promises';
import { dirname, join } from 'path';

/**
 * 生成断面HTML
 */
function generateSectionHTML(section: Section): string {
  const { title, environment, introduction, phantomNotes = [], codeExamples = [], aiConversations = [], exercises = [], relatedSections = [] } = section;
  
  const emotionClass = environment.dominantEmotion;
  const visualDescription = environment.visualDescription;
  
  return `<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="zh-CN">
<head>
  <meta charset="UTF-8"/>
  <title>${title}</title>
  <link rel="stylesheet" href="../styles/ghost.css"/>
  <link rel="stylesheet" href="../styles/emotion.css"/>
  <link rel="stylesheet" href="../styles/ghost-dimension.css"/>
</head>
<body class="${emotionClass}">
  <!-- 魔瓶环境设定：${visualDescription} -->
  
  <div class="ghost-section">
    <div class="emotion-indicator">${emotionClass === 'confused' ? '困惑推荐' : emotionClass === 'curious' ? '好奇推荐' : emotionClass === 'excited' ? '兴奋推荐' : '挫败推荐'}</div>
    
    <h1>${title}</h1>
    
    ${phantomNotes.map(note => `<div class="phantom-note">${note.text}</div>`).join('\n    ')}
    
    ${introduction ? `<section><p>${introduction}</p></section>` : ''}
    
    ${codeExamples.map((example, i) => `
    <section>
      ${example.description ? `<h3>${example.description}</h3>` : ''}
      <pre><code>${example.code}</code></pre>
    </section>`).join('\n')}
    
    ${aiConversations.map((conv, i) => `
    <section class="ai-conversation">
      <h3>AI协作示例 ${i + 1}</h3>
      <div class="human-prompt">
        <strong>你的提示：</strong>
        <blockquote>${conv.human}</blockquote>
      </div>
      <div class="ai-response">
        <strong>AI可能生成：</strong>
        <pre><code>${conv.ai}</code></pre>
      </div>
      ${conv.analysis ? `<div class="analysis">${conv.analysis}</div>` : ''}
    </section>`).join('\n')}
    
    ${exercises.map((exercise, i) => `
    <section class="exercise">
      <h3>练习 ${i + 1}</h3>
      <p>${exercise.description}</p>
      ${exercise.hints ? `<div class="hints">提示：${exercise.hints.join(' ')}</div>` : ''}
      ${exercise.solution ? `<div class="expandable" id="solution-${i}"><h4>解决方案</h4><pre><code>${exercise.solution}</code></pre></div>` : ''}
    </section>`).join('\n')}
    
    ${relatedSections.length > 0 ? `
    <nav class="ghost-passages">
      <h3>穿梭到相关断面</h3>
      <ul>
        ${relatedSections.map(link => `<li><a href="${link.href}">${link.text}</a></li>`).join('\n        ')}
      </ul>
    </nav>` : ''}
    
    <!-- 魔瓶的最后观察 -->
    <div class="phantom-note" style="margin-top: 2em;">
      记住魔瓶的世界观："没有无法塑造的规则，只有无法表达的现状。"
      如果你觉得某个类型无法表达你的意图，不是类型的限制，是你还没找到正确的表达方式。
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

/**
 * 创建基本类型断面
 */
function createBasicTypesSection(): Section {
  return {
    id: 'basic-types',
    type: 'basic-types',
    title: '基本类型：思维的原子',
    path: 'hallways/types/basic-types.xhtml',
    environment: {
      dominantEmotion: 'curious',
      visualDescription: '微观世界中，发光的几何体在虚空中悬浮碰撞，产生新的复合形状',
      atmosphere: '对简单性的欣赏，复杂的现实由简单的元件构成'
    },
    introduction: '不要记忆<code>number</code>、<code>string</code>、<code>boolean</code>。感受它们：当你的意图是计算、测量、比较时用<code>number</code>；当你的意图是信息、标识、展示时用<code>string</code>；当你的意图是判断、决策、状态时用<code>boolean</code>。',
    phantomNotes: [
      { text: '幽灵观察：原子不是终点，是起点。类型系统的复杂性始于这些简单元件。' },
      { text: '问自己：我的意图是什么？然后选择对应的类型标签。' }
    ],
    codeExamples: [
      {
        code: `// 这不是代码，这是思维模式
let temperature: number = 23.5;          // 计算思维：测量
let ghostName: string = "卡斯珀";        // 信息思维：标识  
let isVisible: boolean = true;           // 判断思维：状态

// 向AI表达时，类型就是意图的明确表达
// AI看到': number'就知道："哦，这里需要数值计算"`,
        description: '意图的结晶'
      }
    ],
    dimension: 'concepts',
    keywords: ['基本类型', 'number', 'string', 'boolean', '意图'],
    createdAt: new Date(),
    updatedAt: new Date()
  };
}

/**
 * 创建类型推断断面
 */
function createTypeInferenceSection(): Section {
  return {
    id: 'type-inference',
    type: 'type-inference',
    title: '类型推断：暗示的艺术',
    path: 'hallways/types/type-inference.xhtml',
    environment: {
      dominantEmotion: 'curious',
      visualDescription: '无形的线索像发光的丝线从代码中延伸出来，在空中编织成类型形状',
      atmosphere: '发现隐藏模式的兴奋，理解系统在为你思考'
    },
    introduction: 'TypeScript不是强迫你写出所有类型，而是和你玩一个游戏："给我足够的信息，我会猜出你的意图。"类型推断就是这个游戏的核心机制。',
    phantomNotes: [
      { text: '幽灵观察：类型推断不是魔术，是模式识别。系统看到你写"23.5"，知道这是数字；看到你写"hello"，知道这是字符串。给它足够的上下文，它会理解更多。' },
      { text: '提示：当你不确定是否要写类型时，先不写。看看TypeScript能推断出什么，然后检查是否正确。' }
    ],
    codeExamples: [
      {
        code: `// 让类型推断为你工作
const ghostName = "卡斯珀";    // TypeScript知道这是string
const ghostAge = 150;          // TypeScript知道这是number
const isVisible = true;        // TypeScript知道这是boolean

// 更复杂的例子
const ghosts = ["卡斯珀", "维克多", "伊丽莎白"];  
// TypeScript知道这是string[]

function createGhost(name: string) {
  return { name, age: 150 };
}
// TypeScript知道这个函数的返回类型是{name: string, age: number}`,
        description: '让系统为你思考'
      }
    ],
    dimension: 'concepts',
    keywords: ['类型推断', '类型注解', '上下文', '模式识别'],
    createdAt: new Date(),
    updatedAt: new Date()
  };
}

/**
 * 创建any与unknown断面
 */
function createAnyUnknownSection(): Section {
  return {
    id: 'any-unknown',
    type: 'any-unknown',
    title: 'any与unknown：不确定性的两种表达',
    path: 'hallways/types/any-unknown.xhtml',
    environment: {
      dominantEmotion: 'confused',
      visualDescription: '两团朦胧的光雾在虚空中旋转，一团完全透明（any），一团半透明（unknown）',
      atmosphere: '理解两种不同的不确定性，从困惑到清晰'
    },
    introduction: '<code>any</code>说："我放弃，你随便弄。"<code>unknown</code>说："我不知道这是什么，但你必须先检查才能用。"这是不确定性的两种哲学。',
    phantomNotes: [
      { text: '幽灵观察：any是时间的穿越者——它来自JavaScript的过去，不在乎类型安全。unknown是时间的探索者——它承认未知，但要求谨慎。' },
      { text: '魔瓶建议：用unknown代替any。如果你必须用any，在旁边写上注释解释为什么。' }
    ],
    codeExamples: [
      {
        code: `// any：危险的自由
let dangerous: any = "hello";
dangerous = 42;          // 没问题，any可以是任何东西
dangerous.toUpperCase(); // 运行时错误！但是TypeScript不会警告你

// unknown：安全的未知
let safe: unknown = "hello";
safe = 42;               // 没问题，unknown也可以是任何东西
// safe.toUpperCase();   // 错误！必须先检查类型

// 使用unknown的正确方式
if (typeof safe === "string") {
  safe.toUpperCase();    // 现在安全了
}`,
        description: '两种不确定性的对比'
      }
    ],
    dimension: 'concepts',
    keywords: ['any', 'unknown', '类型安全', '不确定性'],
    createdAt: new Date(),
    updatedAt: new Date()
  };
}

/**
 * 创建数组与元组断面
 */
function createArraysTuplesSection(): Section {
  return {
    id: 'arrays-tuples',
    type: 'arrays-tuples',
    title: '数组与元组：集合与序列',
    path: 'hallways/types/arrays-tuples.xhtml',
    environment: {
      dominantEmotion: 'excited',
      visualDescription: '数组像一列相同的幽灵在排队，元组像一组各不相同的幽灵站成特定顺序',
      atmosphere: '发现如何组织数据的多种方式，感受到结构的优雅'
    },
    introduction: '数组是"许多相同的东西"，元组是"几个特定的东西，按特定顺序"。一个关注重复，一个关注结构。',
    phantomNotes: [
      { text: '幽灵观察：数组是合唱团——所有成员唱同样的部分。元组是重奏组——每个成员有特定的角色和顺序。' },
      { text: '提示：使用元组处理固定结构的数据，如坐标[x, y]、RGB颜色[r, g, b]、或数据库记录[id, name, age]。' }
    ],
    codeExamples: [
      {
        code: `// 数组：同质集合
const ghostNames: string[] = ["卡斯珀", "维克多", "伊丽莎白"];
const ghostAges: number[] = [150, 230, 75];

// 元组：固定结构的序列
const ghostPosition: [number, number] = [23.5, 45.2];  // x, y坐标
const ghostColor: [number, number, number] = [255, 0, 0];  // RGB

// 带有标签的元组（TypeScript 4.0+）
const ghostData: [name: string, age: number, isFriendly: boolean] = 
  ["卡斯珀", 150, true];`,
        description: '集合与序列的对比'
      }
    ],
    dimension: 'concepts',
    keywords: ['数组', '元组', '集合', '序列', '结构'],
    createdAt: new Date(),
    updatedAt: new Date()
  };
}

/**
 * 创建枚举断面
 */
function createEnumsSection(): Section {
  return {
    id: 'enums',
    type: 'enums',
    title: '枚举：命名的可能性',
    path: 'hallways/types/enums.xhtml',
    environment: {
      dominantEmotion: 'excited',
      visualDescription: '一组发光的选项像旋转的星系中的星星，每个都有独特的颜色和标签',
      atmosphere: '发现如何给可能性命名，创造更有意义的代码'
    },
    introduction: '枚举不是魔法，只是给一组相关的值起名字的方式。"红色"比0更有意义，"周一"比1更清晰。',
    phantomNotes: [
      { text: '幽灵观察：枚举是给不确定性的确定性命名。与其记住"0=友好，1=中性，2=敌对"，不如用GhostDisposition.FRIENDLY。' },
      { text: '魔瓶建议：使用字符串枚举（enum GhostType {FRIENDLY = "FRIENDLY"}）避免数字枚举的陷阱。' }
    ],
    codeExamples: [
      {
        code: `// 数字枚举（传统但有问题）
enum GhostType {
  FRIENDLY,    // 0
  NEUTRAL,     // 1  
  HOSTILE      // 2
}

// 字符串枚举（推荐）
enum GhostDisposition {
  FRIENDLY = "FRIENDLY",
  NEUTRAL = "NEUTRAL",
  HOSTILE = "HOSTILE"
}

// 使用枚举
function handleGhost(ghostType: GhostDisposition) {
  if (ghostType === GhostDisposition.FRIENDLY) {
    console.log("Hello friendly ghost!");
  }
}`,
        description: '命名可能性'
      }
    ],
    dimension: 'concepts',
    keywords: ['枚举', 'enum', '命名常量', '类型安全'],
    createdAt: new Date(),
    updatedAt: new Date()
  };
}

/**
 * 创建接口基础断面
 */
function createInterfaceBasicsSection(): Section {
  return {
    id: 'interface-basics',
    type: 'interface-basics',
    title: '接口：幽灵的契约',
    path: 'hallways/interfaces/interface-basics.xhtml',
    environment: {
      dominantEmotion: 'curious',
      visualDescription: '半透明的契约卷轴在空中展开，发光的条款定义了幽灵必须遵守的规则',
      atmosphere: '理解如何定义规则而不限制实现，感受到约束的自由'
    },
    introduction: '接口说："如果你想要成为X，你必须能做Y。"不关心你如何做到，只关心你能做到。这是规则，不是实现。',
    phantomNotes: [
      { text: '幽灵观察：接口是幽灵社会的法律。它们定义幽灵必须有的能力，但不规定这些能力如何实现。' },
      { text: '魔瓶世界观："没有无法塑造的规则，只有无法表达的现状。"接口就是你表达规则的方式。' }
    ],
    codeExamples: [
      {
        code: `// 定义幽灵契约
interface Ghost {
  name: string;
  appear(): void;
  disappear(): void;
}

// 实现契约
class FriendlyGhost implements Ghost {
  name: string;
  
  constructor(name: string) {
    this.name = name;
  }
  
  appear() {
    console.log(\`\${this.name} gently appears...\`);
  }
  
  disappear() {
    console.log(\`\${this.name} fades away...\`);
  }
}

// 使用契约
function interactWithGhost(ghost: Ghost) {
  ghost.appear();
  // 我们知道ghost有name、appear()和disappear()，因为接口保证了这一点
}`,
        description: '定义与实现契约'
      }
    ],
    dimension: 'concepts',
    keywords: ['接口', 'interface', '契约', '实现'],
    createdAt: new Date(),
    updatedAt: new Date()
  };
}

/**
 * 创建类型别名断面
 */
function createTypeAliasesSection(): Section {
  return {
    id: 'type-aliases',
    type: 'type-aliases',
    title: '类型别名：幽灵的化名',
    path: 'hallways/interfaces/type-aliases.xhtml',
    environment: {
      dominantEmotion: 'curious',
      visualDescription: '同一幽灵以不同面具显现，每个面具代表不同的身份，但本质相同',
      atmosphere: '发现同一概念可以有多个名字，理解命名的重要性'
    },
    introduction: '类型别名不是创造新类型，是给现有类型起新名字。就像幽灵可以叫"卡斯珀"，也可以叫"友好的幽灵"——还是同一个幽灵。',
    phantomNotes: [
      { text: '幽灵观察：接口定义"必须有什么"，类型别名只是说"这个东西也叫那个"。一个是要求，一个是昵称。' },
      { text: '魔瓶建议：为复杂的类型创建别名，让代码自我解释。GhostIdentifier比string更有意义。' }
    ],
    codeExamples: [
      {
        code: `// 复杂类型的别名
type GhostIdentifier = string;
type GhostAge = number;
type GhostCoordinates = [number, number];

// 使用别名
const ghostId: GhostIdentifier = "ghost-001";
const ghostLocation: GhostCoordinates = [23.5, 45.2];

// 复杂联合类型的别名
type GhostBehavior = '穿梭' | '显现' | '篡夺' | '低语';
type HauntedObject = Ghost | HauntedRoom | GhostlyPhenomenon;

// 与接口的比较
interface GhostInterface {
  name: string;
  appear(): void;
}

type GhostAlias = {
  name: string;
  appear(): void;
};`,
        description: '为复杂性命名'
      }
    ],
    dimension: 'concepts',
    keywords: ['类型别名', 'type alias', '命名', '复杂性'],
    createdAt: new Date(),
    updatedAt: new Date()
  };
}

/**
 * 创建可选与只读断面
 */
function createOptionalReadonlySection(): Section {
  return {
    id: 'optional-readonly',
    type: 'optional-readonly',
    title: '可选与只读：契约的灵活性',
    path: 'hallways/interfaces/optional-readonly.xhtml',
    environment: {
      dominantEmotion: 'excited',
      visualDescription: '契约条款有的在闪烁（可选），有的被锁住（只读），有的正常发光（必需）',
      atmosphere: '发现如何让契约既有规则又有灵活性，感受到设计的优雅'
    },
    introduction: '可选属性说："你可以有这个，但不是必须。"只读属性说："一旦有了这个，就不能改变。"一个创造灵活性，一个创造稳定性。',
    phantomNotes: [
      { text: '幽灵观察：可选属性是幽灵的隐身能力——有时显现，有时不。只读属性是幽灵的真名——一旦知道，就无法改变。' },
      { text: '设计模式：将不变的部分设为只读，将变化的部分设为可选或可变。这样既有稳定性又有适应性。' }
    ],
    codeExamples: [
      {
        code: `// 可选属性：可以有，可以没有
interface Ghost {
  name: string;
  age?: number;           // 可选：有些幽灵不知道自己的年龄
  favoritePlace?: string; // 可选：有些幽灵没有特别喜欢的地方
}

const casper: Ghost = { name: "卡斯珀" }; // age和favoritePlace是可选的
const oldGhost: Ghost = { name: "老幽灵", age: 300 }; // 提供了age

// 只读属性：一旦设置，不能改变
interface GhostRegistry {
  readonly id: string;    // 只读：幽灵ID一旦分配就不能改变
  name: string;           // 普通：名字可以改变
}

const ghost: GhostRegistry = { id: "ghost-001", name: "卡斯珀" };
// ghost.id = "ghost-002"; // 错误！id是只读的
ghost.name = "友好的卡斯珀"; // 没问题，name是可变的

// 结合使用
interface CompleteGhost {
  readonly id: string;
  name: string;
  age?: number;
}`,
        description: '灵活性与稳定性'
      }
    ],
    dimension: 'concepts',
    keywords: ['可选属性', '只读属性', 'readonly', '可选性', '不变性'],
    createdAt: new Date(),
    updatedAt: new Date()
  };
}

/**
 * 创建扩展与实现断面
 */
function createExtendsImplementsSection(): Section {
  return {
    id: 'extends-implements',
    type: 'extends-implements',
    title: '扩展与实现：契约的继承',
    path: 'hallways/interfaces/extends-implements.xhtml',
    environment: {
      dominantEmotion: 'excited',
      visualDescription: '契约卷轴相互连接，子契约继承父契约的条款并添加自己的新条款',
      atmosphere: '发现如何构建契约体系，感受到层次结构的力量'
    },
    introduction: '扩展说："我拥有父契约的一切，再加上更多。"实现说："我承诺遵守这个契约。"一个是继承特性，一个是遵守承诺。',
    phantomNotes: [
      { text: '幽灵观察：接口扩展是幽灵王朝的建立——祖先的能力传给后代。类实现是幽灵的社会契约——承诺遵守某些行为准则。' },
      { text: '魔瓶建议：扩展用于"是什么"的关系（Poltergeist是Ghost的一种），实现用于"能做什么"的关系（这个类能像Ghost一样行动）。' }
    ],
    codeExamples: [
      {
        code: `// 接口扩展：构建契约体系
interface Ghost {
  name: string;
  appear(): void;
}

interface FriendlyGhost extends Ghost {
  helpHumans(): void;  // 友好幽灵能帮助人类
}

interface Poltergeist extends Ghost {
  moveObjects(): void; // 骚灵能移动物体
}

// 类实现：承诺遵守契约
class BasicGhost implements Ghost {
  name: string;
  
  constructor(name: string) {
    this.name = name;
  }
  
  appear() {
    console.log(\`\${this.name} appears!\`);
  }
}

class FriendlyCaspar implements FriendlyGhost {
  name: string;
  
  constructor(name: string) {
    this.name = name;
  }
  
  appear() {
    console.log(\`\${this.name} gently appears...\`);
  }
  
  helpHumans() {
    console.log(\`\${this.name} helps the humans.\`);
  }
}

// 多层扩展
interface SupernaturalEntity {
  existsInDimension: string;
}

interface Ghost extends SupernaturalEntity {
  // 继承自SupernaturalEntity，所以也有existsInDimension
  name: string;
  appear(): void;
}`,
        description: '构建契约体系'
      }
    ],
    dimension: 'concepts',
    keywords: ['接口扩展', '类实现', 'extends', 'implements', '继承'],
    createdAt: new Date(),
    updatedAt: new Date()
  };
}

/**
 * 创建泛型基础断面
 */
function createGenericBasicsSection(): Section {
  return {
    id: 'generic-basics',
    type: 'generic-basics',
    title: '泛型基础：类型参数化',
    path: 'rooms/generics/generic-basics.xhtml',
    environment: {
      dominantEmotion: 'excited',
      visualDescription: '透明的模板在虚空中旋转，可以填入不同的类型材料，产生不同的具体形状',
      atmosphere: '发现如何创建可重用的类型模板，感受到抽象的力量'
    },
    introduction: '泛型说："给我一个类型，我给你一个专门为它设计的东西。"这是类型层面的模板——一次定义，多次使用，每次针对不同的具体类型。',
    phantomNotes: [
      { text: '幽灵观察：泛型是幽灵的变形能力——同一个幽灵可以显现为不同形态，但保持相同的本质结构。' },
      { text: '魔瓶建议：当你有重复的类型模式时，考虑泛型。如果多个函数或类有相似的结构但处理不同的类型，泛型可以帮你。' }
    ],
    codeExamples: [
      {
        code: `// 没有泛型：重复的代码
function getGhostName(ghost: Ghost): string {
  return ghost.name;
}

function getHumanName(human: Human): string {
  return human.name;
}

// 有泛型：一次定义，多次使用
function getName<T extends { name: string }>(entity: T): string {
  return entity.name;
}

// 使用泛型函数
const ghostName = getName(ghost);    // T被推断为Ghost
const humanName = getName(human);    // T被推断为Human

// 泛型接口
interface Container<T> {
  content: T;
  getContent(): T;
  setContent(content: T): void;
}

// 具体化泛型接口
const ghostContainer: Container<Ghost> = {
  content: casper,
  getContent() { return this.content; },
  setContent(ghost: Ghost) { this.content = ghost; }
};

const numberContainer: Container<number> = {
  content: 42,
  getContent() { return this.content; },
  setContent(num: number) { this.content = num; }
};`,
        description: '类型参数化'
      }
    ],
    dimension: 'concepts',
    keywords: ['泛型', 'generic', '类型参数', '模板', '可重用'],
    createdAt: new Date(),
    updatedAt: new Date()
  };
}

/**
 * 创建泛型约束断面
 */
function createGenericConstraintsSection(): Section {
  return {
    id: 'generic-constraints',
    type: 'generic-constraints',
    title: '泛型约束：边界的设定',
    path: 'rooms/generics/generic-constraints.xhtml',
    environment: {
      dominantEmotion: 'curious',
      visualDescription: '泛型模板周围出现发光的边界线，限制可以填入的类型材料',
      atmosphere: '发现如何控制泛型的灵活性，感受到约束带来的安全性'
    },
    introduction: '没有约束的泛型说："给我任何类型。"有约束的泛型说："给我某种特定类型的类型。"约束不是限制，是明确要求。',
    phantomNotes: [
      { text: '幽灵观察：泛型约束是幽灵活动范围的边界。幽灵可以在整个鬼屋中穿梭，但不能离开鬼屋。约束定义了这个鬼屋的范围。' },
      { text: '设计原则：从宽松的约束开始，只在必要时添加更严格的约束。让代码尽可能通用，但足够具体以保持类型安全。' }
    ],
    codeExamples: [
      {
        code: `// 没有约束：太宽松
function logLength<T>(item: T): void {
  // console.log(item.length); // 错误！不知道T是否有length属性
}

// 有约束：明确要求
function logLength<T extends { length: number }>(item: T): void {
  console.log(item.length); // 安全！T必须有length属性
}

logLength("hello");           // 字符串有length
logLength([1, 2, 3]);         // 数组有length
// logLength(42);             // 错误！数字没有length

// 多重约束
function processEntity<T extends Ghost & Timestamped>(entity: T): void {
  console.log(entity.name);      // 来自Ghost
  console.log(entity.createdAt); // 来自Timestamped
}

// keyof约束：确保属性存在
function getProperty<T, K extends keyof T>(obj: T, key: K): T[K] {
  return obj[key];
}

const ghost = { name: "卡斯珀", age: 150 };
getProperty(ghost, "name"); // 返回string
getProperty(ghost, "age");  // 返回number
// getProperty(ghost, "color"); // 错误！ghost没有color属性`,
        description: '设定类型边界'
      }
    ],
    dimension: 'concepts',
    keywords: ['泛型约束', 'extends', '类型边界', '安全性'],
    createdAt: new Date(),
    updatedAt: new Date()
  };
}

/**
 * 创建实用工具类型断面
 */
function createUtilityTypesSection(): Section {
  return {
    id: 'utility-types',
    type: 'utility-types',
    title: '实用工具类型：内置的幽灵工具',
    path: 'rooms/generics/utility-types.xhtml',
    environment: {
      dominantEmotion: 'excited',
      visualDescription: '一组发光的工具在虚空中漂浮，每个工具都能以特定方式变形或操作类型',
      atmosphere: '发现TypeScript内置的强大工具，感受到语言设计的深度'
    },
    introduction: 'TypeScript提供了一组内置的工具类型，就像幽灵工具箱里的特殊工具。不需要自己制造这些工具，直接使用它们。',
    phantomNotes: [
      { text: '幽灵观察：实用工具类型是幽灵世界的自然法则。Partial让幽灵部分显现，Readonly让幽灵固定形态，Pick让幽灵只显现特定部分。' },
      { text: '记忆技巧：不需要记住所有工具类型。记住常用的几个（Partial, Readonly, Pick, Omit），其他的在需要时查阅文档。' }
    ],
    codeExamples: [
      {
        code: `// Partial<T>：所有属性变为可选
interface Ghost {
  name: string;
  age: number;
  location: string;
}

type PartialGhost = Partial<Ghost>;
// 相当于 { name?: string; age?: number; location?: string; }

// 用于更新函数
function updateGhost(ghost: Ghost, updates: Partial<Ghost>): Ghost {
  return { ...ghost, ...updates };
}

// Readonly<T>：所有属性变为只读
type ImmutableGhost = Readonly<Ghost>;
// 相当于 { readonly name: string; readonly age: number; ... }

// Pick<T, K>：选择特定属性
type GhostIdentity = Pick<Ghost, 'name' | 'age'>;
// 相当于 { name: string; age: number; }

// Omit<T, K>：排除特定属性
type GhostWithoutAge = Omit<Ghost, 'age'>;
// 相当于 { name: string; location: string; }

// Record<K, T>：创建键值映射
type GhostRegistry = Record<string, Ghost>;
// 相当于 { [key: string]: Ghost; }

// 组合使用工具类型
type GhostUpdate = Partial<Pick<Ghost, 'name' | 'location'>>;
// 可以更新name和location，都是可选的

// 更复杂的例子
type ReadonlyPartialGhost = Readonly<Partial<Ghost>>;
// 所有属性可选且只读，适合配置对象`,
        description: '内置类型工具'
      }
    ],
    dimension: 'concepts',
    keywords: ['实用工具类型', 'Partial', 'Readonly', 'Pick', 'Omit', 'Record'],
    createdAt: new Date(),
    updatedAt: new Date()
  };
}

/**
 * 创建条件类型断面
 */
function createConditionalTypesSection(): Section {
  return {
    id: 'conditional-types',
    type: 'conditional-types',
    title: '条件类型：类型逻辑',
    path: 'rooms/generics/conditional-types.xhtml',
    environment: {
      dominantEmotion: 'excited',
      visualDescription: '类型像发光的符号在逻辑门中流动，根据条件选择不同的路径，产生不同的结果类型',
      atmosphere: '发现类型系统可以包含逻辑判断，感受到类型编程的可能性'
    },
    introduction: '条件类型说："如果T是X类型，那么结果是Y类型，否则是Z类型。"这是类型层面的if-else语句。',
    phantomNotes: [
      { text: '幽灵观察：条件类型是幽灵的决策能力。根据输入的类型，幽灵选择不同的显现方式。这是类型系统的元认知。' },
      { text: '高级技巧：条件类型经常与infer关键字结合使用，从复杂类型中提取部分类型。' }
    ],
    codeExamples: [
      {
        code: `// 基本的条件类型
type IsString<T> = T extends string ? true : false;

type Test1 = IsString<"hello">;  // true
type Test2 = IsString<number>;   // false
type Test3 = IsString<string | number>; // boolean (分布式条件类型)

// 提取数组元素类型
type ExtractElementType<T> = T extends (infer U)[] ? U : never;

type StringArrayElement = ExtractElementType<string[]>; // string
type NumberArrayElement = ExtractElementType<number[]>; // number
type NotArray = ExtractElementType<string>;             // never

// 提取函数返回类型
type ReturnType<T> = T extends (...args: any[]) => infer R ? R : never;

type FuncReturn = ReturnType<() => string>;      // string
type AsyncReturn = ReturnType<() => Promise<number>>; // Promise<number>

// 条件类型与映射类型结合
type Nullable<T> = {
  [K in keyof T]: T[K] | null;
};

// 条件映射类型：只处理特定类型的属性
type StringPropsOnly<T> = {
  [K in keyof T as T[K] extends string ? K : never]: T[K]
};

interface Ghost {
  name: string;      // string
  age: number;       // number  
  location: string;  // string
}

type GhostStringProps = StringPropsOnly<Ghost>;
// 相当于 { name: string; location: string; }

// 条件类型工具：NonNullable
type NonNullable<T> = T extends null | undefined ? never : T;

type MaybeString = string | null | undefined;
type DefinitelyString = NonNullable<MaybeString>; // string`,
        description: '类型逻辑判断'
      }
    ],
    dimension: 'concepts',
    keywords: ['条件类型', 'conditional types', '类型逻辑', 'infer', '类型提取'],
    createdAt: new Date(),
    updatedAt: new Date()
  };
}

/**
 * 创建类基础断面
 */
function createClassBasicsSection(): Section {
  return {
    id: 'class-basics',
    type: 'class-basics',
    title: '类基础：幽灵的模板',
    path: 'rooms/classes/class-basics.xhtml',
    environment: {
      dominantEmotion: 'curious',
      visualDescription: '发光的模板在虚空中旋转，可以从中复制出具有相同结构的实体幽灵',
      atmosphere: '发现如何创建可复用的实体模板，感受到面向对象的力量'
    },
    introduction: '类说："按照这个模板创建实体。"接口定义"必须有什么"，类定义"如何有"和"如何做"。一个是契约，一个是实现。',
    phantomNotes: [
      { text: '幽灵观察：类是幽灵的出生证明。定义了幽灵如何被创造，具有什么属性，能做什么行为。每个实例是这个类的具体显现。' },
      { text: '魔瓶建议：当你有多个相似对象时使用类。当只需要定义结构时使用接口。类用于创建，接口用于描述。' }
    ],
    codeExamples: [
      {
        code: `// 定义幽灵类
class Ghost {
  // 属性
  name: string;
  age: number;
  
  // 构造函数：创建幽灵实例
  constructor(name: string, age: number) {
    this.name = name;
    this.age = age;
  }
  
  // 方法：幽灵的行为
  appear() {
    console.log(\`\${this.name} appears!\`);
  }
  
  disappear() {
    console.log(\`\${this.name} disappears...\`);
  }
  
  // 计算属性
  get description(): string {
    return \`\${this.name}, \${this.age} years old\`;
  }
}

// 创建幽灵实例
const casper = new Ghost("卡斯珀", 150);
const victoria = new Ghost("维多利亚", 230);

// 使用幽灵
casper.appear();                   // "卡斯珀 appears!"
console.log(casper.description);   // "卡斯珀, 150 years old"

// 类继承接口
interface Appearable {
  appear(): void;
}

class FriendlyGhost extends Ghost implements Appearable {
  // 继承自Ghost，所以已经有name, age, appear(), disappear()
  
  // 添加新方法
  help() {
    console.log(\`\${this.name} helps someone.\`);
  }
  
  // 覆盖父类方法
  appear() {
    console.log(\`\${this.name} gently appears...\`);
  }
}

const friendly = new FriendlyGhost("友好的幽灵", 100);
friendly.appear(); // "友好的幽灵 gently appears..." (覆盖的方法)
friendly.help();   // "友好的幽灵 helps someone." (新方法)`,
        description: '创建实体模板'
      }
    ],
    dimension: 'concepts',
    keywords: ['类', 'class', '构造函数', '方法', '实例', '面向对象'],
    createdAt: new Date(),
    updatedAt: new Date()
  };
}

/**
 * 创建访问修饰符断面
 */
function createAccessModifiersSection(): Section {
  return {
    id: 'access-modifiers',
    type: 'access-modifiers',
    title: '访问修饰符：幽灵社会的边界',
    path: 'rooms/classes/access-modifiers.xhtml',
    environment: {
      dominantEmotion: 'curious',
      visualDescription: '幽灵社会的不同区域：公共广场（public）、家庭区域（private）、受保护的花园（protected）',
      atmosphere: '发现如何控制谁可以访问什么，感受到封装的重要性'
    },
    introduction: '访问修饰符定义幽灵社会的边界：public（谁都可以访问）、private（只有自己可以访问）、protected（自己和后代可以访问）。这是封装的核心。',
    phantomNotes: [
      { text: '幽灵观察：public是幽灵在公共广场的显现，所有人都能看到。private是幽灵在密室中的秘密，只有自己知道。protected是幽灵家族的传承，只传给后代。' },
      { text: '设计原则：默认使用private，只在必要时放宽访问。这保护了内部实现，让类更容易维护和修改。' }
    ],
    codeExamples: [
      {
        code: `// 访问修饰符示例
class Ghost {
  // public: 所有人都可以访问（默认）
  public name: string;
  
  // private: 只有这个类内部可以访问
  private secret: string;
  
  // protected: 这个类和子类可以访问
  protected age: number;
  
  constructor(name: string, secret: string, age: number) {
    this.name = name;
    this.secret = secret;
    this.age = age;
  }
  
  // public方法：外部可以调用
  public appear() {
    console.log(\`\${this.name} appears!\`);
    this.revealSecret(); // 内部可以调用private方法
  }
  
  // private方法：只有内部可以调用
  private revealSecret() {
    console.log(\`My secret is: \${this.secret}\`);
  }
  
  // protected方法：内部和子类可以调用
  protected getFormattedAge() {
    return \`\${this.age} years old\`;
  }
}

const casper = new Ghost("卡斯珀", "害怕黑暗", 150);

// 访问public成员
console.log(casper.name); // "卡斯珀"
casper.appear();          // "卡斯珀 appears!" 然后 "My secret is: 害怕黑暗"

// 不能访问private成员
// console.log(casper.secret); // 错误！secret是private
// casper.revealSecret();      // 错误！revealSecret是private

// 不能访问protected成员
// console.log(casper.age);    // 错误！age是protected

// 子类可以访问protected成员
class FriendlyGhost extends Ghost {
  introduce() {
    console.log(\`I'm \${this.name}, \${this.getFormattedAge()}\`);
    // 可以访问protected的age和getFormattedAge()
    // 但不能访问private的secret和revealSecret()
  }
}

const friendly = new FriendlyGhost("友好的幽灵", "喜欢帮助人", 100);
friendly.introduce(); // "I'm 友好的幽灵, 100 years old"`,
        description: '控制访问边界'
      }
    ],
    dimension: 'concepts',
    keywords: ['访问修饰符', 'public', 'private', 'protected', '封装', '可见性'],
    createdAt: new Date(),
    updatedAt: new Date()
  };
}

/**
 * 创建继承断面
 */
function createInheritanceSection(): Section {
  return {
    id: 'inheritance',
    type: 'inheritance',
    title: '继承：幽灵王朝的建立',
    path: 'rooms/classes/inheritance.xhtml',
    environment: {
      dominantEmotion: 'excited',
      visualDescription: '幽灵家族树在虚空中展开，祖先的能力和特性沿着分支传递给后代',
      atmosphere: '发现如何构建类型层次结构，感受到代码复用的力量'
    },
    introduction: '继承说："我是你的一种，所以我拥有你的一切，再加上我自己的特点。"这是面向对象的核心——构建类型体系，复用代码。',
    phantomNotes: [
      { text: '幽灵观察：继承是幽灵王朝的建立。Ghost是祖先，Poltergeist和FriendlyGhost是不同分支的后代。每个后代继承祖先的特性，并添加自己的独特能力。' },
      { text: '设计建议：优先使用组合而不是继承。继承创建"是什么"的关系，组合创建"有什么"的关系。继承紧密耦合，组合更灵活。' }
    ],
    codeExamples: [
      {
        code: `// 基类：通用幽灵
class Ghost {
  name: string;
  age: number;
  
  constructor(name: string, age: number) {
    this.name = name;
    this.age = age;
  }
  
  appear() {
    console.log(\`\${this.name} appears!\`);
  }
  
  disappear() {
    console.log(\`\${this.name} disappears...\`);
  }
  
  getDescription() {
    return \`\${this.name}, \${this.age} years old\`;
  }
}

// 子类1：骚灵（能移动物体）
class Poltergeist extends Ghost {
  strength: number; // 新属性
  
  constructor(name: string, age: number, strength: number) {
    super(name, age); // 调用父类构造函数
    this.strength = strength;
  }
  
  // 新方法
  moveObject(object: string) {
    console.log(\`\${this.name} moves \${object} with strength \${this.strength}!\`);
  }
  
  // 覆盖父类方法
  appear() {
    console.log(\`\${this.name} appears with a creepy noise!\`);
  }
}

// 子类2：友好幽灵（能帮助人类）
class FriendlyGhost extends Ghost {
  helpfulness: number; // 新属性
  
  constructor(name: string, age: number, helpfulness: number) {
    super(name, age);
    this.helpfulness = helpfulness;
  }
  
  // 新方法
  help(human: string) {
    console.log(\`\${this.name} helps \${human} with helpfulness \${this.helpfulness}!\`);
  }
  
  // 覆盖父类方法
  getDescription() {
    return \`\${super.getDescription()} (helpfulness: \${this.helpfulness})\`;
  }
}

// 使用继承体系
const casper = new Ghost("卡斯珀", 150);
const poltergeist = new Poltergeist("骚灵", 200, 5);
const friendly = new FriendlyGhost("友好的幽灵", 100, 8);

casper.appear();           // "卡斯珀 appears!"
poltergeist.appear();      // "骚灵 appears with a creepy noise!" (覆盖的方法)
poltergeist.moveObject("椅子"); // "骚灵 moves 椅子 with strength 5!" (新方法)

friendly.help("小明");      // "友好的幽灵 helps 小明 with helpfulness 8!" (新方法)
console.log(friendly.getDescription()); // "友好的幽灵, 100 years old (helpfulness: 8)" (覆盖的方法)

// 多态：将子类视为父类
const ghosts: Ghost[] = [casper, poltergeist, friendly];
ghosts.forEach(ghost => ghost.appear()); // 每个幽灵以自己方式显现`,
        description: '构建类型层次'
      }
    ],
    dimension: 'concepts',
    keywords: ['继承', 'inheritance', 'extends', 'super', '多态', '面向对象'],
    createdAt: new Date(),
    updatedAt: new Date()
  };
}

/**
 * 创建抽象类与接口断面
 */
function createAbstractInterfacesSection(): Section {
  return {
    id: 'abstract-interfaces',
    type: 'abstract-interfaces',
    title: '抽象类与接口实现',
    path: 'rooms/classes/abstract-interfaces.xhtml',
    environment: {
      dominantEmotion: 'excited',
      visualDescription: '抽象概念像半成形的幽灵轮廓，必须由具体类填充完整；接口像发光的契约，类必须签字遵守',
      atmosphere: '发现抽象与具体的平衡，感受到设计模式的优雅'
    },
    introduction: '抽象类说："我有一些实现，但有些部分你必须自己完成。"接口说："你必须做到这些，但怎么做我不管。"一个是部分模板，一个是纯契约。',
    phantomNotes: [
      { text: '幽灵观察：抽象类是半成形的幽灵，有基本结构但缺少关键部分。具体类填充这些部分，让幽灵完全成形。接口是幽灵的行为准则，无论幽灵如何实现，必须遵守这些准则。' },
      { text: '使用场景：当多个相关类共享一些实现时使用抽象类。当只需要定义契约时使用接口。抽象类用于"是什么"的层次，接口用于"能做什么"的能力。' }
    ],
    codeExamples: [
      {
        code: `// 抽象类：部分实现的模板
abstract class SupernaturalEntity {
  // 抽象属性：必须在子类中实现
  abstract name: string;
  
  // 抽象方法：必须在子类中实现
  abstract manifest(): void;
  
  // 具体方法：已经有实现，子类可以继承
  exists() {
    console.log(\`\${this.name} exists in the supernatural realm.\`);
  }
  
  // 具体方法：子类可以覆盖
  getDescription(): string {
    return \`A supernatural entity named \${this.name}\`;
  }
}

// 接口：纯契约
interface Hauntable {
  haunt(location: string): void;
  getHauntLevel(): number;
}

// 具体类继承抽象类并实现接口
class Ghost extends SupernaturalEntity implements Hauntable {
  name: string;
  age: number;
  
  constructor(name: string, age: number) {
    super(); // 必须调用父类构造函数
    this.name = name;
    this.age = age;
  }
  
  // 实现抽象方法
  manifest() {
    console.log(\`\${this.name} manifests as a ghostly figure.\`);
  }
  
  // 覆盖具体方法
  getDescription(): string {
    return \`\${super.getDescription()}, \${this.age} years old\`;
  }
  
  // 实现接口方法
  haunt(location: string) {
    console.log(\`\${this.name} haunts \${location}.\`);
  }
  
  getHauntLevel(): number {
    return this.age > 100 ? 5 : 2;
  }
}

// 另一个具体类
class Poltergeist extends SupernaturalEntity implements Hauntable {
  name: string;
  strength: number;
  
  constructor(name: string, strength: number) {
    super();
    this.name = name;
    this.strength = strength;
  }
  
  // 实现抽象方法（不同实现）
  manifest() {
    console.log(\`\${this.name} manifests by moving objects!\`);
  }
  
  // 实现接口方法（不同实现）
  haunt(location: string) {
    console.log(\`\${this.name} violently haunts \${location} with strength \${this.strength}!\`);
  }
  
  getHauntLevel(): number {
    return this.strength * 2;
  }
}

// 不能创建抽象类的实例
// const entity = new SupernaturalEntity(); // 错误！抽象类不能实例化

// 可以创建具体类的实例
const ghost = new Ghost("卡斯珀", 150);
const poltergeist = new Poltergeist("骚灵", 8);

ghost.exists();       // "卡斯珀 exists in the supernatural realm." (继承的方法)
ghost.manifest();     // "卡斯珀 manifests as a ghostly figure." (实现的抽象方法)
ghost.haunt("客厅");  // "卡斯珀 haunts 客厅." (实现的接口方法)`,
        description: '抽象与契约'
      }
    ],
    dimension: 'concepts',
    keywords: ['抽象类', 'abstract', '接口实现', '契约', '模板'],
    createdAt: new Date(),
    updatedAt: new Date()
  };
}

/**
 * 创建模块基础断面
 */
function createModuleBasicsSection(): Section {
  return {
    id: 'module-basics',
    type: 'module-basics',
    title: '模块基础：代码的领地划分',
    path: 'rooms/modules/module-basics.xhtml',
    environment: {
      dominantEmotion: 'curious',
      visualDescription: '代码像发光的领土被无形的边界划分，每个模块有自己的领域，边界上有进出口',
      atmosphere: '发现如何组织大型代码库，感受到结构清晰的好处'
    },
    introduction: '模块说："这是我的领地。这里面的东西是我私有的，除非我明确说可以出口。如果你想用，必须从我的出口进口。"',
    phantomNotes: [
      { text: '幽灵观察：模块是幽灵世界的国度划分。每个模块有自己的幽灵和规则。跨模块交互需要通过正式的进出口通道。' },
      { text: '最佳实践：一个文件一个模块，相关功能放在同一个模块，模块间通过清晰的接口交互。' }
    ],
    codeExamples: [
      {
        code: `// ghosts.ts - 幽灵模块
export interface Ghost {
  name: string;
  age: number;
}

export class FriendlyGhost implements Ghost {
  constructor(public name: string, public age: number) {}
  
  appear() {
    console.log(\`\${this.name} gently appears...\`);
  }
}

// 私有函数：模块外部不能访问
function calculateGhostPower(age: number): number {
  return age * 10;
}

// 默认导出
export default class GhostManager {
  private ghosts: Ghost[] = [];
  
  addGhost(ghost: Ghost) {
    this.ghosts.push(ghost);
  }
}

// ---
// haunt.ts - 出没模块
import { Ghost, FriendlyGhost } from './ghosts';
import GhostManager from './ghosts'; // 导入默认导出

export function createHaunt(ghost: Ghost, location: string) {
  console.log(\`\${ghost.name} haunts \${location}\`);
}

// 重新导出
export { Ghost } from './ghosts';

// ---
// main.ts - 主模块
import { FriendlyGhost } from './ghosts';
import { createHaunt } from './haunt';
import GhostManager from './ghosts';

const casper = new FriendlyGhost("卡斯珀", 150);
createHaunt(casper, "老宅");

const manager = new GhostManager();
manager.addGhost(casper);`,
        description: '模块导入导出'
      }
    ],
    dimension: 'concepts',
    keywords: ['模块', 'import', 'export', '默认导出', '命名导出'],
    createdAt: new Date(),
    updatedAt: new Date()
  };
}

/**
 * 创建导入导出断面
 */
function createImportExportSection(): Section {
  return {
    id: 'import-export',
    type: 'import-export',
    title: '导入与导出：领地的通道',
    path: 'rooms/modules/import-export.xhtml',
    environment: {
      dominantEmotion: 'curious',
      visualDescription: '模块边界上有各种类型的进出口：标准通道（命名导出）、主大门（默认导出）、专用通道（重新导出）',
      atmosphere: '掌握模块间通信的各种方式，感受到灵活性的好处'
    },
    introduction: '导出定义"什么可以离开这个模块"，导入定义"什么可以进入这个模块"。这是模块间通信的协议。',
    phantomNotes: [
      { text: '幽灵观察：命名导出是幽灵世界的正规外交渠道，每个出口有明确标签。默认导出是主要贸易路线，最常用但也最容易被误用。' },
      { text: '使用建议：优先使用命名导出，让导入方明确知道得到什么。只有在模块确实只有一个主要功能时使用默认导出。' }
    ],
    codeExamples: [
      {
        code: `// 多种导出方式
// module.ts
export const ghostName = "卡斯珀";            // 命名导出变量
export function appear() {                    // 命名导出函数
  console.log("A ghost appears!");
}
export class Ghost {                          // 命名导出类
  constructor(public name: string) {}
}
export default class GhostManager {           // 默认导出
  private ghosts: Ghost[] = [];
}

const secret = "这个不导出";                   // 私有，外部不能访问

// 批量导出
const ghostTypes = {
  FRIENDLY: "友好",
  HOSTILE: "敌对"
};

export { ghostTypes };

// 导出别名
export { Ghost as SupernaturalEntity };

// 重新导出其他模块的内容
export { Ghost } from './ghost-module';
export { default as Manager } from './manager-module';

// ---
// 多种导入方式
// app.ts
import GhostManager from './module';          // 导入默认导出
import { Ghost, ghostName } from './module';  // 导入命名导出
import { Ghost as SupernaturalEntity } from './module'; // 导入别名
import * as GhostModule from './module';      // 导入所有作为命名空间

// 重新导出导入的内容
export { Ghost } from './module';

// 动态导入（按需加载）
async function loadGhostModule() {
  const module = await import('./module');
  const ghost = new module.Ghost("卡斯珀");
}

// 只导入类型（TypeScript特有）
import type { Ghost } from './module';

// 副作用导入（只运行模块，不导入任何内容）
import './side-effects';`,
        description: '多样的导入导出'
      }
    ],
    dimension: 'concepts',
    keywords: ['导入', '导出', 'import', 'export', '默认导出', '命名导出', '重新导出'],
    createdAt: new Date(),
    updatedAt: new Date()
  };
}

/**
 * 创建命名空间断面
 */
function createNamespaceSection(): Section {
  return {
    id: 'namespace',
    type: 'namespace',
    title: '命名空间：历史的遗留',
    path: 'rooms/modules/namespace.xhtml',
    environment: {
      dominantEmotion: 'curious',
      visualDescription: '古老的组织结构像发光的层级目录，逐渐被现代的平面模块结构取代',
      atmosphere: '理解TypeScript的历史和演变，感受到向后兼容的重要性'
    },
    introduction: '命名空间是TypeScript早期的模块系统，在现代ES模块普及前使用。现在主要用在声明文件（.d.ts）中组织类型。',
    phantomNotes: [
      { text: '幽灵观察：命名空间是幽灵世界的古老王国制度，有严格的层级。现代模块系统是联邦制，每个文件平等独立。' },
      { text: '现代用法：在新代码中使用ES模块。命名空间主要用于组织第三方库的类型声明，或处理遗留代码。' }
    ],
    codeExamples: [
      {
        code: `// 定义命名空间
namespace GhostWorld {
  export interface Ghost {      // 必须export才能在外部访问
    name: string;
    appear(): void;
  }
  
  export class FriendlyGhost implements Ghost {
    constructor(public name: string) {}
    
    appear() {
      console.log(\`\${this.name} gently appears...\`);
    }
  }
  
  // 嵌套命名空间
  export namespace Haunts {
    export interface Haunt {
      location: string;
      intensity: number;
    }
  }
  
  // 私有，只能在命名空间内部访问
  const SECRET_PHRASE = "Boo!";
}

// 使用命名空间
const ghost: GhostWorld.Ghost = {
  name: "卡斯珀",
  appear() { console.log("Boo!"); }
};

const friendly = new GhostWorld.FriendlyGhost("友好的幽灵");
const haunt: GhostWorld.Haunts.Haunt = {
  location: "老宅",
  intensity: 5
};

// 命名空间合并（跨文件扩展）
// file1.ts
namespace GhostWorld {
  export interface Poltergeist {
    strength: number;
  }
}

// file2.ts  
namespace GhostWorld {
  export function createPoltergeist(): Poltergeist {
    return { strength: 10 };
  }
}

// 三斜线指令引用命名空间
/// <reference path="ghost-world.ts" />

// 命名空间与现代模块的对比
// 现代ES模块（推荐）：
export interface Ghost { /* ... */ }
export class FriendlyGhost { /* ... */ }

// 使用时：
import { Ghost, FriendlyGhost } from './ghosts';`,
        description: '传统的组织方式'
      }
    ],
    dimension: 'concepts',
    keywords: ['命名空间', 'namespace', '模块历史', '向后兼容'],
    createdAt: new Date(),
    updatedAt: new Date()
  };
}

/**
 * 创建模块解析断面
 */
function createModuleResolutionSection(): Section {
  return {
    id: 'module-resolution',
    type: 'module-resolution',
    title: '模块解析：路径的寻找',
    path: 'rooms/modules/module-resolution.xhtml',
    environment: {
      dominantEmotion: 'curious',
      visualDescription: '导入路径像发光的线索在文件系统中延伸，TypeScript编译器像侦探一样追踪这些线索找到模块',
      atmosphere: '理解TypeScript如何找到模块，解决常见的模块找不到问题'
    },
    introduction: '当你说`import { Ghost } from "./ghosts"`时，TypeScript需要找到`ghosts`模块。模块解析就是TypeScript寻找模块的过程。',
    phantomNotes: [
      { text: '幽灵观察：模块解析是幽灵世界的寻路系统。相对路径是本地地图，绝对路径是全局坐标，node_modules是公共图书馆。' },
      { text: '常见问题：模块找不到错误通常由路径错误、缺少文件扩展名、或tsconfig.json配置问题引起。' }
    ],
    codeExamples: [
      {
        code: `// 不同的导入路径类型
import { Ghost } from './ghosts';           // 相对路径
import { Ghost } from '../entities/ghosts'; // 相对路径（上级目录）
import { Ghost } from '/src/ghosts';        // 绝对路径（根据baseUrl）
import { Ghost } from 'ghost-library';      // node_modules中的包

// TypeScript的模块解析策略
// 1. Classic（传统）- 主要为了向后兼容
// 2. Node（推荐）- 模仿Node.js的模块解析

// tsconfig.json中的相关配置
/*
{
  "compilerOptions": {
    "moduleResolution": "node",  // 使用Node.js风格的模块解析
    
    "baseUrl": "./src",          // 基础路径，用于绝对导入
    "paths": {                   // 路径映射
      "@entities/*": ["entities/*"],
      "@utils/*": ["utils/*"]
    },
    
    "rootDirs": [                // 多个根目录
      "./src",
      "./generated"
    ],
    
    "typeRoots": [               // 类型声明文件的位置
      "./node_modules/@types",
      "./custom-types"
    ],
    
    "types": ["node", "jest"]    // 包含的类型声明包
  }
}
*/

// 路径映射示例
// 配置了 "paths": { "@entities/*": ["src/entities/*"] }
import { Ghost } from '@entities/ghosts'; // 解析为 src/entities/ghosts

// Node.js模块解析过程（当导入'ghost-library'时）：
// 1. 当前目录的node_modules/ghost-library
// 2. 上级目录的node_modules/ghost-library
// 3. 继续向上直到根目录
// 4. 全局node_modules

// 文件扩展名解析顺序：
// .ts -> .tsx -> .d.ts -> .js -> .jsx -> .json

// 常见的模块解析错误和解决：
// 错误: Cannot find module './ghosts'
// 可能原因:
// 1. 文件不存在或路径错误
// 2. 需要添加文件扩展名: './ghosts.ts'
// 3. 需要配置moduleResolution或baseUrl

// 使用相对路径时的注意事项：
// ./ - 当前目录
// ../ - 上级目录
// 不加./ - 从node_modules或baseUrl查找`,
        description: '模块查找机制'
      }
    ],
    dimension: 'concepts',
    keywords: ['模块解析', 'moduleResolution', '路径映射', 'baseUrl', 'paths'],
    createdAt: new Date(),
    updatedAt: new Date()
  };
}

/**
 * 创建tsconfig基础断面
 */
function createTsconfigBasicsSection(): Section {
  return {
    id: 'tsconfig-basics',
    type: 'tsconfig-basics',
    title: 'tsconfig.json基础',
    path: 'secret-passages/configuration/tsconfig-basics.xhtml',
    environment: {
      dominantEmotion: 'curious',
      visualDescription: '控制室中有一个巨大的控制面板，每个开关控制TypeScript编译器的不同方面',
      atmosphere: '掌握TypeScript项目的配置，感受到对编译过程的控制力'
    },
    introduction: 'tsconfig.json是TypeScript项目的控制中心。它告诉TypeScript编译器："这是我的项目，这是我希望你如何处理它。"',
    phantomNotes: [
      { text: '幽灵观察：tsconfig.json是鬼屋的建筑规范。它定义幽灵世界的物理法则：幽灵可以做什么，不能做什么，如何显现。' },
      { text: '配置哲学：从严格配置开始（strict: true），只在必要时放宽限制。类型安全是TypeScript的最大优势。' }
    ],
    codeExamples: [
      {
        code: `// tsconfig.json 基础结构
{
  // 编译器选项 - 最重要的部分
  "compilerOptions": {
    // 输出目标
    "target": "ES2022",          // 编译成的JavaScript版本
    "module": "ESNext",          // 模块系统
    "lib": ["ES2022", "DOM"],    // 包含的库定义
    
    // 模块解析
    "moduleResolution": "bundler", // 模块解析策略
    "baseUrl": "./",              // 基础路径
    "paths": {                    // 路径映射
      "@/*": ["src/*"]
    },
    
    // 输出
    "outDir": "./dist",           // 输出目录
    "rootDir": "./src",           // 源文件根目录
    
    // 严格性选项
    "strict": true,               // 开启所有严格检查
    "noImplicitAny": true,        // 不允许隐式的any类型
    "strictNullChecks": true,     // 严格的null检查
    "strictFunctionTypes": true,  // 严格的函数类型检查
    
    // 类型检查
    "noUnusedLocals": true,       // 检查未使用的局部变量
    "noUnusedParameters": true,   // 检查未使用的参数
    "noImplicitReturns": true,    // 检查函数是否总是返回值
    
    // JavaScript支持
    "allowJs": true,              // 允许JavaScript文件
    "checkJs": true,              // 检查JavaScript文件中的类型
    
    // 其他
    "esModuleInterop": true,      // 更好的CommonJS/ES模块互操作
    "skipLibCheck": true,         // 跳过库文件的类型检查
    "forceConsistentCasingInFileNames": true // 强制文件名大小写一致
  },
  
  // 包含的文件
  "include": [
    "src/**/*"                    // 包含src目录下的所有文件
  ],
  
  // 排除的文件
  "exclude": [
    "node_modules",               // 排除node_modules
    "dist",                       // 排除输出目录
    "**/*.test.ts",               // 排除测试文件
    "**/*.spec.ts"                // 排除规格文件
  ],
  
  // 文件引用
  "files": [
    "src/types.d.ts"              // 显式包含的文件
  ],
  
  // 继承配置
  "extends": "./tsconfig.base.json" // 继承基础配置
}

// 继承配置示例
// tsconfig.base.json - 基础配置
{
  "compilerOptions": {
    "strict": true,
    "target": "ES2022",
    "module": "ESNext"
  }
}

// tsconfig.json - 扩展配置
{
  "extends": "./tsconfig.base.json",
  "compilerOptions": {
    "outDir": "./dist",  // 添加或覆盖选项
    "rootDir": "./src"
  },
  "include": ["src/**/*"]
}

// 特定环境的配置
// tsconfig.test.json - 测试配置
{
  "extends": "./tsconfig.json",
  "compilerOptions": {
    "noEmit": true  // 测试时不输出文件
  },
  "include": [
    "src/**/*",
    "tests/**/*"
  ]
}`,
        description: '项目配置基础'
      }
    ],
    dimension: 'concepts',
    keywords: ['tsconfig', '编译器选项', '配置', 'TypeScript配置'],
    createdAt: new Date(),
    updatedAt: new Date()
  };
}

/**
 * 创建编译器选项断面
 */
function createCompilerOptionsSection(): Section {
  return {
    id: 'compiler-options',
    type: 'compiler-options',
    title: '编译器选项解析',
    path: 'secret-passages/configuration/compiler-options.xhtml',
    environment: {
      dominantEmotion: 'excited',
      visualDescription: '编译器像复杂的机器，每个选项是控制机器行为的旋钮和开关',
      atmosphere: '深入理解TypeScript编译器的各种选项，感受到精确控制的力量'
    },
    introduction: 'TypeScript有200多个编译器选项。你不需要记住它们，但需要知道重要的几个。这些选项控制从类型检查到代码生成的一切。',
    phantomNotes: [
      { text: '幽灵观察：编译器选项是幽灵显现的参数。strict选项决定幽灵必须完全成形，noImplicitAny要求幽灵必须有明确本质，sourceMap让人类能追踪幽灵的起源。' },
      { text: '学习路径：从strict: true开始，这是最重要的选项。然后根据需要调整其他选项。使用tsc --help查看所有选项。' }
    ],
    codeExamples: [
      {
        code: `// 重要的编译器选项分类

// 1. 严格性选项（strict系列）
/*
  "strict": true, // 开启所有严格检查（推荐！）
  
  等价于同时开启：
  - "noImplicitAny": true        // 不允许隐式any
  - "strictNullChecks": true     // 严格null检查
  - "strictFunctionTypes": true  // 严格函数类型
  - "strictBindCallApply": true  // 严格bind/call/apply检查
  - "strictPropertyInitialization": true // 严格属性初始化
  - "noImplicitThis": true       // 不允许隐式this
  - "alwaysStrict": true         // 总是使用严格模式
*/

// 2. 模块和输出选项
/*
  "module": "ESNext",           // 模块系统：CommonJS, ES6, ESNext等
  "target": "ES2022",           // 目标JavaScript版本
  "lib": ["ES2022", "DOM"],     // 包含的库定义
  "outDir": "./dist",           // 输出目录
  "rootDir": "./src",           // 源文件根目录
  "declaration": true,          // 生成.d.ts声明文件
  "declarationMap": true,       // 声明文件的sourcemap
  "sourceMap": true,            // 生成sourcemap文件
  "inlineSources": true,        // 将源代码嵌入sourcemap
*/

// 3. 类型检查选项
/*
  "noUnusedLocals": true,       // 检查未使用的局部变量
  "noUnusedParameters": true,   // 检查未使用的参数
  "noImplicitReturns": true,    // 检查函数是否总是返回值
  "noFallthroughCasesInSwitch": true, // 检查switch的fallthrough
  "noUncheckedIndexedAccess": true, // 索引访问的额外检查
  "exactOptionalPropertyTypes": true, // 精确的可选属性类型
*/

// 4. 模块解析选项
/*
  "moduleResolution": "bundler", // 模块解析策略
  "baseUrl": "./",              // 基础路径
  "paths": {                    // 路径映射
    "@/*": ["src/*"]
  },
  "rootDirs": ["./src", "./generated"], // 多个根目录
  "typeRoots": ["./node_modules/@types"], // 类型声明位置
  "types": ["node", "jest"],    // 包含的声明包
*/

// 5. JavaScript支持选项
/*
  "allowJs": true,              // 允许JavaScript文件
  "checkJs": true,              // 检查JavaScript文件中的类型
  "maxNodeModuleJsDepth": 1,    // 检查node_modules中JS文件的深度
*/

// 6. 互操作性选项
/*
  "esModuleInterop": true,      // 更好的CommonJS/ES模块互操作
  "allowSyntheticDefaultImports": true, // 允许合成默认导入
  "resolveJsonModule": true,    // 允许导入JSON模块
*/

// 7. 实验性选项
/*
  "experimentalDecorators": true, // 实验性装饰器
  "emitDecoratorMetadata": true,  // 发出装饰器元数据
  "useDefineForClassFields": true, // 使用define进行类字段
*/

// 8. 其他选项
/*
  "skipLibCheck": true,         // 跳过库文件的类型检查
  "forceConsistentCasingInFileNames": true, // 强制文件名大小写一致
  "noEmit": true,               // 不输出文件，只做类型检查
  "incremental": true,          // 增量编译
  "tsBuildInfoFile": "./build/.tsbuildinfo", // 增量编译信息文件
*/

// 常见配置组合
{
  "compilerOptions": {
    // 现代TypeScript项目推荐配置
    "strict": true,
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "lib": ["ES2022", "DOM"],
    
    "outDir": "./dist",
    "rootDir": "./src",
    "declaration": true,
    "sourceMap": true,
    
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    
    // 额外的严格检查
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noImplicitReturns": true
  }
}

// 使用命令行覆盖配置
// tsc --strict false --target ES2015
// 这会覆盖tsconfig.json中的对应选项`,
        description: '编译器选项详解'
      }
    ],
    dimension: 'concepts',
    keywords: ['编译器选项', 'strict', '类型检查', '模块解析', '编译配置'],
    createdAt: new Date(),
    updatedAt: new Date()
  };
}

/**
 * 创建ESLint与Prettier断面
 */
function createEslintPrettierSection(): Section {
  return {
    id: 'eslint-prettier',
    type: 'eslint-prettier',
    title: 'ESLint与Prettier：代码整洁',
    path: 'secret-passages/configuration/eslint-prettier.xhtml',
    environment: {
      dominantEmotion: 'excited',
      visualDescription: '代码像原始材料通过两个精密的机器：一个检查质量（ESLint），一个打磨形状（Prettier）',
      atmosphere: '掌握现代TypeScript项目的代码质量工具，感受到整洁代码的美学'
    },
    introduction: 'TypeScript检查类型正确性，ESLint检查代码质量，Prettier统一代码风格。三个工具各司其职，共同创造优美的代码。',
    phantomNotes: [
      { text: '幽灵观察：TypeScript是幽灵的本质检查（是否成形），ESLint是幽灵行为规范（是否优雅），Prettier是幽灵外观统一（是否美观）。' },
      { text: '工具哲学：让工具做它们擅长的事。TypeScript做类型检查，ESLint做代码质量，Prettier做代码格式。不要用一个工具做所有事。' }
    ],
    codeExamples: [
      {
        code: `// package.json中的依赖
/*
  "devDependencies": {
    "typescript": "^5.0.0",
    "eslint": "^8.0.0",
    "@typescript-eslint/parser": "^6.0.0",
    "@typescript-eslint/eslint-plugin": "^6.0.0",
    "prettier": "^3.0.0",
    "eslint-config-prettier": "^9.0.0",
    "eslint-plugin-prettier": "^5.0.0"
  }
*/

// .eslintrc.js - ESLint配置
module.exports = {
  parser: '@typescript-eslint/parser',
  plugins: ['@typescript-eslint', 'prettier'],
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:prettier/recommended' // 必须放在最后
  ],
  env: {
    node: true,
    es2022: true
  },
  parserOptions: {
    ecmaVersion: 'latest',
    sourceType: 'module',
    project: './tsconfig.json' // 用于类型感知的规则
  },
  rules: {
    // TypeScript特定规则
    '@typescript-eslint/explicit-function-return-type': 'off', // 不强制显式返回类型
    '@typescript-eslint/no-explicit-any': 'warn',           // 警告使用any
    '@typescript-eslint/no-unused-vars': ['error', { 
      'argsIgnorePattern': '^_' 
    }],
    
    // 代码质量规则
    'no-console': 'warn',      // 警告console.log
    'eqeqeq': ['error', 'always'], // 必须使用===和!==
    'curly': ['error', 'all'], // 必须使用大括号
    
    // Prettier集成
    'prettier/prettier': 'error'
  },
  overrides: [
    {
      files: ['*.test.ts', '*.spec.ts'],
      rules: {
        'no-console': 'off' // 测试文件允许console
      }
    }
  ]
};

// .prettierrc.js - Prettier配置
module.exports = {
  semi: true,
  trailingComma: 'es5',
  singleQuote: true,
  printWidth: 100,
  tabWidth: 2,
  useTabs: false,
  bracketSpacing: true,
  arrowParens: 'avoid',
  endOfLine: 'lf'
};

// .prettierignore - Prettier忽略文件
/*
node_modules
dist
coverage
*.min.js
*.d.ts
*/

// package.json脚本
/*
  "scripts": {
    "lint": "eslint src --ext .ts,.tsx",
    "lint:fix": "eslint src --ext .ts,.tsx --fix",
    "format": "prettier --write src",
    "format:check": "prettier --check src",
    "type-check": "tsc --noEmit"
  }
*/

// 编辑器集成（.vscode/settings.json）
/*
{
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": true
  },
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "typescript.preferences.importModuleSpecifier": "non-relative"
}
*/

// 常见ESLint规则解释
/*
  // 代码质量
  'no-var': 'error'                    // 必须使用let/const，不用var
  'prefer-const': 'error'              // 如果可以，使用const而不是let
  'no-multiple-empty-lines': 'error'   // 不允许多个空行
  
  // TypeScript特定
  '@typescript-eslint/consistent-type-imports': 'error' // 统一类型导入方式
  '@typescript-eslint/no-non-null-assertion': 'warn'    // 警告非空断言
  '@typescript-eslint/ban-ts-comment': 'warn'           // 警告TS注释
  
  // 最佳实践
  'no-else-return': 'warn'             // 如果可以，避免else return
  'prefer-template': 'error'           // 优先使用模板字符串
  'object-shorthand': 'error'          // 使用对象简写
*/

// 工作流程
// 1. 写代码
// 2. 保存时自动格式化（Prettier）
// 3. 保存时自动修复ESLint问题
// 4. 手动运行npm run type-check进行类型检查
// 5. 提交前运行所有检查`,
        description: '代码质量工具链'
      }
    ],
    dimension: 'concepts',
    keywords: ['ESLint', 'Prettier', '代码格式化', '代码质量', '开发工具'],
    createdAt: new Date(),
    updatedAt: new Date()
  };
}

/**
 * 创建AI工具介绍断面
 */
function createAIToolsSection(): Section {
  return {
    id: 'ai-tools',
    type: 'ai-tools',
    title: 'AI工具介绍',
    path: 'attic/ai-assistance/ai-tools.xhtml',
    environment: {
      dominantEmotion: 'excited',
      visualDescription: '多个AI助手像不同颜色的光球漂浮在空中，每个有独特的沟通方式和能力',
      atmosphere: '探索AI辅助编程的可能性，感受到与AI协作的新工作方式'
    },
    introduction: 'AI不是要取代程序员，而是要成为程序员的协作伙伴。好的AI协作就像有一个不知疲倦、知识渊博的初级伙伴。',
    phantomNotes: [
      { text: '幽灵观察：AI是新的幽灵种类——数据幽灵。它们不是真正的智能，而是模式的反射器。理解这一点，你就能更好地与它们协作。' },
      { text: '协作心态：不要问AI"写代码"，问AI"帮我理解"、"帮我重构"、"帮我测试"。让AI做辅助工作，你做决策工作。' }
    ],
    codeExamples: [
      {
        code: `// AI辅助编程的典型场景

// 1. 解释代码
// 你的提示："解释这个TypeScript接口的作用："
interface GhostRegistry {
  readonly id: string;
  name: string;
  age?: number;
  haunt(location: string): void;
}

// AI可能回答：
// 这个接口定义了一个幽灵注册表条目的结构：
// - id: 只读字符串，唯一标识符，创建后不能修改
// - name: 字符串，幽灵的名字，可以修改
// - age: 可选数字，幽灵的年龄（可能未知）
// - haunt: 方法，幽灵出没在指定位置

// 2. 生成代码
// 你的提示："创建一个TypeScript类实现上面的GhostRegistry接口"
// AI可能生成：
class BasicGhost implements GhostRegistry {
  readonly id: string;
  name: string;
  age?: number;
  
  constructor(id: string, name: string, age?: number) {
    this.id = id;
    this.name = name;
    this.age = age;
  }
  
  haunt(location: string) {
    console.log(\`Ghost \${this.name} haunts \${location}\`);
  }
}

// 3. 重构代码
// 你的代码：
function processGhosts(ghosts: any[]) {
  let result = [];
  for (let i = 0; i < ghosts.length; i++) {
    if (ghosts[i].age > 100) {
      result.push(ghosts[i].name);
    }
  }
  return result;
}

// 你的提示："用现代TypeScript重构这个函数，添加适当的类型"
// AI可能生成：
function processGhosts(ghosts: Array<{name: string; age?: number}>): string[] {
  return ghosts
    .filter((ghost): ghost is {name: string; age: number} => 
      ghost.age !== undefined && ghost.age > 100
    )
    .map(ghost => ghost.name);
}

// 4. 调试代码
// 你的错误：
// Error: Property 'name' does not exist on type 'Ghost | undefined'
// 你的提示："解释这个TypeScript错误，并给出修复建议"
// AI可能回答：
// 这个错误表示你正在尝试访问可能是undefined的值的属性。
// 修复方法1: 添加类型守卫
// 修复方法2: 使用可选链操作符 ghost?.name
// 修复方法3: 提供默认值 ghost?.name ?? 'Unknown'

// 5. 学习概念
// 你的提示："用简单例子解释TypeScript中的条件类型"
// AI可能生成：
type IsString<T> = T extends string ? true : false;
type Test1 = IsString<"hello">;  // true
type Test2 = IsString<number>;   // false

// 常用AI工具：
// - GitHub Copilot: 代码补全和生成
// - ChatGPT: 对话和解释
// - Claude: 长文本分析和推理
// - Cursor: 集成AI的IDE
// - Tabnine: 另一个代码补全工具

// 工作流程建议：
// 1. 自己先尝试写代码框架
// 2. 用AI填充细节
// 3. 理解AI生成的代码
// 4. 修改和优化
// 5. 让AI解释复杂的部分`,
        description: 'AI编程助手介绍'
      }
    ],
    dimension: 'concepts',
    keywords: ['AI编程', 'GitHub Copilot', 'ChatGPT', '代码生成', 'AI辅助'],
    createdAt: new Date(),
    updatedAt: new Date()
  };
}

/**
 * 创建提示工程基础断面
 */
function createPromptEngineeringSection(): Section {
  return {
    id: 'prompt-engineering',
    type: 'prompt-engineering',
    title: '提示工程基础',
    path: 'attic/ai-assistance/prompt-engineering.xhtml',
    environment: {
      dominantEmotion: 'excited',
      visualDescription: '与AI对话像发送精确编码的信息包，每个包包含指令、上下文、示例和约束',
      atmosphere: '掌握与AI有效沟通的艺术，感受到清晰表达的力量'
    },
    introduction: '对AI说话不是自然对话，是精确的指令编写。好的提示就像好的代码：清晰、具体、有结构。',
    phantomNotes: [
      { text: '幽灵观察：提示工程是教AI如何看见幽灵。你描述幽灵的方式决定AI理解幽灵的方式。模糊的描述产生模糊的幽灵，精确的描述产生精确的幽灵。' },
      { text: '提示公式：角色 + 任务 + 上下文 + 约束 + 示例 + 格式。不一定需要全部，但包含越多，结果越好。' }
    ],
    codeExamples: [
      {
        code: `// 差的提示 vs 好的提示

// 差的提示：模糊
"写一个TypeScript函数"

// 好的提示：具体
"""
你是一个TypeScript专家。创建一个处理幽灵数据的函数。

要求：
1. 函数名为 filterOldGhosts
2. 接收 Ghost 对象数组
3. 返回年龄超过100岁的幽灵名字数组
4. 使用现代TypeScript特性
5. 添加适当的类型注释
6. 包含使用示例

Ghost接口定义：
interface Ghost {
  id: string;
  name: string;
  age?: number;
  location: string;
}
"""

// AI可能生成的响应：
function filterOldGhosts(ghosts: Ghost[]): string[] {
  return ghosts
    .filter((ghost): ghost is Ghost & { age: number } => 
      ghost.age !== undefined && ghost.age > 100
    )
    .map(ghost => ghost.name);
}

// 使用示例：
const ghosts: Ghost[] = [
  { id: '1', name: '卡斯珀', age: 150, location: '阁楼' },
  { id: '2', name: '维多利亚', age: 80, location: '客厅' },
  { id: '3', name: '老幽灵', location: '地下室' } // 没有年龄
];

const oldGhostNames = filterOldGhosts(ghosts); // ['卡斯珀']

// TypeScript特定的提示技巧

// 1. 提供类型定义
"""
基于以下类型定义创建函数：
type Coordinate = { x: number; y: number };
type Ghost = { name: string; position: Coordinate };

创建函数计算两个幽灵之间的距离。
"""

// 2. 指定TypeScript版本
"""
使用TypeScript 5.0+的特性。
不要使用any类型。
使用严格模式。
"""

// 3. 要求特定模式
"""
使用函数式编程风格。
使用async/await处理异步。
使用泛型使函数更通用。
"""

// 4. 包含测试用例
"""
创建函数后，也创建测试用例。
使用Jest风格。
覆盖边界情况。
"""

// 5. 逐步思考提示
"""
让我们一步步思考：
1. 首先分析需求
2. 设计类型定义
3. 实现核心逻辑
4. 添加错误处理
5. 编写测试用例
"""

// 6. 角色扮演提示
"""
你是一个严格的TypeScript编译器。
检查以下代码的类型安全问题。
指出所有潜在问题并提供修复建议。
"""

// 7. 对比提示
"""
比较这两种实现方式的优缺点：
1. 使用类继承
2. 使用组合和接口

从类型安全、可维护性、性能角度分析。
"""

// 迭代改进提示
// 第一轮：基础实现
"创建一个简单的幽灵类"

// 第二轮：改进
"""
基于你刚才创建的类，添加：
1. 访问修饰符（public/private/protected）
2. 抽象方法
3. 接口实现
"""

// 第三轮：优化
"""
现在优化代码：
1. 使用泛型增加灵活性
2. 添加错误处理
3. 改进性能
"""

// 与AI协作的最佳实践：
// 1. 从小开始，逐步增加复杂度
// 2. 要求AI解释生成的代码
// 3. 质疑AI的建议，不要盲目接受
// 4. 让AI从多个角度思考问题
// 5. 保存好的提示作为模板`,
        description: '有效AI提示技巧'
      }
    ],
    dimension: 'concepts',
    keywords: ['提示工程', 'prompt engineering', 'AI沟通', '有效提示', 'ChatGPT'],
    createdAt: new Date(),
    updatedAt: new Date()
  };
}

/**
 * 创建AI协作流程断面
 */
function createAICollaborationSection(): Section {
  return {
    id: 'ai-collaboration',
    type: 'ai-collaboration',
    title: 'AI协作流程',
    path: 'attic/ai-assistance/ai-collaboration.xhtml',
    environment: {
      dominantEmotion: 'excited',
      visualDescription: '程序员和AI像舞蹈伙伴，程序员引导，AI跟随和执行，两者协同创造',
      atmosphere: '掌握与AI协作的完整工作流程，感受到人机协作的效率'
    },
    introduction: 'AI协作不是一次性的代码生成，是持续的对话和迭代。像指导初级开发者一样指导AI：明确、耐心、反馈。',
    phantomNotes: [
      { text: '幽灵观察：AI协作是召唤数据幽灵的仪式。清晰的意图召唤清晰的幽灵，混乱的意图召唤混乱的幽灵。仪式（流程）决定结果的质量。' },
      { text: '协作心态：你是架构师，AI是建造者。你设计蓝图，AI执行细节。你检查质量，AI进行调整。' }
    ],
    codeExamples: [
      {
        code: `// 完整的AI协作工作流程示例

// 阶段1: 需求分析
"""
我计划创建一个幽灵管理系统。
系统需要：
1. 管理幽灵的基本信息（名称、年龄、类型）
2. 追踪幽灵的位置
3. 记录幽灵的活动
4. 生成报告

请帮我设计类型定义。
"""

// AI响应：创建基础类型
type GhostType = 'FRIENDLY' | 'NEUTRAL' | 'HOSTILE';

interface Ghost {
  id: string;
  name: string;
  age?: number;
  type: GhostType;
  location: string;
  lastSeen: Date;
}

// 阶段2: 核心功能
"""
基于上面的类型定义，请创建：
1. GhostManager类，用于管理幽灵集合
2. 添加、删除、查找幽灵的方法
3. 按类型或位置过滤幽灵的方法
"""

// AI响应：创建核心类
class GhostManager {
  private ghosts: Map<string, Ghost> = new Map();
  
  addGhost(ghost: Ghost): void {
    this.ghosts.set(ghost.id, ghost);
  }
  
  // ... 其他方法
}

// 阶段3: 功能扩展
"""
现在添加：
1. 活动日志功能，记录幽灵的每次显现
2. 报告生成功能，生成每日活动报告
3. 数据持久化接口
"""

// AI响应：扩展功能
interface ActivityLog {
  ghostId: string;
  action: string;
  timestamp: Date;
  location: string;
}

class EnhancedGhostManager extends GhostManager {
  private activityLogs: ActivityLog[] = [];
  
  logActivity(ghostId: string, action: string, location: string): void {
    this.activityLogs.push({
      ghostId,
      action,
      timestamp: new Date(),
      location
    });
  }
  
  generateDailyReport(date: Date): string {
    // ... 生成报告
  }
}

// 阶段4: 错误处理和测试
"""
为上面的代码添加：
1. 错误处理（重复ID、无效数据等）
2. 单元测试示例
3. 边界情况处理
"""

// AI响应：添加健壮性
class RobustGhostManager extends EnhancedGhostManager {
  addGhost(ghost: Ghost): void {
    if (this.ghosts.has(ghost.id)) {
      throw new Error(\`Ghost with id \${ghost.id} already exists\`);
    }
    if (ghost.age && ghost.age < 0) {
      throw new Error('Age cannot be negative');
    }
    super.addGhost(ghost);
  }
}

// 测试示例
describe('GhostManager', () => {
  it('should add a ghost', () => {
    const manager = new RobustGhostManager();
    const ghost: Ghost = {
      id: '1',
      name: '卡斯珀',
      type: 'FRIENDLY',
      location: '阁楼',
      lastSeen: new Date()
    };
    
    expect(() => manager.addGhost(ghost)).not.toThrow();
  });
});

// 阶段5: 优化和重构
"""
审查代码，优化以下方面：
1. 性能（大数据量下的表现）
2. 内存使用
3. 代码可读性
4. 类型安全性
"""

// AI响应：优化建议
/*
优化建议：
1. 使用Map而不是对象存储幽灵，提高查找速度
2. 活动日志可能很大，考虑分页或流式处理
3. 添加更多类型守卫和类型谓词
4. 考虑使用不可变数据结构
*/

// 阶段6: 文档和示例
"""
为最终代码创建：
1. API文档
2. 使用示例
3. 常见问题解答
"""

// AI协作的最佳实践清单：

// 1. 分阶段开发
//   - 阶段1: 类型定义
//   - 阶段2: 核心逻辑
//   - 阶段3: 扩展功能
//   - 阶段4: 错误处理
//   - 阶段5: 测试
//   - 阶段6: 优化
//   - 阶段7: 文档

// 2. 保持对话上下文
//   - 每次提示引用之前的对话
//   - 明确说明这是对话的延续
//   - 要求AI记住之前的决定

// 3. 验证和理解
//   - 要求AI解释复杂代码
//   - 要求AI提供替代方案
//   - 自己运行和测试代码
//   - 理解每一行代码的作用

// 4. 反馈循环
//   - 指出AI的错误
//   - 要求AI纠正错误
//   - 提供具体的改进方向
//   - 感谢AI的有用建议

// 5. 工具集成
//   - 在IDE中使用AI（如Cursor）
//   - 使用AI进行代码审查
//   - 使用AI生成测试
//   - 使用AI编写文档

// 记住：AI是工具，不是替代品。
// 你的思考和决策仍然是最重要的。`,
        description: '完整的AI协作流程'
      }
    ],
    dimension: 'concepts',
    keywords: ['AI协作', '工作流程', '迭代开发', '人机协作', '开发流程'],
    createdAt: new Date(),
    updatedAt: new Date()
  };
}

/**
 * 生成所有断面
 */
async function generateAllSections() {
  const sections: Section[] = [
    createBasicTypesSection(),
    createTypeInferenceSection(),
    createAnyUnknownSection(),
    createArraysTuplesSection(),
    createEnumsSection(),
    createInterfaceBasicsSection(),
    createTypeAliasesSection(),
    createOptionalReadonlySection(),
    createExtendsImplementsSection(),
    createGenericBasicsSection(),
    createGenericConstraintsSection(),
    createUtilityTypesSection(),
    createConditionalTypesSection(),
    createClassBasicsSection(),
    createAccessModifiersSection(),
    createInheritanceSection(),
    createAbstractInterfacesSection(),
    createModuleBasicsSection(),
    createImportExportSection(),
    createNamespaceSection(),
    createModuleResolutionSection(),
    createTsconfigBasicsSection(),
    createCompilerOptionsSection(),
    createEslintPrettierSection(),
    createAIToolsSection(),
    createPromptEngineeringSection(),
    createAICollaborationSection()
    // 这里可以添加更多断面
  ];
  
  for (const section of sections) {
    const html = generateSectionHTML(section);
    const outputPath = join('OEBPS', section.path);
    
    // 确保目录存在
    await mkdir(dirname(outputPath), { recursive: true });
    
    // 写入文件
    await writeFile(outputPath, html, 'utf-8');
    console.log(`生成断面: ${outputPath}`);
  }
}

// 运行生成器
if (import.meta.main) {
  generateAllSections().catch(console.error);
}