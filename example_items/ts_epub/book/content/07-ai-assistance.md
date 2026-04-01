# 第七章：灵魂附体——AI 辅助开发实战

> 在幽灵世界中，附身是一种特殊的能力，让一个存在可以借用另一个存在的知识和技能。AI 编程助手就是这样的存在——它们可以“附身”于你，提供代码建议、错误修复和最佳实践。学会与 AI 合作，就像学会与幽灵共舞。

## AI 编程助手简介

在 AI 时代，编程不再是孤军奋战。你有了一群无形的助手，随时准备帮助你。让我们认识一下最常见的几位：

### GitHub Copilot

GitHub Copilot 是集成在编辑器中的 AI 助手，能够根据你的代码上下文提供建议。它就像是一个坐在你肩膀上的幽灵编码伙伴。

**特点：**
- 实时代码补全
- 根据注释生成代码
- 支持多种编程语言
- 集成在 VSCode、JetBrains IDE 等编辑器中

### ChatGPT / Claude / DeepSeek

这些是通用 AI 助手，可以对话、回答问题、生成代码。它们就像是可以咨询的幽灵智者。

**特点：**
- 自然语言对话
- 代码生成和解释
- 错误调试帮助
- 架构设计建议

### Cursor

Cursor 是一个基于 AI 的现代化编辑器，专门为 AI 辅助编程设计。

**特点：**
- 内置 AI 对话功能
- 代码自动补全和重构
- 错误检测和修复建议
- 项目级别的理解

### 其他工具

- **Sourcegraph Cody**：企业级的 AI 编程助手
- **Tabnine**：专注于代码补全的 AI 助手
- **Codeium**：免费的 AI 代码补全工具

## 如何向 AI 描述你的需求？

与 AI 合作的关键是清晰的沟通。就像向一个幽灵描述你想要什么，你需要具体、明确。

### 不好的描述 vs 好的描述

```typescript
// ❌ 不好的描述：太模糊
"写一个函数"

// ✅ 好的描述：具体明确
"写一个 TypeScript 函数，接受一个数字数组，返回数组中所有偶数的和"

// ❌ 不好的描述：缺少上下文
"修复这个错误"

// ✅ 好的描述：提供完整信息
"我有一个 TypeScript 函数，它应该过滤出数组中的正数，但返回类型有问题。请帮我修复类型错误。"
```

### 提供足够的上下文

AI 不是通灵者。你需要提供足够的上下文：

```typescript
// 📝 给 AI 的提示：
"""
我有一个 TypeScript 项目，正在构建一个电商系统。

当前文件：src/models/Product.ts
内容：
export default class Product {
  constructor(
    public id: number,
    public name: string,
    public price: number
  ) {}
}

需求：
我需要添加一个方法，计算商品的含税价格。
税率应该作为参数传入，默认值为 10%。
方法应该返回 number 类型。
请实现这个方法。
"""

// 🤖 AI 的回应：
export default class Product {
  constructor(
    public id: number,
    public name: string,
    public price: number
  ) {}
  
  getPriceWithTax(taxRate: number = 10): number {
    return this.price * (1 + taxRate / 100);
  }
}
```

### 指定技术栈和约束

```typescript
// 📝 明确的约束：
"""
使用 TypeScript，面向 Node.js 环境。
不要使用任何外部库。
遵循 Airbnb 的代码风格。
添加适当的类型注解和 JSDoc 注释。
"""
```

## 提示工程基础：让 AI 理解你的 TypeScript 项目

提示工程是与 AI 有效合作的艺术。以下是一些针对 TypeScript 开发的提示技巧：

### 1. 分步骤提示

复杂的任务应该分解成步骤：

```typescript
// 📝 分步骤提示：
"""
请帮我完成以下任务：

步骤 1：创建一个 Product 接口，包含 id、name、price 属性。
步骤 2：创建一个 ShoppingCart 类，可以添加、移除商品，计算总价。
步骤 3：创建一个函数，将购物车内容格式化为字符串。
"""
```

### 2. 提供示例

给 AI 提供示例，让它理解你想要什么：

```typescript
// 📝 提供示例的提示：
"""
我想要一个 TypeScript 工具函数，类似这样：

示例输入：{ name: "卡斯珀", age: 150 }
示例输出："{'name': '卡斯珀', 'age': 150}"

请创建一个函数，将对象转换为这种格式的字符串。
"""
```

### 3. 指定错误处理

明确告诉 AI 如何处理边界情况：

```typescript
// 📝 指定错误处理的提示：
"""
创建一个 TypeScript 函数，解析 JSON 字符串。
如果解析失败，应该返回一个特定的错误对象，包含错误信息。
如果输入不是字符串，应该抛出 TypeError。
请包含完整的类型定义。
"""
```

### 4. 要求测试用例

让 AI 为生成的代码创建测试：

```typescript
// 📝 要求测试的提示：
"""
创建一个 TypeScript 函数，计算两个日期的天数差。
同时创建 Jest 测试用例，覆盖以下场景：
1. 正常日期计算
2. 开始日期晚于结束日期
3. 无效日期输入
"""
```

