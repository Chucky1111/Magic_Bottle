# 第三章：时空穿梭——泛型与高级类型

> 幽灵不只有一个名字，不只有一种形态。我在不同的时空被称作不同的存在。泛型就是这种多态性在代码中的体现：同一段代码，适应不同数据类型。

**页边注解** *（魔瓶的低语）*  
*时空不是线性的。*  
*代码可以同时在多个类型维度存在。*  
*泛型不是特性，是本质。*  

## 情绪魔药：轻蔑的嘲弄

```feeling
画面：竞技场看台高处，俯视着下面混乱的战斗。嘴角微微上扬，不是喜悦，而是对笨拙努力的轻蔑。
感受：优越与讽刺混合。看着他人用笨拙的方式解决简单问题，既觉得可笑，又懒得指点。
```

当你看到有人为每种数据类型写重复代码时，会有这种感受。**泛型**就是对这种重复的轻蔑回应：**“为什么为每个类型都写一遍？写一次，让类型适应你。”**

## 泛型函数：幽灵的多重身份

幽灵在不同的观察者面前显现不同形态。对孩子是友好的卡通形象，对研究者是数据记录，对诗人是隐喻。

泛型函数也是如此：**同一逻辑，不同类型。**

```typescript
// 笨拙的方式：为每种类型写一个函数
function getFirstNumber(arr: number[]): number {
  return arr[0];
}

function getFirstString(arr: string[]): string {
  return arr[0];
}

function getFirstGhost(arr: Ghost[]): Ghost {
  return arr[0];
}

// 优雅的方式：一个泛型函数
function firstElement<T>(arr: T[]): T {
  return arr[0];
}

// 使用
const numbers = [1, 2, 3];
const firstNum = firstElement(numbers); // 类型：number

const strings = ["幽灵", "鬼屋", "南瓜"];
const firstStr = firstElement(strings); // 类型：string

const ghosts = [{ name: "卡斯珀" }, { name: "胖胖" }];
const firstGhost = firstElement(ghosts); // 类型：{ name: string }
```

**页边注解** *（魔瓶的嘲讽）*  
*`<T>` 是什么？*  
*类型参数。占位符。*  
*叫它 `T` 还是 `Type` 还是 `ElementType`？*  
*不重要。重要的是它代表“某种类型”。*  

### 多个类型参数：复杂的身份关系

幽灵有时同时以两种身份存在：既是历史人物，又是民间传说。

```typescript
// 交换身份
function swapIdentities<A, B>(pair: [A, B]): [B, A] {
  return [pair[1], pair[0]];
}

// 使用
const ghostAndYear = ["卡斯珀", 1890] as [string, number];
const yearAndGhost = swapIdentities(ghostAndYear); // [number, string]

// 更复杂的例子
function createRelationship<Ghost, Human>(
  ghost: Ghost,
  human: Human,
  bond: string
): { ghost: Ghost; human: Human; bond: string } {
  return { ghost, human, bond };
}

const relationship = createRelationship(
  { name: "白衣女士" },
  { name: "历史学家" },
  "研究对象"
);
// relationship.ghost 类型: { name: string }
// relationship.human 类型: { name: string }
```

## 泛型约束：幽灵的能力范围

不是所有幽灵都能穿墙。不是所有类型都有长度属性。

约束说：**“你可以是多态的，但必须在某个范围内。”**

```typescript
// 问题：这个函数应该能获取长度，但 T 可能没有 length
function problematicLength<T>(item: T): number {
  // return item.length; // 错误：T 可能没有 .length
}

// 解决方案：约束 T 必须具有 length 属性
interface HasLength {
  length: number;
}

function safeLength<T extends HasLength>(item: T): number {
  return item.length; // 现在安全了
}

// 使用
safeLength("幽灵"); // 2 - 字符串有 length
safeLength([1, 2, 3]); // 3 - 数组有 length
safeLength({ length: 10 }); // 10 - 明确有 length 属性
// safeLength(42); // 错误：数字没有 length
```

约束不是限制，是**澄清**。它告诉编译器：“我知道这类数据有什么能力。”

## 泛型接口：契约的模板

API 响应总是有相同结构：成功状态、数据、可选消息。只是数据类型不同。

