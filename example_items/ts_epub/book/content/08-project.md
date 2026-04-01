# 第八章：鬼屋项目——从零到一的完整应用

> 在幽灵世界中，理论知识只有通过实践才能真正掌握。现在，让我们进入鬼屋的深处，综合运用所有学到的 TypeScript 知识，构建一个完整的幽灵待办事项管理应用。这不仅是技术的实践，也是魔瓶视角的完整展现。

## 项目概述：幽灵待办事项管理应用

我们将构建一个帮助幽灵们管理日常任务的应用程序。幽灵们也需要记住很多事情：何时出没、吓唬谁、整理鬼屋等等。

### 功能需求

1. **任务管理**
   - 创建、读取、更新、删除任务
   - 标记任务为完成/未完成
   - 按类别过滤任务

2. **幽灵管理**
   - 幽灵可以注册账户
   - 每个幽灵有自己的任务列表
   - 幽灵可以设置偏好（如主题颜色）

3. **数据持久化**
   - 使用本地存储保存数据
   - 支持导入/导出数据

4. **用户界面**
   - 简洁的命令行界面
   - 清晰的反馈和错误提示

### 技术栈
- TypeScript
- Node.js（运行时）
- 无外部依赖（保持简单）

## 项目结构设计

让我们先规划项目结构：

```
ghost-todo/
├── src/
│   ├── models/          # 数据模型
│   │   ├── Task.ts
│   │   ├── Ghost.ts
│   │   └── index.ts
│   ├── services/        # 业务逻辑
│   │   ├── TaskService.ts
│   │   ├── GhostService.ts
│   │   ├── StorageService.ts
│   │   └── index.ts
│   ├── utils/           # 工具函数
│   │   ├── formatters.ts
│   │   ├── validators.ts
│   │   └── index.ts
│   ├── cli/             # 命令行界面
│   │   ├── commands.ts
│   │   ├── prompts.ts
│   │   └── index.ts
│   └── index.ts         # 应用入口
├── tests/               # 测试文件
├── dist/                # 编译输出
├── types/               # 类型声明
├── package.json
├── tsconfig.json
├── .eslintrc.js
└── .prettierrc
```

## 逐步实现

### 阶段 1：数据模型定义

#### Task 模型

```typescript
// 📁 src/models/Task.ts
export type TaskPriority = 'low' | 'medium' | 'high' | 'critical';
export type TaskStatus = 'todo' | 'in-progress' | 'done' | 'cancelled';

export interface Task {
  id: string;
  title: string;
  description?: string;
  priority: TaskPriority;
  status: TaskStatus;
  dueDate?: Date;
  createdAt: Date;
  updatedAt: Date;
  ghostId: string; // 属于哪个幽灵
  tags: string[];
}

// 创建任务的参数（不包含自动生成的字段）
export type CreateTaskInput = Omit<Task, 'id' | 'createdAt' | 'updatedAt'> & {
  id?: string; // 可选，如果未提供则自动生成
};

// 更新任务的参数（所有字段都是可选的）
export type UpdateTaskInput = Partial<Omit<Task, 'id' | 'ghostId' | 'createdAt'>>;
```

#### Ghost 模型

```typescript
// 📁 src/models/Ghost.ts
export type GhostType = 'friendly' | 'mischievous' | 'malevolent';

export interface Ghost {
  id: string;
  name: string;
  type: GhostType;
  age: number;
  joinDate: Date;
  preferences: {
    theme: 'light' | 'dark' | 'haunted';
    notifications: boolean;
  };
}

export type CreateGhostInput = Omit<Ghost, 'id' | 'joinDate'> & {
  id?: string;
};

export type UpdateGhostInput = Partial<Omit<Ghost, 'id' | 'joinDate'>>;
```

#### 模型索引文件

```typescript
// 📁 src/models/index.ts
export * from './Task';
export * from './Ghost';
```

### 阶段 2：工具函数

#### 表单atter

