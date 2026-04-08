# Summary C 开发方案

## 1. 背景与需求
当前系统已在每完成一个章节窗口（3章）后执行总结阶段，包含两次总结调用：
1. **Summary B**：使用 `prompts/summary_b` 模板生成单元记忆
2. **常规 Summary**：使用 `prompts/summary.txt` 模板生成单元规划

现有痛点：两次总结虽然能提供单元记忆和规划，但缺乏对整体写作进度的宏观记录，导致长线写作过程中可能丢失全局视角。

**核心需求**：在现有两次总结之前，增加一次额外的总结调用（Summary C），使用不同的提示词（`prompts/summary_c.txt`），但使用与常规总结相同的变量（`{{window_chapters}}`、`{{chapter_1}}`、`{{chapter_2}}`、`{{chapter_3}}`、`{{next_chapter_1}}`、`{{next_chapter_2}}`、`{{world_view}}`）。生成的总结内容需与常规总结、summary_b一同保留在历史记录中，供后续创作参考。

**关键约束**：
- 不破坏现有总结与修剪流程。
- 保留 assistant 的总结内容（包括 summary_c、summary_b、常规总结）。
- 总结的 user 部分可以删除（即不保存冗长的用户提示词）。
- 确保状态持久化和断点续传不受影响。

## 2. 现有总结流程分析
当前总结阶段由 `ChatWorkflow.run_summary_phase()`（`services/workflow.py` 第1275-1333行）实现，其步骤如下：

1. **获取窗口章节**：从 `StateManager` 读取当前窗口（例如 `[4,5,6]`）。
2. **渲染 summary_b 提示词**：调用 `_render_summary_b_prompt()`，使用 `prompts/summary_b` 模板。
3. **构建消息列表**：调用 `_get_messages_for_llm()` 获取当前上下文（包含基准上下文、读者反馈、关键世界观、窗口消息等）。
4. **调用 LLM 生成 summary_b**：通过 `LLMClient.chat()` 生成总结内容。
5. **保存 summary_b 助手消息**：调用 `_add_summary_to_history()` 添加 `role="assistant"`、`stage="summary"`、`is_summary=True` 的消息。
6. **渲染常规总结提示词**：调用 `_render_summary_prompt()`，使用 `prompts/summary.txt` 模板。
7. **再次构建消息列表**：此时上下文已包含 summary_b 的助手消息。
8. **调用 LLM 生成常规总结**：再次通过 `LLMClient.chat()` 生成总结内容。
9. **保存常规总结助手消息**：调用 `_add_summary_to_history()` 添加第二条总结消息。
10. **执行修剪**：调用 `_execute_pruning()`，基于窗口章节删除前两章的所有记录，保留第三章、关键世界观消息和所有属于当前窗口的总结消息。

修剪逻辑（`_execute_pruning_fallback` 和 `PruningManager`）目前已支持保留同一窗口内的所有总结消息（不只最新的一条）。这是实现三条总结共存的基础。

## 3. 设计原则
- **最小侵入**：在现有 `run_summary_phase` 方法内部增加一次 LLM 调用，不引入新的阶段（stage）。
- **变量复用**：summary_c 使用与常规总结完全相同的变量集，确保模板渲染一致性。
- **状态透明**：不修改 `StateManager` 的状态字段，仅增加历史记录条目。
- **修剪兼容**：调整修剪逻辑，保留同一窗口内生成的三条总结消息（summary_c、summary_b、常规总结）。
- **健壮性**：遵循“拒绝假数据”原则，真实调用 LLM API；使用 `tenacity` 重试机制。

## 4. 模块变更清单
### 4.1 新增/修改文件
1. **`services/prompt_renderer.py`** – 增加 `render_summary_c_prompt()` 方法，用于渲染 `prompts/summary_c.txt` 模板。
2. **`services/workflow.py`** – 修改 `ChatWorkflow` 类：
   - 增加 `_render_summary_c_prompt()` 方法（委托给 `prompt_renderer.render_summary_c_prompt`）。
   - 修改 `run_summary_phase()`，在 summary_b 之前增加 summary_c 调用。
   - 调整 `_execute_pruning_fallback()`，确保保留三条总结消息（已支持）。