```typescript
// 泛型接口：相同结构，不同数据类型
interface ApiResponse<Data> {
  success: boolean;
  data: Data;
  message?: string;
  timestamp: Date;
}

// 用于幽灵数据
interface Ghost {
  name: string;
  age: number;
  sightings: number;
}

const ghostResponse: ApiResponse<Ghost> = {
  success: true,
  data: { name: "卡斯珀", age: 150, sightings: 42 },
  timestamp: new Date()
};

// 用于统计数据
const statsResponse: ApiResponse<{ total: number; active: number }> = {
  success: true,
  data: { total: 100, active: 23 },
  message: "数据获取成功",
  timestamp: new Date()
};
```

**页边注解** *（魔瓶的观察）*  
*注意模式：*  
*`ApiResponse<Ghost>` 和 `ApiResponse<Stats>`*  
*相同结构，不同内涵。*  
*这就是抽象的力量。*  

## 泛型类：可变内容的容器

鬼屋的储藏室可以放各种东西：旧家具、日记、奇怪物品。但储藏室本身结构不变。

```typescript
class SpiritContainer<Content> {
  private content: Content;
  private sealed: boolean = false;

  constructor(initialContent: Content) {
    this.content = initialContent;
  }

  inspect(): Content {
    if (this.sealed) {
      throw new Error("容器已封印");
    }
    return this.content;
  }

  replace(newContent: Content): void {
    if (this.sealed) {
      throw new Error("容器已封印，不能替换内容");
    }
    this.content = newContent;
  }

  seal(): void {
    this.sealed = true;
  }
}

// 使用
const diaryContainer = new SpiritContainer({
  title: "鬼屋日记",
  year: 1890,
  pages: 120
});
// diaryContainer.content 类型: { title: string; year: number; pages: number }

const relicContainer = new SpiritContainer("古老的护身符");
// relicContainer.content 类型: string
```

## 条件类型：基于类型的决策

幽灵根据环境决定是否显形：月光充足时显形，黑暗中隐藏。

条件类型根据输入类型决定输出类型：

```typescript
// 基本条件类型
type IsString<T> = T extends string ? true : false;

type Test1 = IsString<"幽灵">; // true
type Test2 = IsString<number>; // false

// 实用例子：提取名字（如果有的话）
type ExtractName<T> = T extends { name: string } ? T["name"] : "无名";

type Ghost = { name: "白衣女士"; age: 200 };
type GhostName = ExtractName<Ghost>; // "白衣女士"

type Number = 42;
type NumberName = ExtractName<Number>; // "无名"
```

### infer 关键字：提取未知类型

有时你需要说：“我不确定这是什么类型，但我想提取它。”

```typescript
// 提取数组元素类型
type ElementType<T> = T extends (infer Element)[] ? Element : T;

type Numbers = number[];
type NumType = ElementType<Numbers>; // number

type Mixed = [string, number, boolean];
type FirstType = ElementType<Mixed>; // string | number | boolean（元组处理不同）

// 提取函数返回类型
type ReturnType<T> = T extends (...args: any[]) => infer R ? R : never;

function getGhostCount(): number { return 42; }
type CountType = ReturnType<typeof getGhostCount>; // number
```

`infer` 是类型级别的模式匹配。它说：“如果 T 匹配这个模式，把匹配的部分叫做 U，然后我用 U 做点什么。”

## 实用工具类型：幽灵的工具箱

TypeScript 提供了一组内置工具类型。它们不是魔法，只是常用模式的简写。

### Partial<T>：部分更新

更新幽灵信息时，可能只修改部分字段。

```typescript
interface Ghost {
  name: string;
  age: number;
  sightings: number;
  location: string;
}

function updateGhost(id: string, updates: Partial<Ghost>) {
  // 只应用提供的字段
  // updates 可能只有 { age: 151 } 或 { location: "阁楼" }
}

updateGhost("ghost-001", { age: 151 }); // 只更新年龄
updateGhost("ghost-002", { 
  name: "新名字", 
  location: "地下室" 
}); // 更新多个字段
```

**页边注解** *（魔瓶的解释）*  
*`Partial<Ghost>` 等同于 `{ name?: string; age?: number; sightings?: number; location?: string; }`*  
*但你不必手动写。*  
*工具类型就是这种便利。*  

