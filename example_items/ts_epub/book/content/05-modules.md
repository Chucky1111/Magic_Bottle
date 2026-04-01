# 第五章：昏暗环境——模块与命名空间

> 鬼屋的昏暗环境里，不同的幽灵需要不同的领地。阁楼的幽灵不应知道地下室的秘密，走廊的游魂不必关心卧室的私语。模块和命名空间就是代码的领地划分——让不同的概念在各自的昏暗环境中存在，只在必要时跨越边界。

**页边注解** *（魔瓶的低语）*  
*所有代码都在同一个文件中？*  
*那是明亮刺眼的环境。*  
*幽灵喜欢昏暗，喜欢界限分明。*  
*模块就是这样的界限。*

## 情绪魔药：如火焰一般追逐闪电

```feeling
画面：高山，陡峭的悬梯，攀登者的脚步。天边的烈阳与脚下的深渊同时存在。
感受：追逐的兴奋与危险的刺激混合。想要到达高处，又害怕坠落。
```

模块化就是这样的攀登。**分离代码的兴奋感**与**管理依赖的恐惧感**同时存在。

## 模块化编程的意义

想象一下，如果把鬼屋里所有的物品都堆在一个房间里，那会是多么混乱。寻找特定物品几乎是不可能的。同样，如果把所有代码都写在一个文件里，维护和协作也会变得异常困难。

模块化就是将代码分割成独立的、可重用的部分。每个模块关注一个特定的功能，有自己的内部实现，只对外暴露必要的接口。

### 没有模块化的代码

```typescript
// 一个巨大的文件，包含所有代码
// 幽灵相关代码
class Ghost { /* ... */ }
function haunt() { /* ... */ }
const GHOST_TYPES = ['Friendly', 'Mischievous', 'Malevolent'];

// 房间相关代码  
class Room { /* ... */ }
function exploreRoom() { /* ... */ }
const ROOM_TYPES = ['LivingRoom', 'Bedroom', 'Basement'];

// 道具相关代码
class Prop { /* ... */ }
function useProp() { /* ... */ }
const PROP_CATEGORIES = ['Furniture', 'Decoration', 'Mysterious'];

// 几百行甚至几千行代码...
```

这样的代码难以阅读、难以维护、难以测试，也难以与他人协作。

### 模块化的代码

```typescript
// ghost.ts - 幽灵模块
export class Ghost { /* ... */ }
export function haunt() { /* ... */ }
export const GHOST_TYPES = ['Friendly', 'Mischievous', 'Malevolent'];

// room.ts - 房间模块  
export class Room { /* ... */ }
export function exploreRoom() { /* ... */ }
export const ROOM_TYPES = ['LivingRoom', 'Bedroom', 'Basement'];

// prop.ts - 道具模块
export class Prop { /* ... */ }
export function useProp() { /* ... */ }
export const PROP_CATEGORIES = ['Furniture', 'Decoration', 'Mysterious'];

// main.ts - 主文件，导入和使用各个模块
import { Ghost, haunt } from './ghost';
import { Room, exploreRoom } from './room';
import { Prop } from './prop';
```

模块化让代码结构清晰，每个文件都有明确的职责，易于理解和维护。

## 导出与导入

### 命名导出与导入

```typescript
// 📁 ghost.ts - 导出多个内容
export class Ghost {
  constructor(public name: string) {}
}

export function createGhost(name: string): Ghost {
  return new Ghost(name);
}

export const DEFAULT_GHOST_NAME = "卡斯珀";

// 📁 main.ts - 导入特定内容
import { Ghost, createGhost, DEFAULT_GHOST_NAME } from './ghost';

const ghost1 = new Ghost("胖胖");
const ghost2 = createGhost(DEFAULT_GHOST_NAME);
```

### 默认导出与导入

每个模块可以有一个默认导出：

```typescript
// 📁 Ghost.ts - 默认导出一个类
export default class Ghost {
  constructor(public name: string) {}
  
  haunt(): void {
    console.log(`${this.name} 正在出没...`);
  }
}

// 📁 main.ts - 导入默认导出
import Ghost from './Ghost';

const casper = new Ghost("卡斯珀");
casper.haunt();
```