3. **`prompts/summary_c.txt`** – 已存在，内容为写作进度纪要，变量与 `summary.txt` 一致。

### 4.2 新增方法说明
- `_render_summary_c_prompt()`：返回渲染后的 summary_c 提示词字符串。
- `_add_summary_to_history()`：现有方法，用于添加总结消息。无需修改，因为 summary_c 与 summary_b、常规总结使用相同的字段。

### 4.3 修剪逻辑调整
当前 `_execute_pruning_fallback` 第825-847行和 `PruningManager` 中的 `SlidingWindowPruner`、`StatusBasedPruner` 均已支持保留同一窗口的所有总结消息。因此无需修改，只需确保三条总结的 `window_chapters` 字段与当前窗口匹配即可。

**状态管理机制确保不会删除新的留下旧的**：
- `StateManager` 维护一个递增的 `summary_status_counter` 字段，每次调用 `_add_summary_to_history` 都会分配一个递增的状态编号。
- 总结消息中会记录 `summary_status` 字段，该字段随着每次总结生成而单调递增。
- 修剪器（特别是 `StatusBasedPruner`）在需要选择单个总结时，会优先选择 `summary_status` 最大的总结（即最新的总结）。
- 对于同一窗口内的多个总结（summary_c、summary_b、常规总结），修剪器会保留所有属于当前窗口的总结，不会因为状态编号差异而删除其中任何一条。
- 因此，新生成的总结（状态编号更大）在跨窗口修剪时会被优先保留，不会出现“删除新的留下旧的”问题。


## 5. 详细实现步骤
### 5.1 修改 `prompt_renderer.py` – 添加 `render_summary_c_prompt` 方法
在 `render_summary_b_prompt` 方法后添加：

```python
def render_summary_c_prompt(self) -> str:
    """渲染总结C阶段提示词（在summary_b和常规总结之前调用）"""
    template = self.load_prompt_template("summary_c.txt")
    
    # 获取窗口章节
    window_chapters = self.state_manager.get_window_chapters()
    if len(window_chapters) != 3:
        logger.warning(f"窗口章节数量不正确: {window_chapters}，应为3章")
        # 使用默认值
        window_chapters = [0, 0, 0]
    
    chapter_1, chapter_2, chapter_3 = window_chapters
    
    # 计算下一章
    next_chapter_1 = chapter_3 + 1
    next_chapter_2 = chapter_3 + 2
    
    # 替换模板变量（与常规总结使用相同的变量集）
    prompt = template.replace("{{window_chapters}}", str(window_chapters))
    prompt = prompt.replace("{{chapter_1}}", str(chapter_1))
    prompt = prompt.replace("{{chapter_2}}", str(chapter_2))
    prompt = prompt.replace("{{chapter_3}}", str(chapter_3))
    prompt = prompt.replace("{{next_chapter_1}}", str(next_chapter_1))
    prompt = prompt.replace("{{next_chapter_2}}", str(next_chapter_2))
    prompt = prompt.replace("{{world_view}}", self.world_view_content if self.world_view_content else "")
    
    # 清理多余的占位符
    prompt = prompt.replace("{{window_chapters}}", str(window_chapters))
    prompt = prompt.replace("{{chapter_1}}", str(chapter_1))
    prompt = prompt.replace("{{chapter_2}}", str(chapter_2))
    prompt = prompt.replace("{{chapter_3}}", str(chapter_3))
    prompt = prompt.replace("{{next_chapter_1}}", str(next_chapter_1))
    prompt = prompt.replace("{{next_chapter_2}}", str(next_chapter_2))
    prompt = prompt.replace("{{world_view}}", "")
    
    logger.info(f"总结C提示词已渲染: 窗口章节={window_chapters}, 下一章={next_chapter_1},{next_chapter_2}")
    
    return prompt
```

### 5.2 修改 `workflow.py` – 添加 `_render_summary_c_prompt` 方法
在 `_render_summary_b_prompt` 方法后添加：

```python
def _render_summary_c_prompt(self) -> str:
    """渲染总结C阶段提示词（在summary_b和常规总结之前调用）"""
    return self.prompt_renderer.render_summary_c_prompt()
```

