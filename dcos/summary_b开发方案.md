# Summary B 开发方案

## 1. 背景与需求
当前系统已在每完成一个章节窗口（3章）后执行总结（summary）阶段，生成窗口内容的总结并存入历史，随后进行上下文修剪（pruning），删除前两章内容，保留第三章及总结，以控制上下文长度。

现有痛点：总结阶段仅使用单一提示词（`prompts/summary.txt`），生成的总结可能无法充分捕获创作所需的关键信息，导致后续创作时“资料有点少，创作起来有点懵”。

**核心需求**：在现有总结阶段之前，增加一次额外的总结调用（Summary B），使用不同的提示词（`prompts/summary_b`），但使用与常规总结相同的变量（`{{window_chapters}}`、`{{chapter_1}}`、`{{chapter_2}}`、`{{chapter_3}}`、`{{next_chapter_1}}`、`{{next_chapter_2}}`、`{{world_view}}`）。生成的总结内容需与常规总结一同保留在历史记录中，供后续创作参考。

**关键约束**：
- 不破坏现有总结与修剪流程。
- 保留 assistant 的总结内容（包括常规总结与 summary_b）。
- 总结的 user 部分可以删除（即不保存冗长的用户提示词）。
- 确保状态持久化和断点续传不受影响。

## 2. 现有总结流程分析
当前总结阶段由 `ChatWorkflow.run_summary_phase()`（`services/workflow.py` 第1246-1293行）实现，其步骤如下：

1. **获取窗口章节**：从 `StateManager` 读取当前窗口（例如 `[4,5,6]`）。
2. **渲染提示词**：调用 `_render_summary_prompt()`，使用 `prompts/summary.txt` 模板。
3. **构建消息列表**：调用 `_get_messages_for_llm()` 获取当前上下文（包含基准上下文、读者反馈、关键世界观、窗口消息等）。
4. **调用 LLM**：通过 `LLMClient.chat()` 生成总结内容。
5. **保存历史记录**：
   - 用户消息：使用 `_add_to_history()` 添加 `role="user"`、`stage="summary"` 的消息（章节号设为0）。
   - 助手消息：使用 `_add_summary_to_history()` 添加 `role="assistant"`、`stage="summary"`、`is_summary=True` 的消息，并记录窗口章节、关联章节等元数据。
6. **执行修剪**：调用 `_execute_pruning()`，基于窗口章节删除前两章的所有记录，保留第三章、关键世界观消息和总结消息（仅保留最新的一条总结）。

修剪逻辑（`_execute_pruning_fallback`）目前只保留**最新的总结消息**（按时间戳排序取最后一条）。这是需要调整的点。

## 3. 设计原则
- **最小侵入**：在现有 `run_summary_phase` 方法内部增加一次 LLM 调用，不引入新的阶段（stage）。
- **变量复用**：summary_b 使用与常规总结完全相同的变量集，确保模板渲染一致性。
- **状态透明**：不修改 `StateManager` 的状态字段，仅增加历史记录条目。
- **修剪兼容**：调整修剪逻辑，保留同一窗口内生成的多条总结消息（summary_b 与常规总结）。
- **健壮性**：遵循“拒绝假数据”原则，真实调用 LLM API；使用 `tenacity` 重试机制。

## 4. 模块变更清单
### 4.1 新增/修改文件
1. **`services/prompt_renderer.py`** – 已增加 `render_summary_b_prompt()` 方法，用于渲染 `prompts/summary_b` 模板。
2. **`services/workflow.py`** – 修改 `ChatWorkflow` 类：
   - 增加 `_render_summary_b_prompt()` 方法（委托给 `prompt_renderer.render_summary_b_prompt`）。
   - 修改 `run_summary_phase()`，在常规总结之前增加 summary_b 调用。
   - 调整 `_execute_pruning_fallback()`，使其保留同一窗口内的所有总结消息（而不仅是最新的一条）。
3. **`prompts/summary_b`** – 已存在，内容为独立的总结提示词，变量与 `summary.txt` 一致。

### 4.2 新增方法说明
- `_render_summary_b_prompt()`：返回渲染后的 summary_b 提示词字符串。
- `_add_summary_to_history()`：现有方法，用于添加总结消息。需要扩展以支持可选的 `stage` 参数（默认为 `"summary"`），以便区分 summary_b 与常规总结。但为简化，可仍使用同一 `stage="summary"`，而通过其他字段（如 `summary_type`）区分，或仅靠顺序区分。考虑到修剪逻辑通过 `stage=="summary" or is_summary==True` 识别总结消息，使用相同 `stage` 即可，因为两者都是总结。

