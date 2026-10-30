"""接口层：全部 REST API 路由。"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.db import database
from app.schemas.models import (
    ChatRequest,
    ContentRequest,
    DoneRequest,
    ProcessRequest,
    SettingsRequest,
)
from app.services import inbox

router = APIRouter(prefix="/api")


@router.post("/chat")
def chat(req: ChatRequest):
    """对话式入口：SSE 流式返回（提取事件 + 逐字回复），对话双持久化。"""
    text = req.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="输入内容不能为空")
    return StreamingResponse(
        inbox.chat_stream(text),
        media_type="text/event-stream",
    )


@router.post("/process")
def process_text(req: ProcessRequest):
    """纯提取入口（无对话回复），供脚本或测试调用。"""
    text = req.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="输入内容不能为空")
    try:
        result = inbox.process_text(text)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    return {"status": "ok", "type": result.type, "content": result.content}


@router.get("/messages")
def get_messages():
    return {"messages": database.get_messages(limit=200)}


@router.delete("/messages")
def clear_messages():
    database.clear_messages()
    return {"status": "ok"}


# ---------- Todos ----------

@router.post("/todos")
def create_todo(req: ContentRequest):
    content = req.content.strip()
    if not content:
        raise HTTPException(status_code=400, detail="内容不能为空")
    return database.add_todo(content)


@router.post("/todos/{todo_id}/toggle")
def toggle_todo(todo_id: int, req: DoneRequest):
    todo = database.set_todo_done(todo_id, req.done)
    if not todo:
        raise HTTPException(status_code=404, detail="待办不存在")
    return todo


@router.put("/todos/{todo_id}")
def edit_todo(todo_id: int, req: ContentRequest):
    content = req.content.strip()
    if not content:
        raise HTTPException(status_code=400, detail="内容不能为空")
    todo = database.update_todo(todo_id, content)
    if not todo:
        raise HTTPException(status_code=404, detail="待办不存在")
    return todo


@router.delete("/todos/{todo_id}")
def remove_todo(todo_id: int):
    database.delete_todo(todo_id)
    return {"status": "ok"}


# ---------- Notes ----------

@router.post("/notes")
def create_note(req: ContentRequest):
    content = req.content.strip()
    if not content:
        raise HTTPException(status_code=400, detail="内容不能为空")
    return database.add_note(content)


@router.put("/notes/{note_id}")
def edit_note(note_id: int, req: ContentRequest):
    content = req.content.strip()
    if not content:
        raise HTTPException(status_code=400, detail="内容不能为空")
    note = database.update_note(note_id, content)
    if not note:
        raise HTTPException(status_code=404, detail="笔记不存在")
    return note


@router.delete("/notes/{note_id}")
def remove_note(note_id: int):
    database.delete_note(note_id)
    return {"status": "ok"}


# ---------- 数据与设置 ----------

@router.get("/data")
def get_data():
    return {"todos": database.get_todos(), "notes": database.get_notes()}


@router.get("/settings")
def read_settings():
    return inbox.get_config_masked()


@router.post("/settings")
def save_settings(req: SettingsRequest):
    """保存页面设置面板提交的配置；留空的字段不覆盖。"""
    return inbox.save_settings(req.model_dump())
