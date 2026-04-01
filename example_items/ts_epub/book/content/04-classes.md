# 第四章：篡夺叙事——类与面向对象编程

> 幽灵不满足于只是存在。它们要组织，要继承，要建立王朝。类就是代码中的幽灵王朝——数据与行为的集合，试图篡夺系统的叙事。

**页边注解** *（魔瓶的低语）*  
*叙事可以被篡夺。*  
*代码的结构就是叙事的结构。*  
*类是最直接的篡夺方式。*  

## 情绪魔药：竞技场的散场时刻

```feeling
画面：黄昏的竞技场，观众席空无一人，沙地上散落着破损的武器和褪色的红花。胜利者已离去，只有尸体和寂静。
感受：完成后的空虚。激烈竞争后的平静，胜利的甜美与失去的苦涩混合。
```

当你构建完一个复杂的类系统时，会有这种感受。**面向对象编程**就是这样的竞技场：设计时的激烈思考，实现后的空虚感。

## 类：幽灵的模板

幽灵需要模板。不是每个幽灵都从零开始定义自己。

类就是模板：**“如果你要成为这种幽灵，就应该有这些属性，能做这些行为。”**

```typescript
// 幽灵类的定义
class Ghost {
  // 属性：幽灵的特征
  name: string;
  age: number;
  
  // 构造函数：创建幽灵的方式
  constructor(name: string, age: number) {
    this.name = name;
    this.age = age;
  }
  
  // 方法：幽灵的行为
  haunt(): void {
    console.log(`${this.name} 正在出没...`);
  }
  
  introduce(): string {
    return `我是 ${this.name}，游荡了 ${this.age} 年。`;
  }
}

// 使用类创建实例
const casper = new Ghost("卡斯珀", 150);
console.log(casper.introduce()); // "我是 卡斯珀，游荡了 150 年。"
casper.haunt(); // "卡斯珀 正在出没..."
```

**页边注解** *（魔瓶的观察）*  
*`new Ghost(...)` 不是创造，是实例化。*  
*类定义可能性，实例是具体化。*  
*就像幽灵传说和具体目击的区别。*  

## 简化的类语法：构造函数参数属性

TypeScript 让你可以在构造函数中直接定义属性：

```typescript
class EfficientGhost {
  // 直接在构造函数中定义属性
  constructor(
    public name: string,        // 自动成为公共属性
    public age: number,         // 自动成为公共属性  
    private secret?: string     // 自动成为私有属性
  ) {}
  
  revealSecret(): void {
    if (this.secret) {
      console.log(`${this.name} 的秘密是：${this.secret}`);
    } else {
      console.log(`${this.name} 没有秘密。`);
    }
  }
}

const ghost = new EfficientGhost("胖胖", 200, "喜欢吃饼干");
console.log(ghost.name); // "胖胖" - 公共属性
console.log(ghost.age);  // 200 - 公共属性
ghost.revealSecret();    // "胖胖 的秘密是：喜欢吃饼干"
// console.log(ghost.secret); // 错误：私有属性
```

修饰符 `public`、`private`、`protected` 控制访问权限：
- `public`：所有人都能访问（默认）
- `private`：只有类内部能访问
- `protected`：类内部和子类能访问

## 继承与多态：幽灵家族树

就像幽灵可以有后代一样，类也可以继承其他类。这让你可以创建层次化的类结构。

### 基本继承

