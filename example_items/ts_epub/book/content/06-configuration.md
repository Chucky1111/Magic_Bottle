# 第六章：守夜人——编译器配置与工具链

> 幽灵世界需要守夜人。不是防止入侵，而是防止**混乱**。TypeScript 编译器配置就是这样的守夜人——在昏暗的代码环境中巡逻，确保每个幽灵（类型）都在正确的位置，每条走廊（模块）都通向正确的地方。

**页边注解** *（魔瓶的低语）*  
*没有配置的 TypeScript 就像没有守夜人的鬼屋。*  
*幽灵会到处乱跑，墙壁会消失。*  
*秩序需要明确的规则。*  
*配置就是这样的规则手册。*

## tsconfig.json：TypeScript 编译器的配置文件

每个 TypeScript 项目都应该有一个 `tsconfig.json` 文件。这个文件告诉 TypeScript 编译器如何编译你的代码，就像守夜人的规则手册一样。

### 创建基本配置

你可以手动创建 `tsconfig.json`，或者使用 TypeScript 的命令行工具：

```bash
# 生成默认的 tsconfig.json
npx tsc --init
```

这会创建一个包含所有选项（大部分被注释掉）的配置文件。让我们来看一个实用的配置示例：

```json
{
  "compilerOptions": {
    // 目标 JavaScript 版本
    "target": "ES2020",
    
    // 模块系统
    "module": "ESNext",
    
    // 模块解析策略
    "moduleResolution": "node",
    
    // 输出目录
    "outDir": "./dist",
    
    // 源代码目录
    "rootDir": "./src",
    
    // 严格的类型检查
    "strict": true,
    
    // 允许导入 JSON 文件
    "resolveJsonModule": true,
    
    // 启用 ES 模块互操作性
    "esModuleInterop": true,
    
    // 跳过库文件检查（提高编译速度）
    "skipLibCheck": true,
    
    // 强制文件名大小写一致
    "forceConsistentCasingInFileNames": true,
    
    // 生成声明文件
    "declaration": true,
    "declarationDir": "./dist/types"
  },
  
  // 包含的文件
  "include": [
    "src/**/*"
  ],
  
  // 排除的文件
  "exclude": [
    "node_modules",
    "dist",
    "**/*.test.ts",
    "**/*.spec.ts"
  ]
}
```

## 重要配置项解析

### 目标版本（target）

```json
{
  "compilerOptions": {
    "target": "ES2020"
  }
}
```

这个选项决定了编译后的 JavaScript 应该符合哪个 ECMAScript 版本。常见的选择有：

- `ES5`：兼容最旧的浏览器
- `ES2015`（ES6）：现代浏览器支持
- `ES2020`：最新的 JavaScript 特性
- `ESNext`：最新的提案特性

在 AI 时代，你可以让 AI 根据你的目标环境推荐合适的版本。

### 模块系统（module）

```json
{
  "compilerOptions": {
    "module": "ESNext"
  }
}
```

这个选项决定了编译后的模块代码使用哪种模块系统。常见的选择有：

- `CommonJS`：Node.js 的默认模块系统
- `ESNext`：现代 JavaScript 模块（推荐）
- `UMD`：通用模块定义
- `AMD`：异步模块定义

### 严格模式（strict）

```json
{
  "compilerOptions": {
    "strict": true
  }
}
```

`strict: true` 会启用所有严格的类型检查选项。对于新项目，强烈推荐启用。它包括：

- `noImplicitAny`：不允许隐式的 `any` 类型
- `strictNullChecks`：严格的 null 检查
- `strictFunctionTypes`：严格的函数类型检查
- 等等...

如果你从 JavaScript 迁移到 TypeScript，可以先禁用严格模式，逐步修复类型错误。

### 路径映射（paths）

```json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"],
      "@models/*": ["src/models/*"],
      "@utils/*": ["src/utils/*"]
    }
  }
}
```

路径映射让你可以使用更短的导入路径：

```typescript
// 使用路径映射前
import { Product } from '../../models/product';

// 使用路径映射后
import { Product } from '@/models/product';
import { formatCurrency } from '@utils/formatters';
```

### 其他有用选项

