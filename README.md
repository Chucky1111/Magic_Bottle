# DeepNovelV3 Lite - AI自动小说创作系统

一个遵循"高内聚、低耦合"原则的模块化AI小说创作系统，支持断点续传和健壮的LLM API调用。

分为两部分，写作agent，一直往后写
reader部分，调用两个api实例阅读，提供反馈，写作agent接受到后在后面的章节打补丁，没有修改之前或现在章节的功能
建议写作agent用强一点的模型，reader用弱一点的，可以在.env中设置模型

`My_novel\prompts\system_prompt.txt`这里面是人格提示词，性格魔瓶的部分决定了整个写作的色彩和情感偏好，需要更换的话在`bottles_zh`中寻找喜欢的性格复制，然后覆盖掉提示词中的性格魔瓶的部分。
`My_novel\prompts\reader`和`My_novel\prompts\reader_b`也是同理

提示词都是分离出来的，你可以在`prompts\`中自由修改

### 写三章之后就会触发三次总结，然后保留最近一章和总结内容，继续写三章，然后再剪切。
这样可以节省不少token，这个逻辑是硬编码的，当时确实没想清楚。
但是输出高质量章节不成问题，只是只能以单元剧情推进长篇，可以用户灵感的形式人工召回之前的线索和人机协同。

## 快速开始

### 1. 安装依赖

```bash
cd M_novel && pip install -r requirements.txt
```

### 2. 配置API

复制环境变量模板并填写您的API配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件，配置您的LLM API：

```env
# 使用DeepSeek
LLM_API_KEY=your_deepseek_api_key
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-chat

# 或使用DMXAPI
# LLM_API_KEY=your_dmxapi_key
# LLM_BASE_URL=https://www.dmxapi.cn/v1
# LLM_MODEL=qwen-flash

# 或使用OpenAI官方
# LLM_API_KEY=your_openai_key
# LLM_BASE_URL=https://api.openai.com/v1
# LLM_MODEL=gpt-4o
```

### 3. 测试连接

运行测试脚本验证API配置：

```bash
python test_llm_connection.py
```

如果一切正常，您将看到类似以下输出：
```
✅ 连接成功!
   模型: deepseek-chat
   接口地址: https://api.deepseek.com
   响应时间: 1.23秒
   测试响应: Hello! I'm online and ready to help...
```

### 4.创建缺失的文件
```bash
.\init_files.ps1
```

### 5.在world_填入小说设定和书名，主角的名字，世界观之类的

### 6.运行，开始创作
```bash
python main.py
```
这个命令会持续运行
需要等五分钟左右冷启动，然后可以在data/draft底下看见章节内容了

```bash
python main.py --cc 5
```
这个命令意味着持续运行五章就停止，后面的数字可以改成任意数字

```bash
python main.py --ct 5
```
意味着写到第五章就停止，所以后面的数字必须比已经完成的章节数目要大

### 7.如果想控制剧情可以在prompt/user_idea底下填入内容，用---分隔开即可，每一块对应一章，用完会直接舍弃

## 其他

### 1. 格式清洗脚本：
```bash
python process_output.py
```
会清洗掉不是、、、而是的句式，还能替换一些ai味重的词语和短语，配置文件在`My_novel\config\sensitive_words.txt`这个文件，文件导出到output_process\目录下面，你可以在脚本里面修改导出路径

### 定点重启脚本

```bash
python restore_snapshot.py --help
```

我忘了参数是什么了，help之后按照说明调整即可，这个功能有小bug，但是不影响使用。
定点重启后只写一章就开始总结，不影响情节连贯。

### 导出为epub电子书
```bash
python export_to_epub.py
```

### 欢迎贡献者debug、开发新功能和优化提示词

### 感谢您对魔瓶项目的支持，希望您的创作之旅顺利