## 代码审查与优化：AI 作为你的第二双眼睛

AI 不仅可以生成代码，还可以审查和优化现有代码。

### 代码审查提示

```typescript
// 📝 代码审查提示：
"""
请审查以下 TypeScript 代码，指出潜在问题并提供改进建议：

代码：
function processData(data: any) {
  if (data && data.length > 0) {
    return data.map(item => item.value).filter(v => v !== null);
  }
  return [];
}

关注点：
1. 类型安全问题
2. 代码可读性
3. 性能优化
4. 错误处理
"""
```

### 代码优化提示

```typescript
// 📝 代码优化提示：
"""
以下 TypeScript 函数可以如何优化？请提供重构版本：

原函数：
function findGhost(ghosts: any[], name: string) {
  for (let i = 0; i < ghosts.length; i++) {
    if (ghosts[i].name === name) {
      return ghosts[i];
    }
  }
  return null;
}

优化目标：
1. 添加正确的类型定义
2. 使用现代 JavaScript 特性
3. 提高可读性
"""
```

### 类型推导帮助

当你不确定如何定义类型时，可以让 AI 帮忙：

```typescript
// 📝 类型推导提示：
"""
我有一个复杂的嵌套数据结构，需要创建 TypeScript 类型定义。
数据结构示例：
{
  id: 1,
  name: "幽灵商店",
  products: [
    {
      id: 101,
      name: "幽灵娃娃",
      price: 299,
      tags: ["toy", "ghost"]
    }
  ],
  settings: {
    theme: "dark",
    currency: "CNY"
  }
}

请创建完整的接口定义。
"""
```

## 练习：与 AI 合作完成一个小功能

现在，让我们实际与 AI 合作完成一个功能。我们将使用一个假设的 AI 助手来演示这个过程。

### 任务：创建购物车折扣系统

**需求描述：**
我们需要为一个电商系统添加折扣功能。购物车应该支持多种折扣类型：
1. 百分比折扣（如 10% off）
2. 固定金额折扣（如减 50 元）
3. 买一赠一

### 步骤 1：设计类型定义

```typescript
// 📝 给 AI 的提示：
"""
我需要为电商折扣系统创建 TypeScript 类型定义。

要求：
1. 定义一个 Discount 联合类型，支持三种折扣：
   - 百分比折扣：{ type: 'percentage'; value: number } // value 是百分比，如 10 表示 10%
   - 固定金额折扣：{ type: 'fixed'; value: number } // value 是固定金额，如 50 表示减 50 元
   - 买一赠一：{ type: 'buyOneGetOneFree'; productId: number }

2. 定义一个 Product 接口，包含 id、name、price。

3. 定义一个 CartItem 接口，包含 product 和 quantity。

请创建完整的类型定义。
"""

// 🤖 AI 的回应：
interface Product {
  id: number;
  name: string;
  price: number;
}

interface CartItem {
  product: Product;
  quantity: number;
}

type PercentageDiscount = {
  type: 'percentage';
  value: number; // 百分比，如 10 表示 10%
};

type FixedDiscount = {
  type: 'fixed';
  value: number; // 固定金额，如 50 表示减 50 元
};

type BuyOneGetOneFreeDiscount = {
  type: 'buyOneGetOneFree';
  productId: number;
};

type Discount = PercentageDiscount | FixedDiscount | BuyOneGetOneFreeDiscount;
```

### 步骤 2：实现折扣计算函数

```typescript
// 📝 给 AI 的提示：
"""
基于上面的类型定义，请实现一个函数 calculateDiscount。

函数签名：
function calculateDiscount(
  cartItems: CartItem[],
  discount: Discount
): number

功能：
根据折扣类型计算折扣金额。

规则：
1. 百分比折扣：应用在所有商品总价上
2. 固定金额折扣：直接减去固定金额（但不能使总价低于 0）
3. 买一赠一：对于指定 productId 的商品，每两个中一个免费

请实现这个函数，包含详细的注释。
"""

// 🤖 AI 的回应（简化版）：
/**
 * 计算购物车的折扣金额
 * @param cartItems 购物车商品
 * @param discount 折扣信息
 * @returns 折扣金额
 */
function calculateDiscount(
  cartItems: CartItem[],
  discount: Discount
): number {
  // 计算原始总价
  const totalPrice = cartItems.reduce(
    (sum, item) => sum + (item.product.price * item.quantity),
    0
  );
  
  switch (discount.type) {
    case 'percentage': {
      // 百分比折扣
      return totalPrice * (discount.value / 100);
    }
    
    case 'fixed': {
      // 固定金额折扣，但不能超过总价
      return Math.min(discount.value, totalPrice);
    }
    
    case 'buyOneGetOneFree': {
      // 买一赠一
      const targetItem = cartItems.find(
        item => item.product.id === discount.productId
      );
      
      if (!targetItem) {
        return 0; // 没有目标商品，无折扣
      }
      
      // 计算免费商品数量（每两个中一个免费）
      const freeItems = Math.floor(targetItem.quantity / 2);
      return freeItems * targetItem.product.price;
    }
    
    default: {
      // 类型保护：确保处理了所有情况
      const exhaustiveCheck: never = discount;
      throw new Error(`未知的折扣类型: ${exhaustiveCheck}`);
    }
  }
}
```

