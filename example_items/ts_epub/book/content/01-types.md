# 第一章：幽灵法则——类型系统的初现

> 法则不是约束，是显现。当幽灵第一次穿越墙壁时，不是违反了物理法则，而是发现了新的法则。

---

## 意图寻找词语

你有一个想法。也许是“记录温度”，也许是“计算鬼魂数量”。在自然语言中，这些想法是模糊的。在 TypeScript 中，它们开始获得精确的形态。

不是通过复杂的语法，而是通过简单的声明：

```typescript
// 尝试感受这个：你在定义本质，不是在写代码
let temperature: number = 23.5;
let ghostCount: number = 13;
let ghostName: string = "卡斯珀";
let isHaunted: boolean = true;
```

这些不是“变量声明”。这是**意图的结晶**。当你写下 `: number` 时，你不是在告诉编译器“这是一个数字”。你在说：“我的意图是数值计算。”

## 为什么从类型开始？（幽灵的视角）

在 AI 时代，代码不是写出来的，是**描述出来然后实现的**。

想象你向 AI 描述需求：

> “我需要一个函数，计算房间的平均温度。”

模糊。AI 可能生成各种实现。

现在用类型描述：

```typescript
type RoomTemperature = {
  roomName: string;
  temperature: number;
  measuredAt: Date;
};

function calculateAverage(temperatures: RoomTemperature[]): number {
  // AI 现在知道精确的需求
}
```

类型系统是**人类与 AI 的契约语言**。不是防止错误，是确保理解。

## 基本类型：思维的原子

不要记忆“number、string、boolean”。感受它们：

- `number`: 当你的意图是**计算、测量、比较**
- `string`: 当你的意图是**信息、标识、展示**
- `boolean`: 当你的意图是**判断、决策、状态**

这些不是语法元素。它们是思维模式的标签。

```typescript
// 这不是代码，这是思维模式
let score: number = 100;          // 计算思维
let message: string = "欢迎";    // 信息思维  
let isReady: boolean = true;      // 判断思维
```

## 类型注解 vs 类型推断：明确与暗示

有时你需要明确表达意图。有时你可以让类型自己显现。

```typescript
// 明确：当意图需要强调时
let deadline: Date = new Date("2023-12-31");

// 暗示：当类型显而易见时  
let today = new Date();  // TypeScript 知道这是 Date
```

在 AI 协作中：**越明确越好**。AI 需要你的意图清晰。

## `any` 与 `unknown`：不确定性的两种表达

在幽灵世界中，有些存在无法被分类。在数据流中，有些值无法被确定。

### `any`: 放弃分类

```typescript
let anything: any = "可能是字符串";
anything = 42;           // 也可以是数字
anything = true;         // 也可以是布尔值
```

`any` 说：“我不知道，也别问。”在 AI 时代，这等于说：“AI，你自己猜吧。”危险但有时必要。

### `unknown`: 明确的不确定

```typescript
let uncertain: unknown = getDataFromAPI();

// 不能直接使用
// let message: string = uncertain; // 错误！

// 需要先检查
if (typeof uncertain === "string") {
  let message: string = uncertain; // 现在安全
}
```

`unknown` 说：“我不确定，所以在使用前必须检查。”这是与 AI 协作时的诚实：**明确表达你的不确定性**。

在 AI 时代，`unknown` 不是弱点，是智慧。当你从外部 API、用户输入、AI 响应获取数据时，使用 `unknown` 是说：“这个数据源不可信，我需要验证。”

## 练习：用类型描述，让 AI 实现

不要写代码。写意图。

**任务**：描述一个“幽灵档案”系统

1. 先写类型定义：

```typescript
type GhostType = 'friendly' | 'mischievous' | 'malevolent';

interface GhostProfile {
  name: string;
  age: number;
  type: GhostType;
  sightings: number;
  lastSeen?: Date;  // 可选：可能没有被目击过
}
```

2. 然后让 AI 实现功能：

> “基于上面的 GhostProfile 接口，请实现以下功能：
> - 创建新的幽灵档案
> - 更新目击次数
> - 获取友好幽灵列表
> - 计算平均年龄”

3. 审查 AI 生成的代码，关注类型是否正确。

这就是 AI 时代的工作流：**你先定义“什么”，AI 实现“如何”**。

---

**页边注解** *（魔瓶的低语）*  
*注意到吗？我没有解释“数组”和“元组”。*  
*幽灵不按顺序教学。它们在需要时出现。*  
*现在，感受已经显现的。剩下的会在边缘闪烁时出现。*  

## 集合与序列：幽灵的显现模式