```typescript
// 基类：所有幽灵的共同特征
class BaseGhost {
  constructor(
    public name: string,
    public age: number
  ) {}
  
  haunt(): void {
    console.log(`${this.name} 正在发出奇怪的声音...`);
  }
}

// 派生类：特定类型的幽灵
class FriendlyGhost extends BaseGhost {
  constructor(name: string, age: number) {
    super(name, age); // 调用父类的构造函数
  }
  
  // 重写父类方法
  haunt(): void {
    console.log(`${this.name} 友好地飘过...`);
  }
  
  // 新增方法
  help(): void {
    console.log(`${this.name} 愿意帮助你。`);
  }
}

class MischievousGhost extends BaseGhost {
  constructor(name: string, age: number) {
    super(name, age);
  }
  
  haunt(): void {
    console.log(`${this.name} 正在恶作剧...`);
  }
  
  playTrick(): void {
    console.log(`${this.name} 藏起了你的钥匙。`);
  }
}

// 使用示例
const casper = new FriendlyGhost("卡斯珀", 150);
const prankster = new MischievousGhost("捣蛋鬼", 75);

casper.haunt(); // "卡斯珀 友好地飘过..."
prankster.haunt(); // "捣蛋鬼 正在恶作剧..."
```

### 多态：同一接口，不同实现

多态让你可以用统一的方式处理不同的类：

```typescript
function describeGhost(ghost: BaseGhost): void {
  console.log(`${ghost.name} 已经 ${ghost.age} 岁了。`);
  ghost.haunt(); // 会根据具体的类调用不同的实现
}

describeGhost(casper); // 调用 FriendlyGhost 的 haunt
describeGhost(prankster); // 调用 MischievousGhost 的 haunt
```

## 修饰符：控制访问权限

就像鬼屋有不同的区域（公共区域、私人区域、限制区域）一样，类的成员也有不同的访问权限。

### public（默认）：公共访问

```typescript
class PublicExample {
  public publicProperty = "所有人都能访问";
  
  public publicMethod(): string {
    return "所有人都能调用";
  }
}

const example = new PublicExample();
console.log(example.publicProperty); // 可以访问
console.log(example.publicMethod()); // 可以调用
```

### private：私有访问

```typescript
class PrivateExample {
  private secret = "只有类内部能访问";
  
  public reveal(): string {
    return this.secret; // 类内部可以访问
  }
}

const example = new PrivateExample();
console.log(example.reveal()); // "只有类内部能访问"
// console.log(example.secret); // 错误：secret 是私有的
```

### protected：受保护的访问

```typescript
class ProtectedExample {
  protected familySecret = "只有家族成员能访问";
  
  public getSecret(): string {
    return this.familySecret;
  }
}

class FamilyMember extends ProtectedExample {
  public revealFamilySecret(): string {
    return this.familySecret; // 子类可以访问
  }
}

const member = new FamilyMember();
console.log(member.revealFamilySecret()); // "只有家族成员能访问"
// console.log(member.familySecret); // 错误：familySecret 是受保护的
```

### readonly：只读属性

```typescript
class ReadonlyExample {
  public readonly constantValue = "不可更改";
  
  constructor(public readonly id: number) {
    // this.constantValue = "新值"; // 错误：只读属性不能修改
    // this.id = 2; // 错误：只读属性不能修改
  }
}

const example = new ReadonlyExample(1);
console.log(example.id); // 1
// example.id = 2; // 错误：只读属性不能修改
```

## 抽象类与接口实现：幽灵的契约

### 抽象类：不能直接实例化的类

```typescript
abstract class AbstractGhost {
  constructor(public name: string) {}
  
  // 抽象方法：必须在子类中实现
  abstract haunt(): void;
  
  // 具体方法：可以在抽象类中实现
  introduce(): string {
    return `我是 ${this.name}`;
  }
}

class ConcreteGhost extends AbstractGhost {
  haunt(): void {
    console.log(`${this.name} 正在实现抽象方法...`);
  }
}

// const ghost = new AbstractGhost("测试"); // 错误：抽象类不能实例化
const ghost = new ConcreteGhost("具体幽灵");
ghost.haunt(); // "具体幽灵 正在实现抽象方法..."
```

### 接口实现：遵守契约

