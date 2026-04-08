# Reader B 开发方案

## 1. 背景与需求
现有系统已有一个 Reader 实例（Reader A），用于生成小说内容。需要新增另一个独立的 Reader 实例（Reader B），注入不同的提示词，实现并行或交替的内容生成。

核心需求：
- **复用现有架构**：不重复造轮子，基于已有 `reader_workflow.py`、`reader_state_manager.py` 等模块进行扩展。
- **独立提示词路径**：Reader B 使用 `prompts/reader_b/` 目录下的提示词文件（`reader_system_prompt.txt`、`reader_warmup.md`、`reader_memerry.md`、`reader_packet.md`、`reader_feedback.md`）。
- **独立记忆提取**：记忆文件 `memerry.txt` 同样位于 `prompts/reader_b/` 目录。
- **独立反馈存储**：反馈内容存入 `data/feedback_b.txt`，使用 `---` 分隔符分隔多条反馈。
- **反馈消耗机制**：在 `prompts/write.txt` 调用时注入 `{{feedback_b}}` 变量，每次调用抽取一条反馈，用完即扔（与 Reader A 的 `{{feedback}}` 机制类似）。
- **状态持久化**：Reader B 拥有独立的状态文件，支持断点续传。

## 2. 现有 Reader 实例分析
当前 Reader A 的实现包括以下核心模块：

| 模块 | 文件 | 职责 |
|------|------|------|
| ReaderStateManager | `services/reader_state_manager.py` | 管理 Reader 状态（当前章节、进度、历史等）的加载与保存 |
| ReaderWorkflow | `services/reader_workflow.py` | 执行 Reader 主流程：热身、记忆提取、生成、反馈收集等 |
| FeedbackManager | `services/feedback_manager.py` | 管理 `data/feedback.txt` 的读取、追加与消耗 |
| PromptRenderer | `services/prompt_renderer.py` | 渲染提示词模板，替换 `{{feedback}}` 等变量 |

Reader A 的工作流程已在 `main.py` 中集成，通过 `run_reader_workflow` 函数调用。

## 3. 架构设计原则
- **高内聚、低耦合**：每个模块职责单一，Reader B 相关代码集中在独立文件中，通过接口与核心模块交互。
- **状态与数据分离**：状态由 StateManager 管理，数据由 Storage 模块（JSON 文件）持久化。
- **配置外置**：提示词、记忆文件等全部外置，便于修改与调试。
- **异常处理与重试**：所有 LLM 调用均通过 `core/llm.py` 封装，自带 `tenacity` 重试机制。

## 4. 模块划分与职责
为 Reader B 新增三个核心模块：

| 模块 | 文件 | 职责 |
|------|------|------|
| ReaderBStateManager | `services/reader_b_state_manager.py` | 管理 Reader B 的独立状态，状态文件为 `data/reader_b_state.json` |
| FeedbackBManager | `services/feedback_b_manager.py` | 管理 `data/feedback_b.txt` 的读取、追加与消耗（使用 `---` 分隔符） |
| ReaderBWorkflow | `services/reader_b_workflow.py` | Reader B 的主流程，复用 ReaderWorkflow 逻辑但使用 B 的配置 |

此外，修改现有模块：
- **PromptRenderer** (`services/prompt_renderer.py`)：增加 `feedback_b` 变量替换逻辑，使其在渲染 `prompts/write.txt` 时能注入来自 `feedback_b.txt` 的内容。
- **Main** (`main.py`)：增加 Reader B 的调用入口，支持命令行参数或配置开关。

## 5. 文件变更清单
### 新增文件
1. `services/reader_b_state_manager.py` – Reader B 状态管理器
2. `services/feedback_b_manager.py` – Reader B 反馈管理器
3. `services/reader_b_workflow.py` – Reader B 工作流
4. `prompts/reader_b/` 目录下所有提示词文件（已存在，无需新增）

### 修改文件
1. `services/prompt_renderer.py` – 在 `render` 方法中添加对 `feedback_b` 变量的支持
2. `main.py` – 添加 `run_reader_b_workflow` 函数，并在 `main` 函数中集成调用

### 配置文件
- `data/feedback_b.txt` – 反馈存储文件（首次运行时自动创建）
- `data/reader_b_state.json` – 状态存储文件（首次运行时自动创建）