### 4.3 修剪逻辑调整
当前 `_execute_pruning_fallback` 第813-818行：
```python
if summary_messages:
    summary_messages.sort(key=lambda x: x[1].get("timestamp", 0))
    latest_summary_index, latest_summary_msg = summary_messages[-1]
    new_history.append(latest_summary_msg)
```
这将丢弃除最新总结外的所有总结。需改为保留同一窗口内生成的所有总结消息（即 `window_chapters` 匹配的消息）。识别窗口的方法：总结消息的 `window_chapters` 字段记录了其所属窗口。因此，可以筛选出 `window_chapters` 等于当前窗口章节列表的消息，全部保留。

同时，需确保 **summary_b 与常规总结的 `window_chapters` 相同**（因为它们总结的是同一个窗口）。

## 5. 详细实现步骤
### 5.1 修改 `workflow.py` – 添加 `_render_summary_b_prompt` 方法
在 `_render_summary_prompt` 方法后添加：
```python
def _render_summary_b_prompt(self) -> str:
    """渲染总结B阶段提示词（在常规总结之前调用）"""
    return self.prompt_renderer.render_summary_b_prompt()
```

### 5.2 修改 `run_summary_phase` – 双总结调用
将原有单一总结拆分为两步：

1. **调用 summary_b**：
   - 渲染 summary_b 提示词。
   - 使用相同的消息列表（`_get_messages_for_llm()` + 用户消息）调用 LLM。
   - 保存用户消息（可选，可删除）。
   - 保存助手消息（调用 `_add_summary_to_history`，但可考虑增加一个标记，例如 `summary_type="b"`）。

2. **调用常规 summary**：
   - 渲染常规总结提示词。
   - 再次构建消息列表（此时上下文已包含 summary_b 的用户和助手消息？注意：`_get_messages_for_llm()` 会读取最新历史记录，其中已包含刚刚添加的 summary_b 消息，这可能导致总结内容冗余。但考虑到总结阶段紧接着执行修剪，且总结消息的章节号为0，不会被窗口章节筛选，可能不会影响总结生成。为简化，可复用同一套消息列表，但需注意 token 增加。更安全的方式是：在 summary_b 调用后，立即将 summary_b 的用户消息从历史记录中删除（因为用户要求“总结的user部分可以删除”），仅保留 assistant 消息。这样第二次总结时，上下文不会包含额外的用户提示词。

**简化方案**：
- 不保存 summary_b 的用户消息（直接调用 LLM，但不写入历史）。
- 只保存 summary_b 的 assistant 消息（使用 `_add_summary_to_history`，但添加一个字段 `summary_type="b"`）。
- 然后进行常规总结：保存用户消息（可删除）、保存助手消息（`summary_type="regular"`）。

然而，`_add_summary_to_history` 目前没有 `summary_type` 参数。可扩展该方法，或使用现有的 `summary_status` 字段区分（但该字段是递增数字）。为简单起见，可以不加区分，因为两者都是总结，修剪时都会保留。

**实现步骤**（伪代码）：
```python
def run_summary_phase(self):
    window_chapters = self.state_manager.get_window_chapters()
    # 1. Summary B
    prompt_b = self._render_summary_b_prompt()
    messages = self._get_messages_for_llm()
    messages.append({"role": "user", "content": prompt_b})
    response_b = self.llm_client.chat(messages)
    # 不保存用户消息，只保存助手消息
    summary_chapter = max(window_chapters) if window_chapters else 0
    self._add_summary_to_history(response_b, summary_chapter, window_chapters)
    
    # 2. 常规 Summary
    prompt = self._render_summary_prompt()
    # 重新构建消息列表，因为历史记录已新增了summary_b的助手消息
    messages = self._get_messages_for_llm()
    messages.append({"role": "user", "content": prompt})
    response = self.llm_client.chat(messages)
    # 保存用户消息（后续可删除）
    self._add_to_history("user", prompt, 0, "summary", simplify_user_prompt=False)
    self._add_summary_to_history(response, summary_chapter, window_chapters)
    
    # 3. 执行修剪
    self._execute_pruning()
```

### 5.3 修改 `_add_summary_to_history` 以支持可选的 `stage` 参数
目前方法签名：`_add_summary_to_history(self, content: str, summary_chapter: int, window_chapters: List[int])`
可以增加一个可选参数 `stage: str = "summary"`，但调用处都传 `"summary"`。也可以增加一个字段 `summary_type` 在消息中。

考虑到后续可能需要区分，但当前需求仅要求保留 assistant 内容，不要求区分类型。因此可暂不修改，使用相同的 `stage="summary"` 和 `is_summary=True`。两条总结消息仅时间戳不同。

### 5.4 调整修剪逻辑
修改 `_execute_pruning_fallback` 中关于总结消息的处理：

**当前逻辑**：收集所有 `stage=="summary" or is_summary==True` 的消息，按时间戳排序，只保留最新的一条。

**新逻辑**：保留所有属于当前窗口的总结消息（即 `window_chapters` 字段与当前窗口匹配的消息）。同时，为防止历史积累过多，仍应只保留同一窗口内的总结（因为跨窗口的总结已被之前的修剪删除）。