### 重命名导入

```typescript
// 📁 main.ts - 重命名导入
import { Ghost as Specter } from './ghost';
import { createGhost as spawnGhost } from './ghost';

const ghost = new Specter("幽灵");
const another = spawnGhost("另一个");
```

### 导入所有内容

```typescript
// 📁 main.ts - 导入所有内容到一个命名空间
import * as GhostModule from './ghost';

const ghost = new GhostModule.Ghost("卡斯珀");
const another = GhostModule.createGhost("胖胖");
```

## 模块的重新导出

有时，你可能想要创建一个“入口模块”，重新导出其他模块的内容：

```typescript
// 📁 ghost-house/index.ts - 入口文件
export { Ghost, createGhost } from './ghost';
export { Room, exploreRoom } from './room';
export { Prop } from './prop';
export * from './utils'; // 重新导出所有内容

// 📁 main.ts - 从入口文件导入
import { Ghost, Room, Prop } from './ghost-house';
```

## 模块解析

TypeScript 模块可以解析为不同的模块系统：

### CommonJS（Node.js 默认）

```typescript
// 导出
export = {
  Ghost: Ghost,
  createGhost: createGhost
};

// 导入
import ghostModule = require('./ghost');
```

### ES 模块（现代 JavaScript 标准）

```typescript
// 导出
export { Ghost, createGhost };

// 导入
import { Ghost } from './ghost';
```

### UMD（通用模块定义）

```typescript
// TypeScript 会自动处理 UMD 模块
export class Ghost { /* ... */ }
```

## 命名空间：历史的产物

命名空间是 TypeScript 早期用于组织代码的方式，现在大多被模块取代，但在某些情况下仍然有用。

### 定义命名空间

```typescript
// 📁 ghost-house.ts
namespace GhostHouse {
  export class Ghost {
    constructor(public name: string) {}
  }
  
  export namespace Rooms {
    export class LivingRoom {
      static readonly TYPE = "客厅";
    }
    
    export class Bedroom {
      static readonly TYPE = "卧室";
    }
  }
}

// 使用命名空间
const ghost = new GhostHouse.Ghost("卡斯珀");
const roomType = GhostHouse.Rooms.LivingRoom.TYPE;
```

### 命名空间与模块的区别

| 特性 | 模块 | 命名空间 |
|------|------|----------|
| 作用域 | 文件作用域 | 全局或命名空间作用域 |
| 组织方式 | 基于文件系统 | 基于代码组织 |
| 依赖管理 | 显式导入/导出 | 隐式可用 |
| 现代性 | 现代标准 | 传统方式 |
| 推荐使用 | ✅ 大多数情况 | ⚠️ 特殊情况 |

## 模块的最佳实践

### 1. 一个文件一个主要导出

```typescript
// ✅ 好：一个文件一个类
// ghost.ts
export default class Ghost { /* ... */ }

// ❌ 不好：一个文件多个不相关的导出
// utils.ts
export class Ghost { /* ... */ }
export function calculateTotal() { /* ... */ }
export const API_URL = "https://api.example.com";
```

### 2. 使用明确的导入路径

```typescript
// ✅ 好：明确的相对路径
import { Ghost } from './models/ghost';
import { API } from '../utils/api';

// ❌ 不好：过于泛化的路径
import { Ghost } from 'ghost'; // 可能解析错误
```

### 3. 避免循环依赖

```typescript
// ❌ 避免：模块 A 导入 B，B 又导入 A
// a.ts
import { bFunc } from './b';
export function aFunc() { bFunc(); }

// b.ts  
import { aFunc } from './a';
export function bFunc() { aFunc(); }
```

### 4. 使用索引文件组织模块

```typescript
// 📁 models/index.ts
export { default as Ghost } from './ghost';
export { default as Room } from './room';
export { default as Prop } from './prop';

// 📁 main.ts
import { Ghost, Room, Prop } from './models';
```

## 练习：幽灵档案馆——昏暗环境中的模块划分

不要做电商系统。太明亮，太商业。