### Required<T>：所有字段必填

```typescript
interface OptionalFields {
  name?: string;
  age?: number;
}

type Mandatory = Required<OptionalFields>;
// 等同于 { name: string; age: number; }
```

### Readonly<T>：防止修改

```typescript
interface MutableRecord {
  title: string;
  content: string;
}

type HistoricalRecord = Readonly<MutableRecord>;
// 等同于 { readonly title: string; readonly content: string; }

const record: HistoricalRecord = {
  title: "1890年目击报告",
  content: "看到白衣女士在阳台"
};

// record.title = "新标题"; // 错误：只读属性
```

### Pick<T, K> 和 Omit<T, K>：选择与排除

```typescript
interface CompleteGhost {
  id: string;
  name: string;
  age: number;
  type: string;
  sightings: number;
  description: string;
}

// 只需要基本信息的类型
type BasicInfo = Pick<CompleteGhost, "id" | "name" | "age">;
// { id: string; name: string; age: number; }

// 排除敏感信息的类型  
type PublicInfo = Omit<CompleteGhost, "id" | "description">;
// { name: string; age: number; type: string; sightings: number; }
```

### Record<K, T>：创建映射类型

```typescript
// 幽灵名字到目击次数的映射
type SightingMap = Record<string, number>;

const sightings: SightingMap = {
  "卡斯珀": 42,
  "胖胖": 17,
  "白衣女士": 89
};

// 更严格的版本
type GhostName = "卡斯珀" | "胖胖" | "白衣女士";
type StrictSightingMap = Record<GhostName, number>;

const strictSightings: StrictSightingMap = {
  "卡斯珀": 42,
  "胖胖": 17,
  "白衣女士": 89
  // 不能添加其他名字
};
```

## 练习：让 AI 写泛型代码

**任务**：创建一个灵活的“数据转换管道”系统。

不要写实现。写类型定义和需求描述。

### 步骤 1：定义核心类型
```typescript
// 转换函数类型：接受某种输入，产生某种输出
type Transform<Input, Output> = (input: Input) => Output;

// 数据管道：一系列转换
interface Pipeline<Start, End> {
  transforms: Transform<any, any>[];
  execute(input: Start): End;
}
```

### 步骤 2：描述需求给 AI
> “我需要一个 TypeScript 泛型系统，实现数据转换管道：
> 
> 1. 定义 `Transform<Input, Output>` 类型
> 2. 创建 `Pipeline<Start, End>` 类，可以添加多个转换函数
> 3. 管道应该保证类型安全：每个转换的输出类型必须匹配下一个转换的输入类型
> 4. 实现 `execute` 方法，按顺序应用所有转换
> 5. 添加错误处理：如果转换失败，应该记录错误但继续执行（如果可能）
> 
> 请提供完整实现，包含示例用法。”

### 步骤 3：审查 AI 的代码
检查：
- 泛型参数是否正确使用
- 类型约束是否合理
- 错误处理是否符合类型安全

**页边注解** *（魔瓶的建议）*  
*与 AI 合作时：*  
*1. 你先定义“类型骨架”*  
*2. AI 填充“实现血肉”*  
*3. 你检查“类型正确性”*  
*这是 AI 时代的开发流程。*  

## 本章核心：类型即参数

泛型的本质是：**将类型作为参数传递**。

在 AI 时代，你不需要记住所有工具类型的语法。你需要知道的是：

1. **识别模式**：这段代码是否在处理多种类似类型？
2. **应用泛型**：用类型参数替换具体类型。
3. **添加约束**：明确类型必须满足的条件。
4. **使用工具类型**：利用内置工具减少重复代码。

记住魔瓶的行为惯性：**“同时出现在任何时空，同时篡夺到所有叙事。”**

泛型让你能够“同时出现在多个类型维度”——同一段代码，多种数据类型。

---

**情绪魔药演化**  
*轻蔑的嘲弄 → 理解的微笑*  
*从嘲笑笨拙，到欣赏优雅。*  
*泛型不是炫耀的复杂性，而是隐藏的简洁性。*  

在下一章，我们将探索“篡夺叙事”——类与面向对象。如何让代码不仅处理数据，还模拟行为？

> 下一章：[第四章：篡夺叙事——类与面向对象编程](../content/04-classes.md)