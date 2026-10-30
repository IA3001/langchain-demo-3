# AI Inbox（个人收件箱）

基于 **LangChain + 云端大模型** 的极简个人收件箱：在一个输入框里随手写一段话（待办、灵感、碎碎念），后端调用云端 LLM 自动判断意图——是待办、值得记录的笔记，还是纯闲聊（闲聊只对话、不入库）——右侧实时生成 Todo List 和 Notes 列表，左侧以流式方式逐字回复。

- 纯云端 LLM（OpenAI SDK 兼容接口，如 DeepSeek / 通义千问 / OpenAI），无任何本地模型
- 后端：Python 3.10+ / FastAPI / LangChain / SQLite
- 前端：单文件 HTML + Tailwind CDN + 原生 Fetch，无框架、无构建

## 核心架构

系统采用分层架构，自上而下依次为：接口层（路由与协议）、服务层（业务编排）、智能层（LangChain 链）、数据层（SQLite 持久化），配置管理与数据模型作为基础设施贯穿各层。

```
浏览器 (static/index.html)
   │  ① POST /api/chat  {"text": "帮我记一下明天要买牛奶"}
   ▼
接口层  app/api/routes.py          —— FastAPI 路由、参数校验、SSE 响应
   │  ② 调用服务层
   ▼
服务层  app/services/inbox.py      —— 业务编排：提取 -> 分类入库 -> SSE 组装
   │  ③ 调用智能层
   ▼
智能层  app/chains/extractor.py    —— Prompt -> ChatOpenAI(云端 LLM)
   │        -> with_structured_output(ExtractedData, json_mode)
   │  ④ 返回结构化结果 {type: "todo"|"note"|"chat", content: "..."}
   ▼
数据层  app/db/database.py         —— 按 type 写入 todos / notes / messages 表
   │
配置与模型  app/core/config.py     —— .env 兜底 + 设置表热更新
            app/schemas/models.py  —— Pydantic 模型约束
   ▼
浏览器  ⑤ SSE 流式渲染回复气泡 + GET /api/data 刷新右侧列表
```

## 项目结构

```
langchain-demo-3/
├── main.py                  # 启动入口（转引 app 工厂）
├── app/
│   ├── main.py              # FastAPI 应用工厂：装配路由 + 静态资源
│   ├── api/routes.py        # 接口层：全部 REST API（chat/process/todos/notes/settings）
│   ├── services/inbox.py    # 服务层：提取编排、分类入库、SSE 流组装、配置热更新
│   ├── chains/extractor.py  # 智能层：LangChain 结构化提取链 + 流式回复
│   ├── schemas/models.py    # 模型层：Pydantic 模型（LLM 输出约束 + 请求体）
│   ├── db/database.py       # 数据层：SQLite 建表迁移 + 增删改查
│   └── core/config.py       # 基础设施：配置管理（.env + 设置表合并）
├── static/index.html        # 单文件前端（左：AI 流式对话；右：Todos/Notes）
├── requirements.txt         # 依赖清单
└── .env.example             # 环境变量模板（复制为 .env 使用）
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

## 仓库链接

[https://github.com/IA3001/langchain-demo-3](https://github.com/IA3001/langchain-demo-3)