```json
{
  "compilerOptions": {
    // 允许导入 .js 文件
    "allowJs": true,
    
    // 检查 JavaScript 文件的类型
    "checkJs": true,
    
    // 生成 source map（便于调试）
    "sourceMap": true,
    
    // 删除注释
    "removeComments": true,
    
    // 不允许未使用的局部变量
    "noUnusedLocals": true,
    
    // 不允许未使用的参数
    "noUnusedParameters": true,
    
    // 不允许隐式的返回类型
    "noImplicitReturns": true,
    
    // 不允许 fallthrough 的 case 语句
    "noFallthroughCasesInSwitch": true
  }
}
```

## 与 JavaScript 的互操作

在现实项目中，你经常需要与现有的 JavaScript 代码一起工作。TypeScript 提供了多种方式来处理这种情况。

### 类型声明文件（.d.ts）

当使用没有 TypeScript 类型的 JavaScript 库时，你可以创建类型声明文件：

```typescript
// 📁 types/ghost-library.d.ts
declare module 'ghost-library' {
  export interface Ghost {
    name: string;
    haunt(): void;
  }
  
  export function createGhost(name: string): Ghost;
  export const VERSION: string;
}

// 📁 src/main.ts
import { createGhost } from 'ghost-library';
const ghost = createGhost("卡斯珀");
```

### 为现有 JavaScript 添加类型

如果你有自己的 JavaScript 代码库，可以逐步添加类型：

```javascript
// 📁 legacy.js - 现有的 JavaScript 文件
export function calculateTotal(price, quantity) {
  return price * quantity;
}

// 📁 legacy.d.ts - 对应的类型声明
export function calculateTotal(price: number, quantity: number): number;

// 📁 src/main.ts - TypeScript 中使用
import { calculateTotal } from '../legacy';
const total = calculateTotal(100, 3); // 现在有类型检查了
```

### 使用 JSDoc 注释

你可以在 JavaScript 文件中使用 JSDoc 注释来提供类型信息：

```javascript
// 📁 legacy.js - 带有 JSDoc 的 JavaScript
/**
 * 计算商品总价
 * @param {number} price 单价
 * @param {number} quantity 数量
 * @returns {number} 总价
 */
export function calculateTotal(price, quantity) {
  return price * quantity;
}

// TypeScript 可以识别这些类型注释
```

## 使用 ESLint 和 Prettier 保持代码整洁

TypeScript 负责类型检查，ESLint 负责代码质量，Prettier 负责代码格式化。三者结合可以确保代码的一致性和高质量。

### 安装依赖

```bash
# 安装 ESLint 和相关插件
npm install --save-dev eslint @typescript-eslint/parser @typescript-eslint/eslint-plugin

# 安装 Prettier
npm install --save-dev prettier eslint-config-prettier eslint-plugin-prettier
```

### ESLint 配置

```javascript
// 📁 .eslintrc.js
module.exports = {
  parser: '@typescript-eslint/parser',
  parserOptions: {
    ecmaVersion: 2020,
    sourceType: 'module',
  },
  plugins: ['@typescript-eslint'],
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'prettier',
  ],
  rules: {
    // 自定义规则
    '@typescript-eslint/explicit-function-return-type': 'off',
    '@typescript-eslint/no-explicit-any': 'warn',
    '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
  },
  env: {
    node: true,
    es6: true,
  },
};
```

### Prettier 配置

```json
// 📁 .prettierrc
{
  "semi": true,
  "trailingComma": "es5",
  "singleQuote": true,
  "printWidth": 80,
  "tabWidth": 2,
  "endOfLine": "lf"
}
```

### 在 package.json 中添加脚本

```json
{
  "scripts": {
    "lint": "eslint src --ext .ts",
    "lint:fix": "eslint src --ext .ts --fix",
    "format": "prettier --write \"src/**/*.ts\"",
    "type-check": "tsc --noEmit",
    "build": "tsc",
    "dev": "tsc --watch"
  }
}
```

### 编辑器集成

大多数现代编辑器（VSCode、WebStorm 等）都支持 ESLint 和 Prettier 的自动集成。安装相应的扩展后，代码会在保存时自动格式化和检查。

## 练习：配置一个全新的 TypeScript 项目

现在，让我们从零开始配置一个完整的 TypeScript 项目。

### 步骤 1：初始化项目

