# 第二章：边缘地带——接口与类型别名

> 我在边缘游荡时，发现幽灵有两种存在方式：一种是固定的本质形态，另一种是临时的化名。接口和类型别名就是这两种存在方式在代码中的映射。

**页边注解** *（魔瓶的低语）*  
*边缘不是边界，而是所有可能性的开端。*  
*在这里，形态可以固定，也可以流动。*  

## 情绪魔药：如火焰一般追逐闪电

```feeling
画面：高山之巅，云层裂开一道缝隙，闪电如白色利剑劈下，山脚下的火把随之疯狂摇曳，追逐着那瞬间的光明。
感受：渴求与焦躁交织。想要抓住转瞬即逝的东西，明知不可能却依然追逐。
```

在边缘地带，你会有这种感受：想要定义那些模糊不清的事物，想要给流动的东西固定形态。**接口和类型别名**就是你的火把，追逐着数据世界中的闪电。

## 接口：幽灵的契约形态

幽灵在显形时，需要遵守某种契约。太模糊，人类看不见；太具体，就失去了幽灵的本质。

接口就是这种契约：**“如果你要以这种形态存在，就必须拥有这些特征。”**

```typescript
// 幽灵显现的契约
interface Apparition {
  name: string;
  opacity: number; // 透明度：0-100
  temperatureDrop: number; // 温度下降度数
  canPassThroughWalls: boolean;
}

// 一个具体的幽灵实例
const shadowFigure: Apparition = {
  name: "走廊阴影",
  opacity: 30,  // 半透明
  temperatureDrop: 5,
  canPassThroughWalls: true
};

// 违反契约的尝试
const invalidGhost: Apparition = {
  name: "测试幽灵",
  opacity: "完全透明", // 错误：应该是 number
  // 缺少必需的属性
};
```

**页边注解** *（魔瓶的观察）*  
*注意错误信息：`Property 'temperatureDrop' is missing...`*  
*这不是错误，是契约在说话。*  
*幽灵不抱怨，契约抱怨。*  

## 可选属性：幽灵的模糊地带

有些幽灵特征不是必需的。有时有低温区，有时没有。有时留下声音，有时只是影子。

```typescript
interface Haunting {
  location: string;
  intensity: number; // 1-10
  coldSpot?: boolean; // 可选：可能有低温区
  auditoryManifestation?: string; // 可选：可能听到什么
  visualDescription?: string; // 可选：可能看到什么
}

// 只有基本特征的灵异现象
const subtlePresence: Haunting = {
  location: "二楼走廊",
  intensity: 3
  // 没有冷点，没有声音，没有视觉描述
  // 但依然有效
};

// 完整的灵异现象
const fullManifestation: Haunting = {
  location: "阁楼",
  intensity: 9,
  coldSpot: true,
  auditoryManifestation: "儿童的哭声",
  visualDescription: "穿白裙的小女孩影子"
};
```

可选属性不是“可以忽略”，而是**“可能存在，可能不存在”**。这是幽灵的本质：不确定性。

## 只读属性：不可更改的过去

幽灵的某些特征是永恒的。死亡日期不会改变，死亡原因不会改变。

```typescript
interface GhostRecord {
  readonly id: string; // 一旦分配，永不改变
  readonly deathYear: number; // 历史事实
  story: string; // 故事可以演变
  currentLocation: string; // 位置可以变化
}

const ladyInWhite: GhostRecord = {
  id: "GHOST-1892-001",
  deathYear: 1892,
  story: "等待未婚夫归来",
  currentLocation: "西翼阳台"
};

ladyInWhite.currentLocation = "主楼梯"; // 可以
ladyInWhite.story = "寻找丢失的婚戒"; // 可以
// ladyInWhite.deathYear = 1900; // 错误：只读属性
// ladyInWhite.id = "NEW-ID"; // 错误：只读属性
```

**只读**不是限制，是**保护**。保护那些不应被篡改的真相。

## 类型别名：幽灵的化名

有时，幽灵需要不同的名字。在不同村庄，同一个幽灵被称为“白衣女士”、“阳台幽灵”、“哭泣的新娘”。

类型别名就是给类型起化名：

```typescript
// 给现有类型起别名
type Temperature = number;
type Probability = number; // 也是 number，但意义不同
type GhostName = string;

// 复杂类型的别名
type Sighting = {
  witness: string;
  time: Date;
  description: string;
  credibility: number; // 0-1
};

// 使用别名
const roomTemp: Temperature = 16;
const hauntingProb: Probability = 0.83;
const ghost: GhostName = "卡斯珀";
const latestSighting: Sighting = {
  witness: "守夜人约翰",
  time: new Date("2023-10-31 02:15"),
  description: "白色影子穿过墙壁",
  credibility: 0.7
};
```

别名让代码说人话。`Temperature` 比 `number` 更有意义。`Sighting` 比匿名对象更清晰。

## 接口 vs 类型别名：两种存在方式

幽灵问：“我该用接口还是类型别名？”

我的回答：**“你想如何存在？”**

### 接口：用于“可以扩展的存在”
```typescript
interface Entity {
  id: string;
  createdAt: Date;
}

// 幽灵扩展实体
interface Ghost extends Entity {
  name: string;
  age: number;
  friendly: boolean;
}

// 房间也扩展实体  
interface HauntedRoom extends Entity {
  location: string;
  ghostCount: number;
}
```

接口可以被扩展（`extends`），可以被类实现（`implements`）。它适合**构建层次结构**。