```typescript
// 📁 src/utils/formatters.ts
export function formatDate(date: Date): string {
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function formatTask(task: Task): string {
  const statusEmoji = {
    'todo': '🔘',
    'in-progress': '🔄', 
    'done': '✅',
    'cancelled': '❌',
  }[task.status];
  
  const priorityEmoji = {
    'low': '⚪',
    'medium': '🟡',
    'high': '🟠',
    'critical': '🔴',
  }[task.priority];
  
  return `${statusEmoji} ${priorityEmoji} ${task.title}
    描述: ${task.description || '无'}
    截止: ${task.dueDate ? formatDate(task.dueDate) : '无截止日期'}
    标签: ${task.tags.join(', ') || '无'}
    创建: ${formatDate(task.createdAt)}
    更新: ${formatDate(task.updatedAt)}`;
}

export function formatGhost(ghost: Ghost): string {
  const typeEmoji = {
    'friendly': '😇',
    'mischievous': '😈',
    'malevolent': '👻',
  }[ghost.type];
  
  return `${typeEmoji} ${ghost.name} (${ghost.age}岁)
    类型: ${ghost.type}
    加入: ${formatDate(ghost.joinDate)}
    主题: ${ghost.preferences.theme}
    通知: ${ghost.preferences.notifications ? '开启' : '关闭'}`;
}
```

#### 验证器

```typescript
// 📁 src/utils/validators.ts
export function isValidTaskPriority(priority: string): priority is TaskPriority {
  return ['low', 'medium', 'high', 'critical'].includes(priority);
}

export function isValidTaskStatus(status: string): status is TaskStatus {
  return ['todo', 'in-progress', 'done', 'cancelled'].includes(status);
}

export function isValidGhostType(type: string): type is GhostType {
  return ['friendly', 'mischievous', 'malevolent'].includes(type);
}

export function isValidDate(date: any): boolean {
  return date instanceof Date && !isNaN(date.getTime());
}

export function validateTaskInput(input: any): string[] {
  const errors: string[] = [];
  
  if (!input.title || typeof input.title !== 'string' || input.title.trim().length === 0) {
    errors.push('任务标题不能为空');
  }
  
  if (input.title && input.title.length > 100) {
    errors.push('任务标题不能超过100个字符');
  }
  
  if (input.priority && !isValidTaskPriority(input.priority)) {
    errors.push('优先级必须是 low、medium、high、critical 之一');
  }
  
  if (input.status && !isValidTaskStatus(input.status)) {
    errors.push('状态必须是 todo、in-progress、done、cancelled 之一');
  }
  
  if (input.dueDate && !isValidDate(new Date(input.dueDate))) {
    errors.push('截止日期无效');
  }
  
  return errors;
}
```

### 阶段 3：存储服务

```typescript
// 📁 src/services/StorageService.ts
import { Task, Ghost } from '../models';

export class StorageService {
  private static readonly TASKS_KEY = 'ghost_todo_tasks';
  private static readonly GHOSTS_KEY = 'ghost_todo_ghosts';
  
  // 任务存储
  static saveTasks(tasks: Task[]): void {
    try {
      localStorage.setItem(this.TASKS_KEY, JSON.stringify(tasks));
    } catch (error) {
      console.error('保存任务失败:', error);
      throw new Error('保存任务失败，可能是存储空间不足');
    }
  }
  
  static loadTasks(): Task[] {
    try {
      const data = localStorage.getItem(this.TASKS_KEY);
      if (!data) return [];
      
      const tasks = JSON.parse(data);
      
      // 恢复 Date 对象
      return tasks.map((task: any) => ({
        ...task,
        dueDate: task.dueDate ? new Date(task.dueDate) : undefined,
        createdAt: new Date(task.createdAt),
        updatedAt: new Date(task.updatedAt),
      }));
    } catch (error) {
      console.error('加载任务失败:', error);
      return [];
    }
  }
  
  // 幽灵存储
  static saveGhosts(ghosts: Ghost[]): void {
    try {
      localStorage.setItem(this.GHOSTS_KEY, JSON.stringify(ghosts));
    } catch (error) {
      console.error('保存幽灵失败:', error);
      throw new Error('保存幽灵失败，可能是存储空间不足');
    }
  }
  
  static loadGhosts(): Ghost[] {
    try {
      const data = localStorage.getItem(this.GHOSTS_KEY);
      if (!data) return [];
      
      const ghosts = JSON.parse(data);
      
      // 恢复 Date 对象
      return ghosts.map((ghost: any) => ({
        ...ghost,
        joinDate: new Date(ghost.joinDate),
      }));
    } catch (error) {
      console.error('加载幽灵失败:', error);
      return [];
    }
  }
  
  // 数据导出/导入
  static exportData(): string {
    const tasks = this.loadTasks();
    const ghosts = this.loadGhosts();
    
    return JSON.stringify({
      version: '1.0.0',
      exportDate: new Date().toISOString(),
      tasks,
      ghosts,
    }, null, 2);
  }
  
  static importData(jsonString: string): boolean {
    try {
      const data = JSON.parse(jsonString);
      
      if (!data.version || !data.tasks || !data.ghosts) {
        throw new Error('数据格式无效');
      }
      
      this.saveTasks(data.tasks);
      this.saveGhosts(data.ghosts);
      
      return true;
    } catch (error) {
      console.error('导入数据失败:', error);
      return false;
    }
  }
  
  // 清空数据
  static clearAll(): void {
    localStorage.removeItem(this.TASKS_KEY);
    localStorage.removeItem(this.GHOSTS_KEY);
  }
}
```