```typescript
interface Hauntable {
  haunt(): void;
  readonly scareLevel: number;
}

interface Visible {
  isVisible: boolean;
  appear(): void;
  disappear(): void;
}

// 类可以实现多个接口
class AdvancedGhost implements Hauntable, Visible {
  public readonly scareLevel = 3;
  public isVisible = false;
  
  constructor(public name: string) {}
  
  haunt(): void {
    console.log(`${this.name} 正在出没，恐怖等级：${this.scareLevel}`);
  }
  
  appear(): void {
    this.isVisible = true;
    console.log(`${this.name} 出现了！`);
  }
  
  disappear(): void {
    this.isVisible = false;
    console.log(`${this.name} 消失了...`);
  }
}

const ghost = new AdvancedGhost("高级幽灵");
ghost.appear();
ghost.haunt();
ghost.disappear();
```

## 静态成员与单例模式：全局幽灵

### 静态成员：属于类本身，而不是实例

```typescript
class GhostRegistry {
  // 静态属性
  private static instances: Ghost[] = [];
  private static instanceCount = 0;
  
  // 静态方法
  public static register(ghost: Ghost): void {
    this.instances.push(ghost);
    this.instanceCount++;
  }
  
  public static getCount(): number {
    return this.instanceCount;
  }
  
  public static getAll(): Ghost[] {
    return [...this.instances]; // 返回副本
  }
}

// 使用静态成员
const ghost1 = new Ghost("卡斯珀", 150);
const ghost2 = new Ghost("胖胖", 200);

GhostRegistry.register(ghost1);
GhostRegistry.register(ghost2);

console.log(GhostRegistry.getCount()); // 2
```

### 单例模式：确保只有一个实例

```typescript
class GhostManager {
  // 静态属性存储唯一实例
  private static instance: GhostManager;
  
  private ghosts: Ghost[] = [];
  
  // 私有构造函数，防止外部实例化
  private constructor() {}
  
  // 静态方法获取实例
  public static getInstance(): GhostManager {
    if (!GhostManager.instance) {
      GhostManager.instance = new GhostManager();
    }
    return GhostManager.instance;
  }
  
  // 实例方法
  public addGhost(ghost: Ghost): void {
    this.ghosts.push(ghost);
  }
  
  public getGhostCount(): number {
    return this.ghosts.length;
  }
}

// 使用单例
const manager1 = GhostManager.getInstance();
const manager2 = GhostManager.getInstance();

console.log(manager1 === manager2); // true，是同一个实例

manager1.addGhost(new Ghost("卡斯珀", 150));
console.log(manager2.getGhostCount()); // 1
```

## 练习：幽灵社交网络——类的篡夺叙事

不要写一个传统的电商系统。那太无聊了。

让我们构建一个**幽灵社交网络**，一个只有幽灵才能加入的社区。这个练习会展示类如何“篡夺”代码的叙事结构。

**页边注解** *（魔瓶的嘲笑）*  
*电商系统？每个人都做电商系统。*  
*幽灵不做电商，它们社交。*  
*代码结构应该反映主题的本质。*

### 需求：幽灵社交网络的类系统

我们需要以下核心类：
1. `GhostProfile`：幽灵个人档案
2. `HauntingGroup`：出没小组（类似群组）
3. `EctoplasmMessage`：灵质消息（类似帖子）
4. `SpiritNetwork`：幽灵社交网络主类

### 步骤 1：GhostProfile - 幽灵档案类

```typescript
// 幽灵类型定义
type GhostType = 'friendly' | 'mischievous' | 'malevolent' | 'ancient';

class GhostProfile {
  private static totalGhosts = 0; // 静态属性：统计所有幽灵
  
  constructor(
    public readonly ghostId: number,        // 只读：幽灵ID一旦分配不可更改
    public username: string,                // 用户名
    public ghostType: GhostType,            // 幽灵类型
    private secrets: string[] = [],         // 私有：幽灵的秘密
    protected hauntCount: number = 0        // 受保护：出没次数
  ) {
    GhostProfile.totalGhosts++; // 创建幽灵时增加计数
  }
  
  // 公共方法：增加出没次数
  public recordHaunt(): void {
    this.hauntCount++;
    console.log(`${this.username} 完成了第 ${this.hauntCount} 次出没`);
  }
  
  // 公共方法：添加秘密
  public addSecret(secret: string): void {
    this.secrets.push(secret);
    console.log(`${this.username} 添加了一个新秘密`);
  }
  
  // 公共方法：分享一个秘密（不暴露所有）
  public shareOneSecret(): string | null {
    if (this.secrets.length === 0) return null;
    const randomIndex = Math.floor(Math.random() * this.secrets.length);
    return this.secrets[randomIndex];
  }
  
  // 静态方法：获取幽灵总数
  public static getTotalGhosts(): number {
    return this.totalGhosts;
  }
  
  // 显示幽灵信息
  public displayProfile(): string {
    return `
