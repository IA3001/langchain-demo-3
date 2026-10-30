"""AI Inbox 后端入口：FastAPI + SQLite + LangChain 结构化提取 + 流式对话。"""

import json
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import database
from llm_chain import extract_info, get_config_masked, reset_chain, stream_reply

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent


@asynccontextmanager
async def lifespan(_: FastAPI):
    database.init_db()
    yield


app = FastAPI(title="AI Inbox", lifespan=lifespan)


class ProcessRequest(BaseModel):
    text: str


class ChatRequest(BaseModel):
    text: str


class ContentRequest(BaseModel):
    content: str


class DoneRequest(BaseModel):
    done: bool


# ---------- AI 对话与提取 ----------

def _sse(payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


@app.post("/api/chat")
def chat(req: ChatRequest):
    """对话式入口：SSE 流式返回（提取事件 + 逐字回复），对话双持久化。"""
    text = req.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="输入内容不能为空")

    history = [
        {"role": m["role"], "content": m["content"]}
        for m in database.get_messages(limit=20)
        if m["role"] in ("user", "assistant")
    ]

    try:
        result = extract_info(text)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    if result.type == "todo":
        database.add_todo(result.content)
    elif result.type == "note":
        database.add_note(result.content)

    database.add_message("user", text)
    database.add_message(
        "event",
        json.dumps({"type": result.type, "content": result.content}, ensure_ascii=False),
    )

    def generate():
        # 先推送提取结果事件，前端据此显示状态条
        yield _sse({"event": "extracted", "type": result.type, "content": result.content})
        reply = ""
        for chunk in stream_reply(text, result, history):
            if not chunk:
                continue
            reply += chunk
            yield _sse({"event": "delta", "text": chunk})
        if reply.strip():
            database.add_message("assistant", reply)
        yield _sse({"event": "done"})

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
    )


@app.post("/api/process")
def process_text(req: ProcessRequest):
    """纯提取入口（无对话回复），供脚本或测试调用。"""
    text = req.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="输入内容不能为空")

    try:
        result = extract_info(text)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    if result.type == "todo":
        database.add_todo(result.content)
    elif result.type == "note":
        database.add_note(result.content)

    return {"status": "ok", "type": result.type, "content": result.content}


@app.get("/api/messages")
def get_messages():
    return {"messages": database.get_messages(limit=200)}


@app.delete("/api/messages")
def clear_messages():
    database.clear_messages()
    return {"status": "ok"}


# ---------- Todos ----------

@app.post("/api/todos")
def create_todo(req: ContentRequest):
    content = req.content.strip()
    if not content:
        raise HTTPException(status_code=400, detail="内容不能为空")
    return database.add_todo(content)


@app.post("/api/todos/{todo_id}/toggle")
def toggle_todo(todo_id: int, req: DoneRequest):
    todo = database.set_todo_done(todo_id, req.done)
    if not todo:
        raise HTTPException(status_code=404, detail="待办不存在")
    return todo


@app.put("/api/todos/{todo_id}")
def edit_todo(todo_id: int, req: ContentRequest):
    content = req.content.strip()
    if not content:
        raise HTTPException(status_code=400, detail="内容不能为空")
    todo = database.update_todo(todo_id, content)
    if not todo:
        raise HTTPException(status_code=404, detail="待办不存在")
    return todo


@app.delete("/api/todos/{todo_id}")
def remove_todo(todo_id: int):
    database.delete_todo(todo_id)
    return {"status": "ok"}


# ---------- Notes ----------

@app.post("/api/notes")
def create_note(req: ContentRequest):
    content = req.content.strip()
    if not content:
        raise HTTPException(status_code=400, detail="内容不能为空")
    return database.add_note(content)


@app.put("/api/notes/{note_id}")
def edit_note(note_id: int, req: ContentRequest):
    content = req.content.strip()
    if not content:
        raise HTTPException(status_code=400, detail="内容不能为空")
    note = database.update_note(note_id, content)
    if not note:
        raise HTTPException(status_code=404, detail="笔记不存在")
    return note


@app.delete("/api/notes/{note_id}")
def remove_note(note_id: int):
    database.delete_note(note_id)
    return {"status": "ok"}


# ---------- 数据与设置 ----------

@app.get("/api/data")
def get_data():
    return {"todos": database.get_todos(), "notes": database.get_notes()}


class SettingsRequest(BaseModel):
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = ""
    MODEL_NAME: str = ""


@app.get("/api/settings")
def read_settings():
    return get_config_masked()


@app.post("/api/settings")
def save_settings(req: SettingsRequest):
    """保存页面设置面板提交的配置；留空的字段不覆盖。"""
    for field in ("OPENAI_API_KEY", "OPENAI_BASE_URL", "MODEL_NAME"):
        value = getattr(req, field).strip()
        if value:
            database.set_setting(field, value)
    reset_chain()  # 立即生效，无需重启
    return get_config_masked()


# 静态页面必须挂在 API 路由之后，避免遮蔽 /api/*
app.mount("/", StaticFiles(directory=BASE_DIR / "static", html=True), name="static")