### 5.3 修改 `run_summary_phase` – 三总结调用
将原有双总结扩展为三步：

1. **调用 summary_c**：
   - 渲染 summary_c 提示词。
   - 使用 `_get_messages_for_llm()` 构建消息列表。
   - 调用 LLM 生成 summary_c 内容。
   - 保存助手消息（调用 `_add_summary_to_history`），不保存用户消息。

2. **调用 summary_b**：
   - 渲染 summary_b 提示词。
   - 重新构建消息列表（此时上下文已包含 summary_c 的助手消息）。
   - 调用 LLM 生成 summary_b 内容。
   - 保存助手消息，不保存用户消息。

3. **调用常规 summary**：
   - 渲染常规总结提示词。
   - 重新构建消息列表（此时上下文已包含 summary_c 和 summary_b 的助手消息）。
   - 调用 LLM 生成常规总结内容。
   - 保存助手消息，不保存用户消息。

4. **执行修剪**：
   - 调用 `_execute_pruning()`，保留第三章写作消息、关键世界观消息以及三条总结消息。

**实现代码**（在 `run_summary_phase` 方法中修改）：

```python
def run_summary_phase(self) -> None:
    logger.info("开始总结阶段")
    
    # 获取当前窗口状态
    window_chapters = self.state_manager.get_window_chapters()
    logger.info(f"总结阶段窗口章节: {window_chapters}")
    
    summary_chapter = 0
    if window_chapters:
        summary_chapter = max(window_chapters)
        logger.info(f"总结消息关联到章节 {summary_chapter} (窗口最大章节)")
    
    # 第一步：生成summary_c总结
    logger.info("生成summary_c总结...")
    summary_c_prompt = self._render_summary_c_prompt()
    summary_c_messages = self._get_messages_for_llm()
    summary_c_messages.append({"role": "user", "content": summary_c_prompt})
    
    try:
        summary_c_response = self.llm_client.chat(summary_c_messages)
    except Exception as e:
        logger.error(f"summary_c总结阶段LLM调用失败: {e}")
        # 使用简化接口作为后备
        system_prompt = self._load_system_prompt()
        summary_c_response = self.llm_client.simple_chat(
            user_message=summary_c_prompt,
            system_message=system_prompt
        )
    
    # 保存summary_c助手消息（总结），不保存用户消息
    self._add_summary_to_history(summary_c_response, summary_chapter, window_chapters)
    logger.info(f"summary_c总结已生成并保存到历史记录，长度: {len(summary_c_response)} 字符")
    
    # 第二步：生成summary_b总结（在summary_c之后，上下文已更新）
    logger.info("生成summary_b总结...")
    summary_b_prompt = self._render_summary_b_prompt()
    summary_b_messages = self._get_messages_for_llm()  # 注意：此时历史记录已包含summary_c的对话
    summary_b_messages.append({"role": "user", "content": summary_b_prompt})
    
    try:
        summary_b_response = self.llm_client.chat(summary_b_messages)
    except Exception as e:
        logger.error(f"summary_b总结阶段LLM调用失败: {e}")
        # 使用简化接口作为后备
        system_prompt = self._load_system_prompt()
        summary_b_response = self.llm_client.simple_chat(
            user_message=summary_b_prompt,
            system_message=system_prompt
        )
    
    # 保存summary_b助手消息（总结），不保存用户消息
    self._add_summary_to_history(summary_b_response, summary_chapter, window_chapters)
    logger.info(f"summary_b总结已生成并保存到历史记录，长度: {len(summary_b_response)} 字符")
    
    # 第三步：生成常规总结（在summary_b之后，上下文已更新）
    logger.info("生成常规总结...")
    regular_prompt = self._render_summary_prompt()
    regular_messages = self._get_messages_for_llm()  # 此时历史记录已包含summary_c和summary_b的对话
    regular_messages.append({"role": "user", "content": regular_prompt})
    
    try:
        regular_response = self.llm_client.chat(regular_messages)
    except Exception as e:
        logger.error(f"常规总结阶段LLM调用失败: {e}")
        # 使用简化接口作为后备
        system_prompt = self._load_system_prompt()
        regular_response = self.llm_client.simple_chat(
            user_message=regular_prompt,
            system_message=system_prompt
        )
    
    # 保存常规总结助手消息，不保存用户消息
    self._add_summary_to_history(regular_response, summary_chapter, window_chapters)
    logger.info(f"常规总结已生成并保存到历史记录，长度: {len(regular_response)} 字符")
    
    # 执行修剪逻辑（将保留同一窗口内的三个总结消息）
    self._execute_pruning()
    
    logger.info("总结阶段完成（包含summary_c、summary_b和常规总结）")
```