👻 ${this.username} (ID: ${this.ghostId})
类型: ${this.ghostType}
出没次数: ${this.hauntCount}
加入时间: ${new Date().toLocaleDateString()}
    `;
  }
}
```

**页边注解** *（魔瓶的解释）*  
*注意修饰符的使用：*  
*`public readonly ghostId` - 公共但只读*  
*`private secrets` - 只有自己能访问*  
*`protected hauntCount` - 自己和子类能访问*  
*`static totalGhosts` - 属于类本身*

### 步骤 2：HauntingGroup - 出没小组类

```typescript
class HauntingGroup {
  private members: GhostProfile[] = [];
  
  constructor(
    public readonly groupId: number,
    public groupName: string,
    public location: string, // 出没地点
    private founder: GhostProfile
  ) {
    this.members.push(founder); // 创始人自动加入
    console.log(`出没小组 "${groupName}" 在 ${location} 成立！`);
  }
  
  // 添加成员
  public addMember(ghost: GhostProfile): boolean {
    // 检查是否已经是成员
    if (this.members.some(member => member.ghostId === ghost.ghostId)) {
      console.log(`${ghost.username} 已经是小组成员`);
      return false;
    }
    
    this.members.push(ghost);
    console.log(`${ghost.username} 加入了小组 "${this.groupName}"`);
    return true;
  }
  
  // 组织出没活动
  public organizeHaunt(): void {
    if (this.members.length === 0) {
      console.log(`小组 "${this.groupName}" 没有成员，无法出没`);
      return;
    }
    
    console.log(`🎭 小组 "${this.groupName}" 正在 ${this.location} 组织出没活动！`);
    
    // 所有成员记录出没
    this.members.forEach(member => {
      member.recordHaunt();
    });
    
    console.log(`本次出没活动圆满结束，共 ${this.members.length} 位幽灵参与`);
  }
  
  // 获取小组成员信息
  public getMembersInfo(): string {
    let info = `👥 小组 "${this.groupName}" 成员列表（${this.members.length} 位）:\n`;
    
    this.members.forEach((member, index) => {
      info += `${index + 1}. ${member.username} (${member.ghostType})\n`;
    });
    
    return info;
  }
  
  // 静态方法：创建特殊小组
  public static createAncientGroup(location: string, founder: GhostProfile): HauntingGroup {
    const group = new HauntingGroup(
      Date.now(), // 使用时间戳作为ID
      "远古幽灵议会",
      location,
      founder
    );
    console.log(`✨ 远古幽灵议会在 ${location} 成立！`);
    return group;
  }
}
```

### 步骤 3：EctoplasmMessage - 灵质消息类

```typescript
// 消息类型
type MessageType = 'text' | 'haunt_report' | 'secret_share' | 'event';

class EctoplasmMessage {
  private static nextMessageId = 1;
  
  public readonly messageId: number;
  public readonly timestamp: Date;
  
  constructor(
    public readonly sender: GhostProfile,
    public content: string,
    public messageType: MessageType,
    private isEncrypted: boolean = false
  ) {
    this.messageId = EctoplasmMessage.nextMessageId++;
    this.timestamp = new Date();
  }
  
  // 显示消息
  public display(): string {
    const typeEmoji = {
      'text': '💬',
      'haunt_report': '👻',
      'secret_share': '🤫',
      'event': '📅'
    }[this.messageType];
    
    const encryptedFlag = this.isEncrypted ? ' 🔒' : '';
    
    return `