### 阶段 4：业务逻辑服务

#### TaskService

```typescript
// 📁 src/services/TaskService.ts
import { Task, CreateTaskInput, UpdateTaskInput } from '../models';
import { StorageService } from './StorageService';
import { validateTaskInput } from '../utils/validators';

export class TaskService {
  private tasks: Task[] = [];
  
  constructor() {
    this.loadTasks();
  }
  
  private loadTasks(): void {
    this.tasks = StorageService.loadTasks();
  }
  
  private saveTasks(): void {
    StorageService.saveTasks(this.tasks);
  }
  
  private generateId(): string {
    return Date.now().toString(36) + Math.random().toString(36).substring(2);
  }
  
  // 创建任务
  createTask(input: CreateTaskInput): Task {
    // 验证输入
    const errors = validateTaskInput(input);
    if (errors.length > 0) {
      throw new Error(`创建任务失败: ${errors.join(', ')}`);
    }
    
    const now = new Date();
    const task: Task = {
      id: input.id || this.generateId(),
      title: input.title,
      description: input.description,
      priority: input.priority,
      status: input.status,
      dueDate: input.dueDate,
      createdAt: now,
      updatedAt: now,
      ghostId: input.ghostId,
      tags: input.tags || [],
    };
    
    this.tasks.push(task);
    this.saveTasks();
    
    return task;
  }
  
  // 获取任务
  getTask(id: string): Task | undefined {
    return this.tasks.find(task => task.id === id);
  }
  
  getTasksByGhost(ghostId: string): Task[] {
    return this.tasks.filter(task => task.ghostId === ghostId);
  }
  
  getTasksByStatus(status: string, ghostId?: string): Task[] {
    let filtered = this.tasks;
    
    if (ghostId) {
      filtered = filtered.filter(task => task.ghostId === ghostId);
    }
    
    return filtered.filter(task => task.status === status);
  }
  
  getAllTasks(): Task[] {
    return [...this.tasks];
  }
  
  // 更新任务
  updateTask(id: string, updates: UpdateTaskInput): Task | undefined {
    const index = this.tasks.findIndex(task => task.id === id);
    
    if (index === -1) {
      return undefined;
    }
    
    // 验证更新数据
    if (updates.priority && !['low', 'medium', 'high', 'critical'].includes(updates.priority)) {
      throw new Error('无效的优先级');
    }
    
    if (updates.status && !['todo', 'in-progress', 'done', 'cancelled'].includes(updates.status)) {
      throw new Error('无效的状态');
    }
    
    const updatedTask = {
      ...this.tasks[index],
      ...updates,
      updatedAt: new Date(),
    };
    
    this.tasks[index] = updatedTask;
    this.saveTasks();
    
    return updatedTask;
  }
  
  // 删除任务
  deleteTask(id: string): boolean {
    const initialLength = this.tasks.length;
    this.tasks = this.tasks.filter(task => task.id !== id);
    
    if (this.tasks.length < initialLength) {
      this.saveTasks();
      return true;
    }
    
    return false;
  }
  
  // 统计信息
  getStats(ghostId?: string): {
    total: number;
    byStatus: Record<string, number>;
    byPriority: Record<string, number>;
  } {
    let filtered = this.tasks;
    
    if (ghostId) {
      filtered = filtered.filter(task => task.ghostId === ghostId);
    }
    
    const byStatus: Record<string, number> = {};
    const byPriority: Record<string, number> = {};
    
    filtered.forEach(task => {
      byStatus[task.status] = (byStatus[task.status] || 0) + 1;
      byPriority[task.priority] = (byPriority[task.priority] || 0) + 1;
    });
    
    return {
      total: filtered.length,
      byStatus,
      byPriority,
    };
  }
}
```