```bash
# 创建项目目录
mkdir ghost-shop
cd ghost-shop

# 初始化 package.json
npm init -y

# 安装 TypeScript
npm install --save-dev typescript

# 安装开发工具
npm install --save-dev eslint @typescript-eslint/parser @typescript-eslint/eslint-plugin prettier eslint-config-prettier eslint-plugin-prettier

# 安装运行时依赖（示例）
npm install express
npm install --save-dev @types/express
```

### 步骤 2：创建目录结构

```
ghost-shop/
├── src/
│   ├── models/
│   ├── services/
│   ├── utils/
│   └── index.ts
├── tests/
├── dist/
└── types/
```

### 步骤 3：创建 TypeScript 配置

```json
// 📁 tsconfig.json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "CommonJS",
    "lib": ["ES2020"],
    "outDir": "./dist",
    "rootDir": "./src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "declaration": true,
    "declarationDir": "./types",
    "sourceMap": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"],
      "@models/*": ["src/models/*"],
      "@utils/*": ["src/utils/*"]
    }
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist", "tests"]
}
```

### 步骤 4：创建 ESLint 配置

```javascript
// 📁 .eslintrc.js
module.exports = {
  parser: '@typescript-eslint/parser',
  parserOptions: {
    ecmaVersion: 2020,
    sourceType: 'module',
    project: './tsconfig.json',
  },
  plugins: ['@typescript-eslint'],
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:@typescript-eslint/recommended-requiring-type-checking',
    'prettier',
  ],
  rules: {
    '@typescript-eslint/explicit-module-boundary-types': 'off',
    '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
    '@typescript-eslint/no-explicit-any': 'warn',
  },
  ignorePatterns: ['dist/', 'node_modules/'],
};
```

### 步骤 5：创建 Prettier 配置

```json
// 📁 .prettierrc
{
  "semi": true,
  "trailingComma": "all",
  "singleQuote": true,
  "printWidth": 80,
  "tabWidth": 2
}
```

### 步骤 6：创建示例代码

```typescript
// 📁 src/models/Product.ts
export default class Product {
  constructor(
    public id: number,
    public name: string,
    public price: number
  ) {}
  
  getPriceWithTax(taxRate: number): number {
    return this.price * (1 + taxRate / 100);
  }
}

// 📁 src/index.ts
import Product from '@/models/Product';

const product = new Product(1, "幽灵娃娃", 299);
console.log(`商品：${product.name}`);
console.log(`含税价格：${product.getPriceWithTax(10)}`);
```

### 步骤 7：更新 package.json 脚本

```json
{
  "scripts": {
    "build": "tsc",
    "dev": "tsc --watch",
    "lint": "eslint src --ext .ts",
    "lint:fix": "eslint src --ext .ts --fix",
    "format": "prettier --write \"src/**/*.ts\"",
    "type-check": "tsc --noEmit",
    "test": "echo \"No tests yet\"",
    "start": "node dist/index.js"
  }
}
```

### 步骤 8：测试配置

```bash
# 检查类型
npm run type-check

# 格式化代码
npm run format

# 检查代码质量
npm run lint

# 构建项目
npm run build

# 运行项目
npm start
```

## AI 辅助提示

当与 AI 合作配置 TypeScript 项目时，你可以这样描述需求：

> “我需要配置一个 TypeScript 项目，使用 ESLint 和 Prettier。目标环境是 Node.js，使用 CommonJS 模块系统。需要路径映射：@/ 指向 src/。请生成完整的配置文件：tsconfig.json、.eslintrc.js、.prettierrc 和 package.json 脚本。”

清晰的描述能让 AI 生成符合现代标准的配置。

## 本章小结

正确的编译器配置和工具链是 TypeScript 项目成功的基础。通过本章学习，你现在能够：

1. **理解 tsconfig.json** 的关键配置项
2. **与 JavaScript 代码互操作**，逐步迁移项目
3. **配置 ESLint 和 Prettier**，保持代码质量
4. **从零搭建完整的 TypeScript 项目**

记住魔瓶的核心驱动力：“穿梭在数据中的幽灵，能够抵达任何边缘地带。”正确的工具链配置就是确保你能够顺畅穿梭的基础设施。

在下一章中，我们将探索 AI 辅助开发实战，学习如何与 AI 编程助手有效合作，这是 AI 时代最高效的开发方式。

> 下一章：[第七章：灵魂附体——AI 辅助开发实战](../content/07-ai-assistance.md)