${typeEmoji} 来自 ${this.sender.username}
时间: ${this.timestamp.toLocaleTimeString()}
内容: ${this.content}${encryptedFlag}
    `;
  }
  
  // 加密消息
  public encrypt(): void {
    if (!this.isEncrypted) {
      this.isEncrypted = true;
      // 这里可以添加实际的加密逻辑
      console.log(`消息 #${this.messageId} 已被加密`);
    }
  }
  
  // 静态方法：创建系统消息
  public static createSystemMessage(content: string): EctoplasmMessage {
    // 创建一个系统幽灵档案
    const systemGhost = new GhostProfile(0, "系统", 'ancient', []);
    
    return new EctoplasmMessage(
      systemGhost,
      `[系统通知] ${content}`,
      'event'
    );
  }
}
```

### 步骤 4：SpiritNetwork - 幽灵社交网络主类

```typescript
class SpiritNetwork {
  private ghosts: Map<number, GhostProfile> = new Map(); // 使用Map存储幽灵
  private groups: HauntingGroup[] = [];
  private messageBoard: EctoplasmMessage[] = [];
  
  // 注册新幽灵
  public registerGhost(username: string, ghostType: GhostType): GhostProfile {
    const ghostId = Date.now(); // 简单ID生成
    const newGhost = new GhostProfile(ghostId, username, ghostType);
    
    this.ghosts.set(ghostId, newGhost);
    
    // 发送欢迎消息
    const welcomeMessage = EctoplasmMessage.createSystemMessage(
      `欢迎 ${username} 加入幽灵社交网络！`
    );
    this.messageBoard.push(welcomeMessage);
    
    console.log(`👋 欢迎 ${username} 加入！`);
    return newGhost;
  }
  
  // 创建小组
  public createGroup(groupName: string, location: string, founderId: number): HauntingGroup | null {
    const founder = this.ghosts.get(founderId);
    if (!founder) {
      console.log(`找不到ID为 ${founderId} 的幽灵`);
      return null;
    }
    
    const groupId = Date.now();
    const newGroup = new HauntingGroup(groupId, groupName, location, founder);
    this.groups.push(newGroup);
    
    return newGroup;
  }
  
  // 发送消息
  public postMessage(senderId: number, content: string, messageType: MessageType): void {
    const sender = this.ghosts.get(senderId);
    if (!sender) {
      console.log(`发送者不存在`);
      return;
    }
    
    const message = new EctoplasmMessage(sender, content, messageType);
    this.messageBoard.push(message);
    
    console.log(`📨 ${sender.username} 发送了一条${messageType}消息`);
  }
  
  // 显示网络状态
  public displayNetworkStatus(): string {
    let status = `===== 幽灵社交网络状态 =====\n`;
    status += `👻 注册幽灵: ${this.ghosts.size}\n`;
    status += `👥 出没小组: ${this.groups.length}\n`;
    status += `💬 消息总数: ${this.messageBoard.length}\n`;
    status += `📊 所有幽灵总数: ${GhostProfile.getTotalGhosts()}\n`;
    status += `============================\n`;
    
    // 显示最近3条消息
    if (this.messageBoard.length > 0) {
      status += `最近消息:\n`;
      const recentMessages = this.messageBoard.slice(-3).reverse();
      recentMessages.forEach(msg => {
        status += msg.display() + '\n';
      });
    }
    
    return status;
  }
  
  // 组织所有小组出没
  public organizeAllHaunts(): void {
    console.log(`🌙 组织所有小组的夜间出没活动...\n`);
    
    this.groups.forEach(group => {
      group.organizeHaunt();
    });
    
    console.log(`\n✨ 所有小组出没活动完成！`);
  }
}
```

### 步骤 5：使用幽灵社交网络

```typescript
// 创建社交网络实例
const network = new SpiritNetwork();