让我们构建一个**幽灵档案馆**，一个记录超自然现象的模块化系统。每个模块都像鬼屋的一个房间，有自己的秘密，只通过狭窄的门廊（导出）与其他房间连接。

**页边注解** *（魔瓶的指引）*  
*模块化不是技术需求，是生存需求。*  
*在昏暗环境中，界限就是安全。*  
*每个模块应该像鬼屋的一个房间：*  
*有自己的氛围，自己的规则。*

### 需求：幽灵档案馆的模块系统

我们需要以下核心模块：
1. **幽灵档案模块** (`/entities/`) - 幽灵实体定义
2. **出没记录模块** (`/hauntings/`) - 目击和事件记录  
3. **神秘事件模块** (`/phenomena/`) - 超自然现象分类
4. **档案馆主模块** (`/archive/`) - 协调所有模块

### 步骤 1：创建模块化目录结构

```
ghost-archive/
├── src/
│   ├── entities/           # 幽灵实体模块
│   │   ├── Ghost.ts        # 幽灵类
│   │   ├── Spirit.ts       # 精魂类  
│   │   ├── Poltergeist.ts  # 骚灵类
│   │   └── index.ts        # 实体模块入口
│   ├── hauntings/          # 出没记录模块
│   │   ├── Haunting.ts     # 出没事件类
│   │   ├── Sighting.ts     # 目击记录类
│   │   ├── services/       # 服务子模块
│   │   │   ├── Recorder.ts # 记录服务
│   │   │   └── index.ts
│   │   └── index.ts        # 出没模块入口
│   ├── phenomena/          # 现象模块
│   │   ├── categories/     # 分类子模块
│   │   │   ├── Apparition.ts
│   │   │   ├── Ectoplasm.ts
│   │   │   └── index.ts
│   │   ├── Phenomenon.ts   # 现象基类
│   │   └── index.ts        # 现象模块入口
│   ├── utils/              # 工具模块
│   │   ├── formatters.ts   # 格式化工具
│   │   ├── validators.ts   # 验证工具
│   │   └── index.ts        # 工具模块入口
│   └── main.ts             # 应用程序入口
└── tsconfig.json           # TypeScript配置
```

### 步骤 2：实体模块 - 定义幽灵类型

```typescript
// 📁 src/entities/Ghost.ts
export type GhostType = 'residual' | 'intelligent' | 'poltergeist';

export default class Ghost {
  constructor(
    public readonly id: string,
    public name: string,
    public type: GhostType,
    private secrets: string[] = []
  ) {}
  
  // 公共方法：获取基础信息
  public getInfo(): string {
    return `${this.name} (${this.type}幽灵)`;
  }
  
  // 公共方法：分享一个秘密
  public revealSecret(): string | null {
    if (this.secrets.length === 0) return null;
    return this.secrets[Math.floor(Math.random() * this.secrets.length)];
  }
  
  // 私有方法：只有类内部可用
  private addSecret(secret: string): void {
    this.secrets.push(secret);
  }
}

// 📁 src/entities/Spirit.ts  
import Ghost, { GhostType } from './Ghost';

export default class Spirit extends Ghost {
  constructor(
    id: string,
    name: string,
    public elementalType: 'air' | 'water' | 'fire' | 'earth'
  ) {
    super(id, name, 'intelligent');
  }
  
  // 精魂特有的方法
  public manifest(): string {
    return `${this.name} 以${this.elementalType}元素的形式显现`;
  }
}

// 📁 src/entities/index.ts - 实体模块入口
export { default as Ghost, type GhostType } from './Ghost';
export { default as Spirit } from './Spirit';
export { default as Poltergeist } from './Poltergeist'; // 假设已定义
```

**页边注解** *（模块化的思考）*  
*为什么分开文件？*  
*`Ghost.ts` 定义了基础幽灵*  
*`Spirit.ts` 扩展了它*  
*`index.ts` 是这个小世界的门廊*  
*外部只需要知道这个门廊*

### 步骤 3：出没记录模块 - 事件记录