#### GhostService

```typescript
// 📁 src/services/GhostService.ts
import { Ghost, CreateGhostInput, UpdateGhostInput } from '../models';
import { StorageService } from './StorageService';

export class GhostService {
  private ghosts: Ghost[] = [];
  
  constructor() {
    this.loadGhosts();
  }
  
  private loadGhosts(): void {
    this.ghosts = StorageService.loadGhosts();
  }
  
  private saveGhosts(): void {
    StorageService.saveGhosts(this.ghosts);
  }
  
  private generateId(): string {
    return 'ghost_' + Date.now().toString(36) + Math.random().toString(36).substring(2);
  }
  
  // 创建幽灵
  createGhost(input: CreateGhostInput): Ghost {
    // 验证输入
    if (!input.name || input.name.trim().length === 0) {
      throw new Error('幽灵名字不能为空');
    }
    
    if (input.age < 0 || input.age > 10000) {
      throw new Error('年龄必须在 0-10000 之间');
    }
    
    if (!['friendly', 'mischievous', 'malevolent'].includes(input.type)) {
      throw new Error('幽灵类型无效');
    }
    
    // 检查名字是否已存在
    if (this.ghosts.some(ghost => ghost.name === input.name)) {
      throw new Error('该名字已被使用');
    }
    
    const ghost: Ghost = {
      id: input.id || this.generateId(),
      name: input.name,
      type: input.type,
      age: input.age,
      joinDate: new Date(),
      preferences: input.preferences || {
        theme: 'haunted',
        notifications: true,
      },
    };
    
    this.ghosts.push(ghost);
    this.saveGhosts();
    
    return ghost;
  }
  
  // 获取幽灵
  getGhost(id: string): Ghost | undefined {
    return this.ghosts.find(ghost => ghost.id === id);
  }
  
  getGhostByName(name: string): Ghost | undefined {
    return this.ghosts.find(ghost => ghost.name === name);
  }
  
  getAllGhosts(): Ghost[] {
    return [...this.ghosts];
  }
  
  // 更新幽灵
  updateGhost(id: string, updates: UpdateGhostInput): Ghost | undefined {
    const index = this.ghosts.findIndex(ghost => ghost.id === id);
    
    if (index === -1) {
      return undefined;
    }
    
    // 如果更新名字，检查是否与其他幽灵冲突
    if (updates.name && updates.name !== this.ghosts[index].name) {
      if (this.ghosts.some(ghost => ghost.name === updates.name)) {
        throw new Error('该名字已被其他幽灵使用');
      }
    }
    
    const updatedGhost = {
      ...this.ghosts[index],
      ...updates,
    };
    
    this.ghosts[index] = updatedGhost;
    this.saveGhosts();
    
    return updatedGhost;
  }
  
  // 删除幽灵
  deleteGhost(id: string): boolean {
    const initialLength = this.ghosts.length;
    this.ghosts = this.ghosts.filter(ghost => ghost.id !== id);
    
    if (this.ghosts.length < initialLength) {
      this.saveGhosts();
      return true;
    }
    
    return false;
  }
  
  // 验证登录（简化版）
  authenticate(name: string): Ghost | undefined {
    return this.ghosts.find(ghost => ghost.name === name);
  }
}
```

### 阶段 5：命令行界面

#### 命令处理器