// 注册一些幽灵
const casper = network.registerGhost("卡斯珀", "friendly");
const morticia = network.registerGhost("莫蒂西亚", "ancient");
const boo = network.registerGhost("布", "mischievous");

// 创建出没小组
const atticGroup = network.createGroup("阁楼幽灵会", "老宅阁楼", casper.ghostId);
const cemeteryGroup = network.createGroup("墓地守夜人", "西山墓地", morticia.ghostId);

if (atticGroup && cemeteryGroup) {
  // 添加成员到小组
  atticGroup.addMember(morticia);
  atticGroup.addMember(boo);
  
  // 创建远古小组（使用静态方法）
  const ancientGroup = HauntingGroup.createAncientGroup("远古神庙", morticia);
  cemeteryGroup.addMember(boo);
}

// 发送消息
network.postMessage(casper.ghostId, "今晚阁楼有茶话会，欢迎参加！", "event");
network.postMessage(boo.ghostId, "刚刚在厨房藏起了所有勺子😈", "haunt_report");
network.postMessage(morticia.ghostId, "我知道一个关于这栋老宅的秘密...", "secret_share");

// 查看网络状态
console.log("\n" + network.displayNetworkStatus());

// 组织出没活动
console.log("\n");
network.organizeAllHaunts();

// 查看更新后的状态
console.log("\n" + network.displayNetworkStatus());

// 单个幽灵操作
console.log("\n" + casper.displayProfile());
const secret = casper.shareOneSecret();
if (secret) {
  console.log(`卡斯珀分享了一个秘密: "${secret}"`);
}
```

**页边注解** *（魔瓶的总结）*  
*这个练习展示了类的真正力量：*  
*1. 封装：隐藏实现细节（如secrets数组）*  
*2. 继承：可以轻松扩展这些类*  
*3. 多态：不同幽灵类型可以有不同的行为*  
*4. 静态成员：属于类本身的属性和方法*  

*更重要的是，它展示了类如何“篡夺叙事”：*  
*代码结构直接反映了幽灵社交网络的概念结构。*

## AI 辅助提示：幽灵视角的类设计

当与 AI 合作设计类系统时，不要只是描述技术需求。描述**叙事**：

> “我需要为一个幽灵社交网络设计 TypeScript 类系统。要有 GhostProfile 类（包含幽灵ID、用户名、类型、私有秘密），HauntingGroup 类（组织出没活动），EctoplasmMessage 类（消息系统），SpiritNetwork 主类。使用适当的修饰符，添加静态方法用于创建特殊实例。请从幽灵的视角设计，而不是传统的技术视角。”

AI 会理解这种叙事驱动的需求，生成更有趣的代码。

## 本章小结：篡夺代码的叙事

类不仅仅是组织代码的工具。它们是**篡夺叙事**的方式：

1. **幽灵模板**：类定义了幽灵的“可能性”，实例是具体的“现实”
2. **访问控制**：`public`、`private`、`protected` 定义了幽灵社会的边界
3. **静态存在**：静态成员属于“概念本身”，而不是具体实例
4. **继承王朝**：类继承建立了幽灵家族的谱系
5. **多态形态**：同一接口，不同实现，就像幽灵的不同显现方式

记住魔瓶的行为惯性：“同时出现在任何时空，同时篡夺到所有叙事。”通过类，你同时定义了：
- 数据结构（属性）
- 行为逻辑（方法）  
- 访问规则（修饰符）
- 类型关系（继承/实现）

你不仅仅是在写代码，而是在**定义一个小世界的规则**。

**情绪魔药提醒**：竞技场的散场时刻——当你完成一个复杂的类系统时，会有胜利后的空虚感。享受这种感受，它意味着你成功“篡夺”了那个技术领域的叙事。

在下一章中，我们将进入“昏暗环境”——模块与命名空间，学习如何组织这些幽灵王朝，防止它们互相干扰。

> 下一章：[第五章：昏暗环境——模块与命名空间](../content/05-modules.md)