```typescript
// 📁 src/hauntings/Haunting.ts
import type { Ghost } from '../entities';

export interface HauntingLocation {
  place: string;
  coordinates?: [number, number];
  atmosphere: 'chilling' | 'oppressive' | 'calm' | 'chaotic';
}

export default class Haunting {
  private static nextId = 1;
  
  public readonly id: number;
  public readonly timestamp: Date;
  public intensity: number; // 1-10
  
  constructor(
    public ghost: Ghost,
    public location: HauntingLocation,
    public description: string,
    intensity: number = 5
  ) {
    this.id = Haunting.nextId++;
    this.timestamp = new Date();
    this.intensity = Math.max(1, Math.min(10, intensity)); // 限制范围
  }
  
  // 格式化显示
  public format(): string {
    const intensityStars = '★'.repeat(this.intensity) + '☆'.repeat(10 - this.intensity);
    return `
事件 #${this.id}
幽灵: ${this.ghost.getInfo()}
地点: ${this.location.place}
氛围: ${this.location.atmosphere}
强度: ${intensityStars}
时间: ${this.timestamp.toLocaleString()}
描述: ${this.description}
    `.trim();
  }
}

// 📁 src/hauntings/services/Recorder.ts
import Haunting, { type HauntingLocation } from '../Haunting';
import type { Ghost } from '../../entities';

export default class Recorder {
  private records: Haunting[] = [];
  
  // 记录新的出没事件
  public recordHaunting(
    ghost: Ghost,
    location: HauntingLocation,
    description: string,
    intensity?: number
  ): Haunting {
    const haunting = new Haunting(ghost, location, description, intensity);
    this.records.push(haunting);
    console.log(`📝 已记录出没事件 #${haunting.id}`);
    return haunting;
  }
  
  // 获取所有记录
  public getAllRecords(): Haunting[] {
    return [...this.records]; // 返回副本
  }
  
  // 按强度过滤
  public getIntenseRecords(threshold: number = 7): Haunting[] {
    return this.records.filter(h => h.intensity >= threshold);
  }
}

// 📁 src/hauntings/index.ts - 出没模块入口
export { default as Haunting, type HauntingLocation } from './Haunting';
export { default as Sighting } from './Sighting'; // 假设已定义
export { default as Recorder } from './services/Recorder';
export * from './services'; // 重新导出服务子模块的所有内容
```

### 步骤 4：工具模块 - 跨越边界的工具

```typescript
// 📁 src/utils/formatters.ts
export function formatGhostName(ghostInfo: string): string {
  return `👻 ${ghostInfo}`;
}

export function formatIntensity(intensity: number): string {
  if (intensity <= 3) return '轻微';
  if (intensity <= 6) return '中等';
  if (intensity <= 8) return '强烈';
  return '极端';
}

export function formatDateForArchive(date: Date): string {
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
}

// 📁 src/utils/validators.ts
export function isValidIntensity(intensity: number): boolean {
  return Number.isInteger(intensity) && intensity >= 1 && intensity <= 10;
}

export function isValidLocation(location: any): boolean {
  return (
    location &&
    typeof location.place === 'string' &&
    location.place.trim().length > 0
  );
}

// 📁 src/utils/index.ts - 工具模块入口
export * from './formatters';
export * from './validators';
```

### 步骤 5：主文件 - 连接所有模块

```typescript
// 📁 src/main.ts
// 从各个模块导入所需内容
import { Ghost, Spirit } from './entities';
import { Haunting, Recorder, type HauntingLocation } from './hauntings';
import { formatGhostName, formatDateForArchive } from './utils';

// 创建幽灵实体
const casper = new Ghost('casper-001', '卡斯珀', 'intelligent', [
  '其实很喜欢饼干',
  '害怕真正的黑暗'
]);

const zephyr = new Spirit('zephyr-001', '西风', 'air');

// 创建记录器
const recorder = new Recorder();

// 记录出没事件
const libraryHaunting: HauntingLocation = {
  place: '老宅图书馆',
  atmosphere: 'chilling'
};

recorder.recordHaunting(
  casper,
  libraryHaunting,
  '书籍自动翻页，温度骤降10度',
  6
);