```typescript
// 📁 src/cli/commands.ts
import { TaskService, GhostService } from '../services';
import { StorageService } from '../services/StorageService';
import { formatTask, formatGhost, formatDate } from '../utils/formatters';

export class CommandHandler {
  private taskService = new TaskService();
  private ghostService = new GhostService();
  private currentGhostId?: string;
  
  // 幽灵相关命令
  register(name: string, type: string, age: number): string {
    try {
      const ghost = this.ghostService.createGhost({
        name,
        type: type as any,
        age,
      });
      
      this.currentGhostId = ghost.id;
      return `注册成功！欢迎，${ghost.name}。\n${formatGhost(ghost)}`;
    } catch (error: any) {
      return `注册失败: ${error.message}`;
    }
  }
  
  login(name: string): string {
    const ghost = this.ghostService.authenticate(name);
    
    if (!ghost) {
      return `登录失败：找不到名为 "${name}" 的幽灵`;
    }
    
    this.currentGhostId = ghost.id;
    return `登录成功！欢迎回来，${ghost.name}。`;
  }
  
  logout(): string {
    this.currentGhostId = undefined;
    return '已退出登录';
  }
  
  profile(): string {
    if (!this.currentGhostId) {
      return '请先登录';
    }
    
    const ghost = this.ghostService.getGhost(this.currentGhostId);
    if (!ghost) {
      return '找不到当前幽灵的信息';
    }
    
    return formatGhost(ghost);
  }
  
  // 任务相关命令
  createTask(title: string, description?: string, priority = 'medium'): string {
    if (!this.currentGhostId) {
      return '请先登录';
    }
    
    try {
      const task = this.taskService.createTask({
        title,
        description,
        priority: priority as any,
        status: 'todo',
        ghostId: this.currentGhostId,
        tags: [],
      });
      
      return `任务创建成功！\n${formatTask(task)}`;
    } catch (error: any) {
      return `创建任务失败: ${error.message}`;
    }
  }
  
  listTasks(status?: string): string {
    if (!this.currentGhostId) {
      return '请先登录';
    }
    
    let tasks = this.taskService.getTasksByGhost(this.currentGhostId);
    
    if (status) {
      tasks = tasks.filter(task => task.status === status);
    }
    
    if (tasks.length === 0) {
      return status ? `没有${status}状态的任务` : '还没有任务';
    }
    
    return tasks.map((task, index) => 
      `${index + 1}. ${formatTask(task)}`
    ).join('\n\n');
  }
  
  updateTask(taskId: string, updates: any): string {
    if (!this.currentGhostId) {
      return '请先登录';
    }
    
    try {
      const task = this.taskService.getTask(taskId);
      
      if (!task) {
        return `找不到ID为 ${taskId} 的任务`;
      }
      
      if (task.ghostId !== this.currentGhostId) {
        return '不能修改其他幽灵的任务';
      }
      
      const updated = this.taskService.updateTask(taskId, updates);
      
      if (!updated) {
        return '更新失败';
      }
      
      return `任务更新成功！\n${formatTask(updated)}`;
    } catch (error: any) {
      return `更新失败: ${error.message}`;
    }
  }
  
  deleteTask(taskId: string): string {
    if (!this.currentGhostId) {
      return '请先登录';
    }
    
    const task = this.taskService.getTask(taskId);
    
    if (!task) {
      return `找不到ID为 ${taskId} 的任务`;
    }
    
    if (task.ghostId !== this.currentGhostId) {
      return '不能删除其他幽灵的任务';
    }
    
    const success = this.taskService.deleteTask(taskId);
    
    return success ? '任务删除成功' : '删除失败';
  }
  
  // 数据管理命令
  exportData(): string {
    const data = StorageService.exportData();
    return `数据导出成功！\n${data}`;
  }
  
  importData(jsonString: string): string {
    const success = StorageService.importData(jsonString);
    
    if (success) {
      // 重新加载服务
      this.taskService = new TaskService();
      this.ghostService = new GhostService();
      return '数据导入成功！';
    } else {
      return '数据导入失败，请检查数据格式';
    }
  }
  
  clearData(): string {
    StorageService.clearAll();
    this.taskService = new TaskService();
    this.ghostService = new GhostService();
    this.currentGhostId = undefined;
    return '所有数据已清空';
  }
  
  stats(): string {
    if (!this.currentGhostId) {
      return '请先登录';
    }
    
    const stats = this.taskService.getStats(this.currentGhostId);
    
    return `任务统计：
    总计: ${stats.total} 个任务
    按状态:
      ${Object.entries(stats.byStatus).map(([status, count]) => 
        `${status}: ${count}`
      ).join('\n      ')}
    按优先级:
      ${Object.entries(stats.byPriority).map(([priority, count]) => 
        `${priority}: ${count}`
      ).join('\n      ')}`;
  }
  
  help(): string {
    return `