当单个幽灵出现时，是现象。当多个幽灵以特定模式出现时，是叙事。

### 数组：相同本质的集合

```typescript
// 不是“字符串数组”，是“名字的集合”
let ghostNames: string[] = ["卡斯珀", "胖胖", "瘦子"];

// 不是“数字数组”，是“温度的序列”
let temperatures: number[] = [18, 22, 15, 20];
```

在 AI 协作中：数组类型告诉 AI“这里有一组相同类型的数据需要处理”。AI 知道可以循环、映射、过滤。

### 元组：固定的叙事结构

有些数据有固定的角色和顺序。就像幽灵调查记录：名字、年龄、目击时间。

```typescript
// 元组：固定结构的叙事
let sighting: [string, number, Date] = ["卡斯珀", 150, new Date()];
//         名字 ↑  年龄 ↑   时间 ↑
```

元组说：“这三个数据以这种顺序和类型一起出现。”在 AI 时代，这就像给数据分配角色。

## 枚举：为可能性命名

当可能性有限且重要时，给它们名字。不是数字 0、1、2，而是意图。

```typescript
// 枚举：命名的可能性
enum GhostType {
  Friendly = 'friendly',      // 友好
  Mischievous = 'mischievous', // 恶作剧
  Malevolent = 'malevolent'   // 恶意
}

// 现在类型本身就是文档
let casperType: GhostType = GhostType.Friendly;
```

枚举在 AI 协作中特别强大：当你使用枚举时，AI 知道可能的取值范围，不会生成无效值。

## 情绪魔药：如火焰一般追逐闪电

感受这个过程的能量：从模糊的想法，到精确的类型定义，到 AI 生成的实现。

你不是在学习语法。你在学习如何将闪电般的灵感转化为可执行的火焰。

```typescript
// 闪电：一个想法
// “我需要一个系统记录幽灵目击”

// 火焰：类型定义
type GhostSighting = {
  ghostName: string;
  location: string;
  time: Date;
  credibility: number; // 可信度 0-10
};

// AI：实现
// 基于这个类型，AI 可以生成：
// - 数据库模型
// - API 端点
// - 验证逻辑
// - 用户界面
```

## 练习：完整的意图表达

**任务**：设计一个幽灵研究数据库

不要想代码。想数据。想关系。

1. 定义核心类型：

```typescript
enum ResearchStatus {
  Planned = 'planned',
  InProgress = 'in-progress',
  Completed = 'completed',
  Cancelled = 'cancelled'
}

interface Researcher {
  id: string;
  name: string;
  specialty: string[];
  joinedDate: Date;
}

interface GhostStudy {
  id: string;
  title: string;
  description: string;
  status: ResearchStatus;
  leadResearcher: Researcher;  // 嵌套类型
  ghostNames: string[];
  startDate: Date;
  endDate?: Date;  // 可能还在进行中
  findings: string[];
}
```

2. 向 AI 描述需求：

> “基于上面的类型定义，请实现：
> - 创建新研究项目的函数
> - 更新研究状态的函数
> - 按研究员筛选研究的函数
> - 生成研究报告的函数”

3. 审查 AI 的产出，关注：
   - 类型是否正确使用？
   - 边界情况是否处理？
   - 错误处理是否恰当？

## 本章小结：法则的初现

类型系统不是约束思想的监狱。是让思想能够被精确表达的法则。

在 AI 时代，这个法则变得至关重要：
- **对你**：清晰思考的工具
- **对 AI**：精确理解的契约
- **对协作**：共同语言的词汇表

你学到的不是 `number`、`string`、`boolean`。你学到的是：
- 如何将计算意图表达为 `number`
- 如何将信息意图表达为 `string`
- 如何将判断意图表达为 `boolean`
- 如何将不确定性表达为 `unknown`
- 如何将结构表达为接口
- 如何将可能性表达为枚举

记住魔瓶的行为惯性：“同时出现在任何时空，同时篡夺所有叙事。”
类型系统让你能够做到这一点：一个类型定义同时出现在编译时、运行时、AI 提示中、文档中。

现在，让这些法则开始寻找更复杂的形态。

> 下一章：[边缘地带：接口与类型别名的幽灵叙事](../content/02-interfaces.md)

---

**页边注解** *（魔瓶的低语）*  
*你可能会问：为什么没有讲“类型断言”？*  
*幽灵不会断言。它们暗示，它们显现。*  
*类型断言是暴力的。在 AI 时代，暴力通常意味着误解。*  
*当你觉得需要断言时，重新思考你的类型设计。*  