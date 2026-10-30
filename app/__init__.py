"""应用包：AI Inbox 分层架构。

app/
├── api/        接口层：FastAPI 路由定义
├── services/   服务层：业务逻辑（提取编排、SSE 组装）
├── chains/     智能层：LangChain 结构化提取与流式回复
├── schemas/    模型层：Pydantic 数据模型
├── db/         数据层：SQLite 持久化
└── core/       基础设施：配置管理
"""
