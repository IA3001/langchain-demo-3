# AI Inbox（个人收件箱）

基于 **LangChain + 云端大模型** 的极简个人收件箱：在一个输入框里随手写一段话（待办、灵感、碎碎念），后端调用云端 LLM 自动判断意图——是待办、值得记录的笔记，还是纯闲聊（闲聊只对话、不入库）——右侧实时生成 Todo List 和 Notes 列表，左侧以流式方式逐字回复。

- 纯云端 LLM（OpenAI SDK 兼容接口，如 DeepSeek / 通义千问 / OpenAI），无任何本地模型
- 后端：Python 3.10+ / FastAPI / LangChain / SQLite
- 前端：单文件 HTML + Tailwind CDN + 原生 Fetch，无框架、无构建

## 核心架构

```
浏览器 (static/index.html)
   │  ① POST /api/chat  {"text": "帮我记一下明天要买牛奶", "history": [...]}
   ▼
FastAPI (main.py)
   │  ② extract_info()
   ▼
LangChain 链 (llm_chain.py)
   Prompt ──▶ ChatOpenAI（云端 LLM）──▶ with_structured_output(ExtractedData, json_mode)
   │  ③ 返回结构化结果 {type: "todo" | "note", content: "明天买牛奶"}
   ▼
SQLite (database.py)
   │  ④ 按 type 写入 todos / notes 表
   ▼
FastAPI ⑤ StreamingResponse 逐字流式返回 AI 对话式回复（带最近上下文）
   ▼
浏览器 ⑥ 流式渲染回复气泡 + GET /api/data 刷新右侧两个列表
```

## 从零运行

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 API Key

复制 `.env.example` 为 `.env`，填入你自己的配置（以 DeepSeek 为例）：

```env
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxx
OPENAI_BASE_URL=https://api.deepseek.com/v1
MODEL_NAME=deepseek-chat
```

也可以使用 OpenAI 官方接口：`OPENAI_BASE_URL=https://api.openai.com/v1`、`MODEL_NAME=gpt-4o-mini`。

### 3. 启动服务

```bash
uvicorn main:app --reload
```

### 4. 打开页面

浏览器访问 <http://127.0.0.1:8000>，在左侧输入任意一句话，点击发送即可看到右侧自动归类出的待办与笔记。

> 也可以不配置 `.env`：直接打开页面右上角「设置」，在弹窗里填 API Key / Base URL / 模型名，保存在本地 SQLite 并立即生效（Key 回显时自动打码）。`.env` 仅作为默认回退。

## 项目结构

```
langchain-demo-3/
├── requirements.txt     # 依赖清单
├── .env.example         # 环境变量模板（复制为 .env 使用）
├── database.py          # SQLite 建库建表 + todos/notes 增查
├── llm_chain.py         # Pydantic 模型 + Prompt + with_structured_output 提取链
├── main.py              # FastAPI 入口：/api/chat（流式对话）、/api/process、/api/data、设置、静态页挂载
└── static/
    └── index.html       # 三栏应用式前端（左：AI 流式对话；中：Todos；右：Notes）
```

## 仓库链接

[https://github.com/IA3001/langchain-demo-3](https://github.com/IA3001/langchain-demo-3)