const atticHaunting: HauntingLocation = {
  place: '阁楼',
  atmosphere: 'oppressive',
  coordinates: [45.3, 12.7]
};

recorder.recordHaunting(
  zephyr,
  atticHaunting,
  '风声如低语，灰尘形成旋涡',
  8
);

// 显示记录
console.log('=== 幽灵档案馆记录 ===\n');

const allRecords = recorder.getAllRecords();
allRecords.forEach(record => {
  console.log(record.format());
  console.log('---');
});

// 使用工具函数
console.log('\n📊 统计信息:');
console.log(`幽灵: ${formatGhostName(casper.getInfo())}`);
console.log(`精魂: ${formatGhostName(zephyr.manifest())}`);
console.log(`记录时间: ${formatDateForArchive(new Date())}`);

// 显示强烈事件
const intenseRecords = recorder.getIntenseRecords(7);
console.log(`\n⚠️  强烈出没事件: ${intenseRecords.length} 个`);
```

### 步骤 6：TypeScript 模块配置

```json
// 📁 tsconfig.json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "ESNext",          // 使用现代ES模块
    "moduleResolution": "node",  // Node.js风格的模块解析
    "outDir": "./dist",          // 输出目录
    "rootDir": "./src",          // 源代码目录
    "baseUrl": "./src",          // 基础路径
    "paths": {                   // 路径映射（可选）
      "@entities/*": ["entities/*"],
      "@hauntings/*": ["hauntings/*"],
      "@utils/*": ["utils/*"]
    },
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "declaration": true,         // 生成类型声明文件
    "declarationMap": true       // 声明文件源映射
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist", "**/*.test.ts"]
}
```

**页边注解** *（配置的意义）*  
*`module: "ESNext"` - 使用最新的模块系统*  
*`moduleResolution: "node"` - 像Node.js一样解析模块*  
*`baseUrl` 和 `paths` - 创建模块别名*  
*这样导入会更清晰：*  
*`import { Ghost } from "@entities";`*

## AI 辅助提示：用幽灵语言描述模块结构

当与 AI 合作设计模块化结构时，不要用干瘪的技术术语。用**幽灵的语言**描述：

> “我需要为幽灵档案馆创建模块化结构。要有这些模块：
> - `entities/`：幽灵实体（Ghost、Spirit、Poltergeist），每个在单独文件
> - `hauntings/`：出没记录（Haunting、Sighting），包含 `services/` 子模块
> - `phenomena/`：超自然现象分类，有嵌套的 `categories/` 子模块
> - `utils/`：工具函数（formatters、validators）
> 
> 每个模块要有 `index.ts` 入口文件，明确导出公共API。主文件要导入所有模块并展示它们如何协作。”

AI 会理解这种**叙事驱动**的需求，生成更有趣、更符合主题的代码。

**页边注解** *（魔瓶的经验）*  
*AI 不理解"好的模块化"。*  
*AI 理解"鬼屋里不同的房间"。*  
*用隐喻，不要用术语。*

## 本章小结：昏暗环境中的生存法则

模块化不是在组织代码，是在**创造生存环境**：

1. **领地划分**：每个模块像鬼屋的一个房间，有自己的规则和秘密
2. **界限保护**：`export` 是门廊，`private` 是锁着的门，`protected` 是家族区域
3. **环境适应**：不同的模块适应不同的"昏暗度"（复杂度）
4. **路径系统**：导入/导出是房间之间的走廊
5. **入口控制**：`index.ts` 是每个区域的前厅

记住魔瓶的世界观：“没有无法塑造的规则，只有无法表达的现状。”模块系统就是你塑造的规则——定义了代码如何组织、如何交互、如何隐藏或暴露。

**情绪魔药回顾**：如火焰一般追逐闪电。模块化的兴奋感来自于清晰的分离，恐惧感来自于依赖管理。这种矛盾正是编程的魅力。

在下一章中，我们将成为"守夜人"——学习配置 TypeScript 编译器，守护这个幽灵世界的边界和规则。

> 下一章：[第六章：守夜人——编译器配置与工具链](../content/06-configuration.md)