### 步骤 3：添加错误处理和边界情况

```typescript
// 📝 给 AI 的提示：
"""
请为上面的 calculateDiscount 函数添加错误处理和边界情况检查：

1. 验证输入参数：
   - cartItems 必须是数组
   - 每个 cartItem 必须有有效的 product 和 quantity
   - discount 必须是有效的 Discount 类型

2. 处理边界情况：
   - 百分比折扣的 value 应该在 0-100 之间
   - 固定金额折扣的 value 应该是正数
   - 数量应该是正整数

3. 添加适当的错误消息。

请提供更新后的函数。
"""

// 🤖 AI 的回应（部分）：
function calculateDiscount(
  cartItems: CartItem[],
  discount: Discount
): number {
  // 输入验证
  if (!Array.isArray(cartItems)) {
    throw new TypeError('cartItems 必须是数组');
  }
  
  // 验证每个 cartItem
  cartItems.forEach((item, index) => {
    if (!item.product || typeof item.product.price !== 'number') {
      throw new Error(`第 ${index + 1} 个商品缺少有效的 product 信息`);
    }
    if (!Number.isInteger(item.quantity) || item.quantity < 1) {
      throw new Error(`第 ${index + 1} 个商品的数量必须是正整数`);
    }
  });
  
  // 验证折扣
  switch (discount.type) {
    case 'percentage':
      if (discount.value < 0 || discount.value > 100) {
        throw new Error('百分比折扣的值必须在 0-100 之间');
      }
      break;
    case 'fixed':
      if (discount.value < 0) {
        throw new Error('固定金额折扣的值不能为负数');
      }
      break;
    case 'buyOneGetOneFree':
      if (!Number.isInteger(discount.productId) || discount.productId < 1) {
        throw new Error('productId 必须是正整数');
      }
      break;
  }
  
  // ... 原有的计算逻辑
}
```

### 步骤 4：创建测试用例

```typescript
// 📝 给 AI 的提示：
"""
请为 calculateDiscount 函数创建 Jest 测试用例。
覆盖以下场景：
1. 百分比折扣的正常情况
2. 固定金额折扣的正常情况
3. 买一赠一的正常情况
4. 各种错误输入
5. 边界情况（如 100% 折扣、折扣超过总价等）

请提供完整的测试文件。
"""

// 🤖 AI 的回应（部分）：
describe('calculateDiscount', () => {
  const mockProducts = {
    doll: { id: 1, name: '幽灵娃娃', price: 299 },
    book: { id: 2, name: '鬼屋指南', price: 199 },
  };
  
  test('百分比折扣 - 正常情况', () => {
    const cartItems = [
      { product: mockProducts.doll, quantity: 2 },
    ];
    const discount = { type: 'percentage' as const, value: 10 };
    
    const result = calculateDiscount(cartItems, discount);
    const expected = 299 * 2 * 0.1; // 总价 598 的 10%
    
    expect(result).toBeCloseTo(expected);
  });
  
  test('固定金额折扣 - 折扣不超过总价', () => {
    const cartItems = [
      { product: mockProducts.book, quantity: 1 },
    ];
    const discount = { type: 'fixed' as const, value: 50 };
    
    const result = calculateDiscount(cartItems, discount);
    expect(result).toBe(50); // 50 元折扣
  });
  
  // ... 更多测试
});
```

## AI 协作的最佳实践

### 1. 逐步迭代
不要期望 AI 一次生成完美的代码。先让 AI 生成基础版本，然后逐步完善。

### 2. 保持控制权
AI 是助手，不是主人。你始终应该理解 AI 生成的代码，并对其进行审查。

### 3. 提供反馈
如果 AI 生成的代码不符合要求，提供具体的反馈，告诉它需要如何修改。

### 4. 结合人类智慧
AI 擅长生成代码，但人类擅长理解业务逻辑和用户体验。将两者结合。

### 5. 安全第一
不要将敏感信息（API 密钥、密码等）提供给 AI。AI 可能会在训练数据中使用这些信息。

## 本章小结

AI 辅助开发是 TypeScript 学习的加速器。通过本章学习，你现在能够：

1. **选择合适的 AI 工具**：根据需求选择 GitHub Copilot、ChatGPT 或 Cursor
2. **编写有效的提示**：清晰、具体地描述需求，提供足够的上下文
3. **与 AI 协作开发**：分步骤完成复杂功能，审查和优化 AI 生成的代码
4. **创建测试和文档**：让 AI 帮助生成测试用例和代码文档

记住魔瓶的世界观：“没有无法塑造的规则，只有无法表达的现状。”与 AI 合作的关键就是清晰地表达你的需求。只要你能清晰地描述，AI 就能帮助你实现。

在下一章中，我们将综合运用所有知识，完成一个“鬼屋项目”——从零到一的完整 TypeScript 应用。

> 下一章：[第八章：鬼屋项目——从零到一的完整应用](../content/08-project.md)