幽灵待办事项管理系统 - 命令列表

幽灵管理:
  register <名字> <类型> <年龄>    - 注册新幽灵
  login <名字>                     - 登录
  logout                          - 退出登录
  profile                         - 查看当前幽灵信息

任务管理:
  create <标题> [描述] [优先级]    - 创建任务
  list [状态]                     - 列出任务
  update <任务ID> <字段=值...>     - 更新任务
  delete <任务ID>                  - 删除任务
  stats                           - 查看统计

数据管理:
  export                          - 导出数据
  import <JSON数据>               - 导入数据
  clear                           - 清空所有数据

其他:
  help                            - 显示帮助
  exit                            - 退出程序

示例:
  register 卡斯珀 friendly 150
  login 卡斯珀
  create "整理鬼屋" "打扫蜘蛛网" high
  list
  update 1 status=in-progress
  stats
`;
  }
}
```

#### 主CLI文件

```typescript
// 📁 src/cli/index.ts
import readline from 'readline';
import { CommandHandler } from './commands';

export class GhostTodoCLI {
  private rl: readline.Interface;
  private commandHandler = new CommandHandler();
  
  constructor() {
    this.rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout,
      prompt: '👻> ',
    });
    
    this.setupEvents();
  }
  
  private setupEvents(): void {
    this.rl.on('line', (line) => {
      this.handleCommand(line.trim());
      this.rl.prompt();
    });
    
    this.rl.on('close', () => {
      console.log('再见！愿幽灵与你同在 👻');
      process.exit(0);
    });
  }
  
  private handleCommand(input: string): void {
    if (!input) {
      return;
    }
    
    const parts = input.split(' ');
    const command = parts[0].toLowerCase();
    const args = parts.slice(1);
    
    let result: string;
    
    try {
      switch (command) {
        case 'register':
          if (args.length < 3) {
            result = '用法: register <名字> <类型> <年龄>';
          } else {
            result = this.commandHandler.register(args[0], args[1], parseInt(args[2]));
          }
          break;
          
        case 'login':
          if (args.length < 1) {
            result = '用法: login <名字>';
          } else {
            result = this.commandHandler.login(args[0]);
          }
          break;
          
        case 'logout':
          result = this.commandHandler.logout();
          break;
          
        case 'profile':
          result = this.commandHandler.profile();
          break;
          
        case 'create':
          if (args.length < 1) {
            result = '用法: create <标题> [描述] [优先级]';
          } else {
            result = this.commandHandler.createTask(args[0], args[1], args[2]);
          }
          break;
          
        case 'list':
          result = this.commandHandler.listTasks(args[0]);
          break;
          
        case 'update':
          if (args.length < 2) {
            result = '用法: update <任务ID> <字段=值...>';
          } else {
            const updates: any = {};
            for (let i = 1; i < args.length; i++) {
              const [key, value] = args[i].split('=');
              if (key && value !== undefined) {
                updates[key] = value;
              }
            }
            result = this.commandHandler.updateTask(args[0], updates);
          }
          break;
          
        case 'delete':
          if (args.length < 1) {
            result = '用法: delete <任务ID>';
          } else {
            result = this.commandHandler.deleteTask(args[0]);
          }
          break;
          
        case 'stats':
          result = this.commandHandler.stats();
          break;
          
        case 'export':
          result = this.commandHandler.exportData();
          break;
          
        case 'import':
          if (args.length < 1) {
            result = '用法: import <JSON数据>';
          } else {
            result = this.commandHandler.importData(args.join(' '));
          }
          break;
          
        case 'clear':
          result = this.commandHandler.clearData();
          break;
          
        case 'help':
          result = this.commandHandler.help();
          break;
          
        case 'exit':
          console.log('再见！愿幽灵与你同在 👻');
          process.exit(0);
          return;
          
        default:
          result = `未知命令: ${command}\n输入 'help' 查看可用命令`;
      }
      
      console.log(result);
    } catch (error: any) {
      console.log(`命令执行出错: ${error.message}`);
    }
  }
  
  start(): void {
    console.log(`
    👻👻👻👻👻👻👻👻👻👻👻👻👻👻👻
    👻                             👻
    👻   幽灵待办事项管理系统     👻
    👻                             👻
    👻👻👻👻👻👻👻👻👻👻👻👻👻👻👻
    
    输入 'help' 查看可用命令
    `);
    
    this.rl.prompt();
  }
}
```