实现：
```python
# 筛选属于当前窗口的总结消息
window_summary_messages = []
for idx, msg in summary_messages:
    if msg.get("window_chapters") == window_chapters:
        window_summary_messages.append((idx, msg))
# 保留所有窗口内的总结消息
for idx, msg in window_summary_messages:
    new_history.append(msg)
```

注意：`window_chapters` 是列表，比较时需确保顺序一致。消息中的 `window_chapters` 字段与当前窗口相同。

### 5.5 删除总结用户消息（可选）
用户提到“总结的user部分可以删除”。可以在常规总结的用户消息保存后，在某个时机（例如修剪前）将其从历史记录中删除。但删除用户消息会影响上下文构建吗？修剪时，用户消息属于“前两章”吗？用户消息的章节号为0，阶段为“summary”，不属于任何章节，因此修剪逻辑会将其归类为“其他消息”并删除（因为 `chapter not in chapters_to_remove` 且 `stage != "summary"`？实际上 `stage=="summary"` 但 `role=="user"` 且 `is_summary==False`，因此会被归为“其他消息”并删除。所以现有逻辑已会删除用户消息。无需额外操作。

## 6. 文件变更清单
### 6.1 已完成的修改
1. **`services/prompt_renderer.py`** – 新增 `render_summary_b_prompt()` 方法（已实现）。
2. **`prompts/summary_b`** – 提示词文件（已存在）。

### 6.2 待执行的修改
1. **`services/workflow.py`**：
   - 添加 `_render_summary_b_prompt()` 方法。
   - 修改 `run_summary_phase()` 实现双总结调用。
   - 修改 `_execute_pruning_fallback()` 保留同一窗口的所有总结消息。
   - （可选）修改 `_add_summary_to_history` 以增加 `summary_type` 字段。

### 6.3 配置文件
- 无新增配置文件。

## 7. 状态持久化与断点续传
- 状态文件 `data/state.json` 不受影响，因为总结阶段不改变 `StateManager` 的状态字段（除 `summary_status` 递增外）。
- 历史记录文件 `data/history.json` 将新增两条 assistant 总结消息，以及可能的用户消息（但会被修剪删除）。
- 断点续传：若在总结阶段中断，恢复后 `stage` 仍为 `"summary"`，会重新执行整个 `run_summary_phase`。这可能导致重复生成总结。但现有机制已能处理（因为 `stage` 在修剪完成后才重置为 `"design"`）。中断后重新执行总结阶段是安全的，但会额外增加 LLM 调用。考虑到发生率低，可接受。

## 8. 测试验证方法
1. **单元测试**：
   - 测试 `render_summary_b_prompt` 是否正确渲染变量。
   - 测试 `run_summary_phase` 是否按顺序调用两次 LLM。
   - 测试修剪逻辑是否保留了多条总结消息。

2. **集成测试**：
   - 运行一个完整窗口（3章）到总结阶段，观察历史记录中是否出现两条 assistant 总结消息。
   - 检查修剪后的历史记录是否包含第三章写作消息、关键世界观消息、以及两条总结消息。
   - 验证后续章节生成是否正常（上下文长度是否可控）。

3. **回归测试**：
   - 确保现有 Reader、Auditor 等功能不受影响。
   - 确保修剪逻辑在其他场景下（如非总结阶段）行为不变。

## 9. 已知注意事项
1. **token 消耗**：双总结调用会增加约一倍的 token 使用量，但总结阶段频率较低（每3章一次），影响可控。
2. **上下文长度**：summary_b 的助手消息会留在历史记录中，增加上下文长度。但修剪后，两条总结消息均保留，相比原来仅一条，增加了一条消息的长度。需确保上下文限制（128k token）仍充足。
3. **总结质量**：summary_b 与常规总结可能内容相似，但提示词不同，预期能提供互补信息。
4. **修剪逻辑的兼容性**：PruningManager（主修剪器）可能也有类似的“只保留最新总结”逻辑，需要同步修改。`pruning_strategy.py` 中的 `StatusBasedPruner` 需要检查并调整。本方案暂时只修改降级方案（`_execute_pruning_fallback`），主修剪器需另行评估。

## 10. 扩展性与后续优化
- **总结类型标记**：未来可增加 `summary_type` 字段，便于区分不同类型的总结（如“情节总结”、“人物总结”）。
- **动态提示词选择**：可根据窗口内容自动选择不同的总结提示词模板。
- **总结消息压缩**：若两条总结内容高度重叠，可合并为一条，减少上下文占用。

## 11. 总结
本方案通过最小化代码修改，在现有总结阶段前增加一次 summary_b 调用，生成额外总结内容，丰富创作上下文。调整修剪逻辑以保留同一窗口内的所有总结消息，确保后续创作能利用更多资料。方案遵循“高内聚、低耦合”原则，不破坏现有流程，且维持状态持久化和断点续传能力。

**开发状态**：部分已实现（prompt_renderer），剩余修改待执行。