### 5.4 删除总结用户消息（可选）
现有逻辑已不保存用户消息，因此无需额外操作。

## 6. 文件变更清单
### 6.1 已存在的文件
1. **`prompts/summary_c.txt`** – 提示词文件（已存在）。

### 6.2 待执行的修改
1. **`services/prompt_renderer.py`**：
   - 添加 `render_summary_c_prompt()` 方法。
2. **`services/workflow.py`**：
   - 添加 `_render_summary_c_prompt()` 方法。
   - 修改 `run_summary_phase()` 实现三总结调用。

### 6.3 配置文件
- 无新增配置文件。

## 7. 状态持久化与断点续传
- 状态文件 `data/state.json` 不受影响，因为总结阶段不改变 `StateManager` 的状态字段（除 `summary_status` 递增外）。
- 历史记录文件 `data/history.json` 将新增三条 assistant 总结消息，以及可能的用户消息（但会被修剪删除）。
- 断点续传：若在总结阶段中断，恢复后 `stage` 仍为 `"summary"`，会重新执行整个 `run_summary_phase`。这可能导致重复生成总结。但现有机制已能处理（因为 `stage` 在修剪完成后才重置为 `"design"`）。中断后重新执行总结阶段是安全的，但会额外增加 LLM 调用。考虑到发生率低，可接受。

## 8. 测试验证方法
1. **单元测试**：
   - 测试 `render_summary_c_prompt` 是否正确渲染变量。
   - 测试 `run_summary_phase` 是否按顺序调用三次 LLM。
   - 测试修剪逻辑是否保留了三条总结消息。

2. **集成测试**：
   - 运行一个完整窗口（3章）到总结阶段，观察历史记录中是否出现三条 assistant 总结消息。
   - 检查修剪后的历史记录是否包含第三章写作消息、关键世界观消息、以及三条总结消息。
   - 验证后续章节生成是否正常（上下文长度是否可控）。

3. **回归测试**：
   - 确保现有 Reader、Auditor 等功能不受影响。
   - 确保修剪逻辑在其他场景下（如非总结阶段）行为不变。

## 9. 已知注意事项
1. **token 消耗**：三总结调用会增加约 50% 的 token 使用量（相比双总结），但总结阶段频率较低（每3章一次），影响可控。
2. **上下文长度**：三条总结消息会留在历史记录中，增加上下文长度。但修剪后，三条总结消息均保留，相比原来仅两条，增加了一条消息的长度。需确保上下文限制（128k token）仍充足。
3. **总结质量**：summary_c 与 summary_b、常规总结内容互补，分别关注写作进度、单元记忆和单元规划，预期能提供更全面的创作上下文。
4. **修剪逻辑的兼容性**：PruningManager（主修剪器）已支持同一窗口内多个总结，无需修改。

## 10. 扩展性与后续优化
- **总结类型标记**：未来可增加 `summary_type` 字段，便于区分不同类型的总结（如“写作纪要”、“单元记忆”、“单元规划”）。
- **动态提示词选择**：可根据窗口内容自动选择不同的总结提示词模板。
- **总结消息压缩**：若三条总结内容高度重叠，可合并为一条，减少上下文占用。

## 11. 总结
本方案通过最小化代码修改，在现有总结阶段前增加一次 summary_c 调用，生成额外写作进度纪要，丰富创作上下文。调整修剪逻辑以保留同一窗口内的所有总结消息，确保后续创作能利用更多资料。方案遵循“高内聚、低耦合”原则，不破坏现有流程，且维持状态持久化和断点续传能力。

**开发状态**：方案设计完成，待实现。