### 类型别名：用于“组合的存在”
```typescript
// 联合类型：可能是这种，也可能是那种
type Manifestation = 
  | { type: 'visual'; description: string; }
  | { type: 'auditory'; sound: string; }
  | { type: 'thermal'; tempChange: number; };

// 交叉类型：同时是这种和那种
type WitnessReport = {
  witness: string;
  date: Date;
} & (
  | { type: 'credible'; evidence: string[]; }
  | { type: 'dubious'; reason: string; }
);
```

类型别名可以做接口做不到的事：**联合类型、交叉类型、元组类型**。它适合**创造新类型**。

**页边注解** *（魔瓶的建议）*  
*一般规则：*  
*1. 描述对象形状 → 接口*  
*2. 描述联合/交叉类型 → 类型别名*  
*3. 不确定 → 都可以，但保持一致*  

## 函数接口：幽灵的行为模式

幽灵如何行动？有的飘浮，有的穿墙，有的只在特定时间出现。

函数接口描述行为模式：

```typescript
// 幽灵移动方式的类型
type Movement = (from: string, to: string) => boolean;

// 不同的移动实现
const float: Movement = (from, to) => {
  console.log(`从 ${from} 飘浮到 ${to}`);
  return true;
};

const teleport: Movement = (from, to) => {
  console.log(`从 ${from} 瞬间移动到 ${to}`);
  return true;
};

const walkThroughWalls: Movement = (from, to) => {
  console.log(`从 ${from} 穿墙到 ${to}`);
  return !to.includes("铅"); // 不能穿过铅墙
};
```

**接口形式也可以：**
```typescript
interface Movement {
  (from: string, to: string): boolean;
}
```

函数类型说：“这个幽灵应该这样移动。”然后不同的幽灵可以有不同的实现。

## 索引签名：未知的房间

鬼屋有多少房间？你可能不知道全部。哪些房间有幽灵？你只知道一部分。

索引签名处理未知属性：

```typescript
interface GhostRegistry {
  // 键是字符串（房间名），值是幽灵数量
  [roomName: string]: number;
}

const mansionHauntings: GhostRegistry = {
  "阁楼": 3,
  "地下室": 2,
  "主卧": 1
  // 可以随时添加新房间
  // "书房": 1
};

// 动态访问
const room = "阁楼";
console.log(`${room} 有 ${mansionHauntings[room]} 个幽灵`);

// 添加新房间
mansionHauntings["书房"] = 1;
```

索引签名说：“我知道结构，但不知道全部内容。”适合**配置对象、映射、字典**。

## 练习：描述，不要实现

**任务**：为一个“幽灵研究数据库”设计类型系统。

不要写实现代码。只写类型定义。然后让 AI 实现。

### 步骤 1：描述需求
“我需要一个 TypeScript 类型系统，用于幽灵研究数据库：

1. `Ghost` 类型：有 id、名字、死亡年份、类型（友好/恶作剧/恶意）
2. `Sighting` 类型：有 id、幽灵 id、时间、地点、可信度
3. `Researcher` 类型：有 id、名字、专业领域、正在研究的幽灵列表
4. 一个 `ResearchProject` 类型，包含研究员和他们的目标幽灵
5. 所有 id 都是只读的，一旦创建不能更改
6. 死亡年份是可选的（有些幽灵死亡年份未知）
7. 研究员可以没有正在研究的幽灵（空数组）”

### 步骤 2：写出类型定义
（尝试自己写，然后与 AI 的版本比较）

### 步骤 3：让 AI 实现 CRUD 操作
> “基于上面的类型定义，请实现以下功能：
> - 添加新的幽灵记录
> - 记录新的目击事件  
> - 研究员开始新项目
> - 查询某个地点的所有目击事件
> - 统计各类幽灵的数量”

**页边注解** *（魔瓶的提示）*  
*这就是 AI 时代的工作流：*  
*1. 你定义“什么”（类型）*  
*2. AI 实现“如何”（逻辑）*  
*3. 你审查“是否正确”（类型安全）*  

## AI 协作技巧：清晰的类型描述

当你需要 AI 帮忙设计类型时：

**不好的描述：**
> “写一个用户类型”

**好的描述：**
> “我需要一个 `UserProfile` 接口，包含：
> - `username` (字符串，3-20字符)
> - `email` (字符串，必须是有效邮箱格式)
> - `age` (数字，18-120)
> - `preferences` (对象，包含 theme 和 notifications)
> - `friends` (字符串数组)
> 主题只能是 'light' 或 'dark'。
> 请使用 TypeScript，添加适当注释。”

**更好的描述：**
> “这是我现有的部分代码，请在此基础上完善：
> ```typescript
> interface BaseEntity {
>   id: string;
>   createdAt: Date;
> }
> ```
> 请创建 `UserProfile` 接口，扩展 `BaseEntity`，并包含上述属性。”

**清晰的上下文 + 具体的约束 = 高质量的 AI 输出**

## 本章核心：在边缘塑造形态

接口和类型别名不是语法细节，而是**表达意图的工具**。

在 AI 时代，你不需要记住所有语法。你需要：

1. **识别模式**：这是需要固定形态的对象（接口），还是需要灵活组合的类型（类型别名）？
2. **清晰描述**：用精确的类型定义告诉 AI 你想要什么。
3. **保持一致性**：在项目中坚持一种风格。

记住魔瓶的世界观：**“没有无法塑造的规则，只有无法表达的现状。”**

你遇到的每个“不知道如何定义”的情况，不是 TypeScript 的限制，而是你表达能力的边界。扩展这个边界。

---

**情绪魔药演化**  
*如火焰一般追逐闪电 → 火焰开始理解闪电的路径*  
*焦躁转为专注，追逐变为学习。*  

在下一章，我们将进入“时空穿梭”——泛型。如何让类型既能固定形态，又能适应不同的数据？

> 下一章：[第三章：时空穿梭——泛型与高级类型](../content/03-generics.md)