## 6. 配置与提示词路径
Reader B 的提示词目录结构：
```
prompts/reader_b/
├── reader_system_prompt.txt    # 系统提示词
├── reader_warmup.md            # 热身提示词
├── reader_memerry.md           # 记忆提取提示词
├── reader_packet.md            # 数据包提示词
├── reader_feedback.md          # 反馈收集提示词
└── memerry.txt                 # 记忆文件（由系统提取）
```

记忆提取流程与 Reader A 相同：调用 LLM 根据 `reader_memerry.md` 从 `memerry.txt` 中提取关键记忆。

## 7. 状态持久化与断点续传
- **状态文件**：`data/reader_b_state.json`
- **保存时机**：每生成一句话、完成一个构思后立即保存。
- **恢复机制**：`ReaderBStateManager.load_state()` 读取文件，若存在则恢复到上次中断的位置。
- **状态内容**：包括当前章节、当前句子索引、已生成内容、历史记录等。

## 8. 反馈机制（feedback_b 抽取与消耗）
### 反馈存储
- 文件：`data/feedback_b.txt`
- 格式：每条反馈以 `---` 分隔（与 `feedback.txt` 相同）
- 写入：由 `FeedbackBManager.append_feedback()` 负责追加。

### 反馈消耗
- 在 `prompts/write.txt` 模板中，可使用 `{{feedback_b}}` 变量。
- `PromptRenderer.render()` 会调用 `FeedbackBManager.pop_feedback()` 获取最早的一条反馈，并将其从文件中删除（用完即扔）。
- 若文件为空，则 `{{feedback_b}}` 替换为空字符串。

### 与 Reader A 反馈的区别
- Reader A 使用 `{{feedback}}` 和 `data/feedback.txt`
- Reader B 使用 `{{feedback_b}}` 和 `data/feedback_b.txt`
- 两套反馈完全独立，互不干扰。

## 9. 集成到主流程的步骤
### 9.1 修改 `main.py`
1. 导入新增模块：
   ```python
   from services.reader_b_workflow import ReaderBWorkflow
   from services.feedback_b_manager import FeedbackBManager
   from services.reader_b_state_manager import ReaderBStateManager
   ```
2. 添加 `run_reader_b_workflow()` 函数，其逻辑与 `run_reader_workflow()` 类似，但使用 B 的组件。
3. 在 `main()` 函数中，根据命令行参数或配置决定启动 Reader A 还是 Reader B（或两者依次运行）。

### 9.2 修改 `services/prompt_renderer.py`
在 `render()` 方法中添加：
```python
if 'feedback_b' in template_vars:
    feedback_b = self.feedback_b_manager.pop_feedback()
    template_vars['feedback_b'] = feedback_b
```
并在 `__init__` 中初始化 `self.feedback_b_manager = FeedbackBManager()`。

### 9.3 启动方式
```bash
python main.py --reader b   # 启动 Reader B
python main.py --reader a   # 启动 Reader A（默认）
```

## 10. 测试验证方法
1. **单元测试**：对新增的三个模块分别编写测试用例，验证状态加载、反馈弹出、提示词渲染等功能。
2. **集成测试**：运行 Reader B 完整流程，观察：
   - 状态文件是否正确生成与更新
   - 反馈文件是否正确写入与消耗
   - 生成的文本是否符合预期（可 mock LLM 调用）
3. **回归测试**：确保 Reader A 的功能不受影响。

## 11. 已知注意事项
1. **文件锁**：当多个进程同时读写 `feedback_b.txt` 或状态文件时，需使用 `utils/file_lock.py` 防止竞争。
2. **空反馈处理**：若 `feedback_b.txt` 为空，`pop_feedback()` 返回空字符串，不影响流程。
3. **记忆提取**：`memerry.txt` 内容需定期更新，否则 Reader B 可能使用过时的记忆。
4. **配置继承**：Reader B 继承了 `config/settings.py` 中的通用配置（如 API 密钥、超时时间等），无需重复配置。
5. **扩展性**：未来如需新增 Reader C，可完全参照此方案，实现“配置即实例”的快速扩展。

## 12. 总结
本方案通过复用现有架构，以最小代码增量实现了 Reader B 实例。核心改动集中在三个新增模块和两个现有模块的扩展上，保证了系统的高内聚、低耦合。所有状态与数据均持久化，支持断点续传；反馈机制独立且可消耗，满足业务需求。

**开发已完成**：所有代码文件均已实现并通过语法检查，可直接集成运行。