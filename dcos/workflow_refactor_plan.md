# workflow.py 模块化重构规划

## 当前问题
`services/workflow.py` 文件已接近2000行，代码臃肿，职责混杂，不符合“高内聚、低耦合”原则。

## 重构目标
1. 将庞大的 `ChatWorkflow` 类拆分为多个单一职责的模块
2. 保持现有接口不变，确保系统功能不受破坏
3. 提高代码可维护性和可测试性
4. 遵循项目已有的模块化架构模式

## 现有模块分析
项目已存在以下相关模块：
- `state_manager.py` - 状态管理
- `pruning_strategy.py` - 修剪策略
- `context_manager.py` - 上下文辅助函数
- `feedback_manager.py` - 反馈管理
- `sequence_manager.py` - 序列管理
- `prompt_logger.py` - 提示词日志
- `snapshot_manager.py` - 快照管理
- `warmup_runner.py` - 预热运行器

## 新模块设计

### 1. HistoryManager (`services/history_manager.py`) - 已创建
**职责**：
- 历史记录的加载、保存、基本操作
- 提供原子化的历史记录操作方法

**迁移方法**：
- `_load_history` → `load_history`
- `_save_history` → `save_history`
- `_add_to_history` 基础部分 → `add_message`
- `_add_summary_to_history` → `add_summary_message`
- `_update_user_prompt_in_history` → `update_user_prompt`
- `_infer_base_context_length` → `infer_base_context_length`
- `_create_minimal_history` → `create_minimal_history`
- `update_chapter_content_in_history` → `update_chapter_content`
- `get_chapter_content_from_history` → `get_chapter_content`
- `_remove_last_write_messages` → `remove_write_messages`

### 2. PromptRenderer (`services/prompt_renderer.py`) - 已创建
**职责**：
- 所有提示词模板的加载和渲染
- 设计、写作、总结阶段的提示词生成

**迁移方法**：
- `_load_world_view` → `load_world_view`
- `_load_system_prompt` → `load_system_prompt`
- `_load_feedback_prompt_template` → `load_feedback_prompt_template`
- `_load_prompt_template` → `load_prompt_template`
- `_render_design_prompt` → `render_design_prompt`
- `_render_simple_design_prompt` → `render_simple_design_prompt`
- `_render_write_prompt` → `render_write_prompt`
- `_render_simple_write_prompt` → `render_simple_write_prompt`
- `_render_summary_prompt` → `render_summary_prompt`

### 3. ContextBuilder (`services/context_builder.py`) - 已创建
**职责**：
- 构建LLM消息上下文，包括智能修剪
- 处理基准上下文、读者反馈、关键世界观消息、窗口消息的优先级

**迁移方法**：
- `_get_messages_for_llm` → `build_messages`
- `_get_feedback_for_context` → `_get_feedback_for_context`（私有方法）

### 4. SystemInitializer (`services/system_initializer.py`) - 待创建
**职责**：
- 系统初始化逻辑
- 处理全新启动和恢复运行两种场景

**迁移方法**：
- `_initialize_system` → `initialize_system`
- `_create_minimal_history` 部分逻辑
- `_infer_base_context_length` 调用

### 5. FileWriter (`services/file_writer.py`) - 待创建
**职责**：
- 章节文件的写入操作
- 文件名清理和路径管理

**迁移方法**：
- `_write_chapter_file` → `write_chapter_file`
- `write_chapter_to_file` → 保留在workflow中或迁移
- `_sanitize_filename` → 静态工具方法

### 6. PhaseHandlers (`services/phase_handlers.py`) - 待创建
**职责**：
- 各阶段（design/write/summary）的执行逻辑
- 生成章节内容和相似度检查

**迁移方法**：
- `run_design_phase` → `DesignPhaseHandler`
- `generate_chapter_content` → `WritePhaseHandler`
- `run_write_phase` → 可能整合
- `run_summary_phase` → `SummaryPhaseHandler`
- `_check_content_similarity` → 相似度检查器

### 7. PruningExecutor (`services/pruning_executor.py`) - 可能不需要
**说明**：已有 `PruningManager` 和 `PruningStrategy`，现有 `_execute_pruning` 方法已使用这些模块，只需保留协调逻辑。

## 迁移步骤

### 第一阶段：创建基础模块（已完成）
1. ✅ 创建 `HistoryManager`
2. ✅ 创建 `PromptRenderer`
3. ✅ 创建 `ContextBuilder`

### 第二阶段：更新 workflow.py 依赖注入
1. 在 `ChatWorkflow.__init__` 中初始化新模块
2. 替换原有方法调用为新模块方法
3. 确保所有测试通过

### 第三阶段：迁移业务逻辑
1. 将 `_initialize_system` 迁移到 `SystemInitializer`
2. 将文件写入逻辑迁移到 `FileWriter`
3. 将各阶段处理逻辑迁移到 `PhaseHandlers`

### 第四阶段：清理和优化
1. 删除 workflow.py 中已迁移的私有方法
2. 确保代码风格一致
3. 验证系统功能完整性

## 接口变更注意事项

### 保持向后兼容
- `ChatWorkflow` 的公共方法签名保持不变
- `run_step()`, `get_status()` 等对外接口不变
- 内部状态管理方式不变

### 依赖注入调整
`ChatWorkflow.__init__` 需要初始化新模块：

```python
def __init__(self):
    self.llm_client = LLMClient()
    self.parser = ContentParser()
    self.state_manager = StateManager()
    self.warmup_runner = WarmupRunner()
    self.feedback_manager = FeedbackManager()
    self.system_info_manager = SystemInfoManager()
    self.pruning_manager = PruningManager(self.state_manager)
    self.sequence_manager = get_sequence_manager()
    self.prompt_logger = get_prompt_logger()
    
    # 新模块
    self.history_manager = HistoryManager()
    self.prompt_renderer = PromptRenderer(
        state_manager=self.state_manager,
        system_info_manager=self.system_info_manager,
        sequence_manager=self.sequence_manager,
        prompt_logger=self.prompt_logger,
        world_view_content=self._load_world_view()
    )
    self.context_builder = ContextBuilder(
        state_manager=self.state_manager,
        feedback_manager=self.feedback_manager,
        prompt_logger=self.prompt_logger,
        history_manager=self.history_manager,
        prompt_renderer=self.prompt_renderer
    )
```

## 风险控制

### 备份策略
- 用户已备份 `workflow_backed.py`
- 每次迁移前创建git提交
- 逐步迁移，分批次验证

### 测试验证
- 运行现有系统，确保能正常生成章节
- 检查历史记录读写功能
- 验证修剪逻辑正常工作
- 确保断点续传功能不受影响

### 回滚方案
- 如果迁移出现问题，可快速回滚到备份版本
- 保持模块接口简单，便于调试

## 时间规划
1. 第一阶段：1小时（已完成）
2. 第二阶段：2小时
3. 第三阶段：2小时
4. 第四阶段：1小时

总计：6小时

## 成功标准
1. `workflow.py` 行数减少到500行以下
2. 系统所有功能正常工作
3. 代码结构清晰，符合模块化架构
4. 便于后续功能扩展和维护