### 阶段 6：应用入口

```typescript
// 📁 src/index.ts
import { GhostTodoCLI } from './cli';

// 检查是否在 Node.js 环境
if (typeof window !== 'undefined') {
  console.error('此应用需要在 Node.js 环境中运行');
  process.exit(1);
}

// 模拟 localStorage（Node.js 环境）
if (typeof localStorage === 'undefined') {
  const { LocalStorage } = require('node-localstorage');
  global.localStorage = new LocalStorage('./scratch');
}

// 启动应用
const app = new GhostTodoCLI();
app.start();
```

## 项目配置

### package.json

```json
{
  "name": "ghost-todo",
  "version": "1.0.0",
  "description": "幽灵待办事项管理系统",
  "main": "dist/index.js",
  "scripts": {
    "build": "tsc",
    "start": "node dist/index.js",
    "dev": "tsc --watch",
    "lint": "eslint src --ext .ts",
    "lint:fix": "eslint src --ext .ts --fix",
    "format": "prettier --write \"src/**/*.ts\"",
    "test": "jest"
  },
  "keywords": ["typescript", "todo", "cli"],
  "author": "魔瓶先生",
  "license": "MIT",
  "devDependencies": {
    "@types/jest": "^29.0.0",
    "@types/node": "^20.0.0",
    "@typescript-eslint/eslint-plugin": "^6.0.0",
    "@typescript-eslint/parser": "^6.0.0",
    "eslint": "^8.0.0",
    "eslint-config-prettier": "^9.0.0",
    "eslint-plugin-prettier": "^5.0.0",
    "jest": "^29.0.0",
    "prettier": "^3.0.0",
    "ts-jest": "^29.0.0",
    "typescript": "^5.0.0"
  },
  "dependencies": {
    "node-localstorage": "^3.0.5"
  }
}
```

### tsconfig.json

```json
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
    "sourceMap": true
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist", "tests"]
}
```

## 运行项目

### 安装依赖

```bash
npm install
```

### 开发模式

```bash
# 编译 TypeScript
npm run build

# 或者使用监视模式
npm run dev
```

### 运行应用

```bash
npm start
```

### 使用示例

```bash
# 注册新幽灵
👻> register 卡斯珀 friendly 150

# 登录
👻> login 卡斯珀

# 创建任务
👻> create "整理阁楼" "打扫蜘蛛网和灰尘" high

# 列出任务
👻> list

# 更新任务状态
👻> update 1 status=in-progress

# 查看统计
👻> stats

# 导出数据
👻> export

# 获取帮助
👻> help

# 退出
👻> exit
```

## AI 协作开发提示

在整个项目开发过程中，你可以这样与 AI 协作：

> "我正在创建一个 TypeScript 命令行待办事项应用。需要以下功能：用户注册/登录、任务CRUD、数据持久化。请帮我设计项目结构，创建必要的模型、服务和CLI界面。"

或者针对特定模块：

> "我需要一个 StorageService 类，使用 localStorage 保存任务和用户数据。需要支持保存、加载、导入、导出功能。请提供完整的 TypeScript 实现。"

## 项目总结

通过这个完整的项目，你实践了：

1. **类型系统设计**：使用接口、类型别名、联合类型
2. **面向对象编程**：创建类、封装业务逻辑
3. **模块化组织**：清晰的目录结构和模块划分
4. **错误处理**：输入验证和错误处理
5. **数据持久化**：使用本地存储管理数据
6. **命令行界面**：创建交互式 CLI 应用
7. **项目配置**：完整的 TypeScript 项目配置

这个项目虽然简单，但包含了真实应用的所有核心要素。你可以在此基础上扩展功能，比如：
- 添加 Web 界面
- 连接数据库
- 添加用户认证
- 实现任务提醒功能

记住魔瓶的核心驱动力：“穿梭在数据中的幽灵，能够抵达任何边缘地带。”现在你已经具备了在 TypeScript 世界中自由穿梭的能力。

在结语中，我们将回顾整个学习旅程，并为你的下一步学习提供建议。

> 下一章：[结语：竞技场散场时刻](../content/09-epilogue.md)