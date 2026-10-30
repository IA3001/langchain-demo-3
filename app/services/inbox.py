"""服务层：业务逻辑编排（提取 -> 分类入库 -> SSE 回复组装）。"""

import json
from typing import Iterator

from app.chains.extractor import extract_info, reset_chain, stream_reply
from app.core import config
from app.db import database
from app.schemas.models import ExtractedData


def _persist_extracted(result: ExtractedData) -> None:
    """按提取类型落库：todo/note 写入对应表，chat 不记录。"""
    if result.type == "todo":
        database.add_todo(result.content)
    elif result.type == "note":
        database.add_note(result.content)


def process_text(user_input: str) -> ExtractedData:
    """纯提取入口：结构化提取并入库。"""
    result = extract_info(user_input)
    _persist_extracted(result)
    return result


def _build_history(limit: int = 20) -> list[dict]:
    return [
        {"role": m["role"], "content": m["content"]}
        for m in database.get_messages(limit=limit)
        if m["role"] in ("user", "assistant")
    ]


def _sse(payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


def chat_stream(user_input: str) -> Iterator[str]:
    """对话式入口：提取入库后，SSE 流式返回（提取事件 + 逐字回复）。

    全程持久化：用户消息、提取事件、AI 回复都写入 messages 表。
    """
    history = _build_history()
    result = extract_info(user_input)
    _persist_extracted(result)

    database.add_message("user", user_input)
    database.add_message(
        "event",
        json.dumps({"type": result.type, "content": result.content}, ensure_ascii=False),
    )

    # 先推送提取结果事件，前端据此显示状态条
    yield _sse({"event": "extracted", "type": result.type, "content": result.content})
    reply = ""
    for chunk in stream_reply(user_input, result, history):
        if not chunk:
            continue
        reply += chunk
        yield _sse({"event": "delta", "text": chunk})
    if reply.strip():
        database.add_message("assistant", reply)
    yield _sse({"event": "done"})


# ---------- 配置相关（转发给接口层） ----------

def get_config_masked() -> dict:
    """返回给前端的配置：key 打码，只显示末 4 位。"""
    cfg = config.get_effective_config(database.get_settings())
    return {
        "OPENAI_API_KEY": config.mask_key(cfg["api_key"]),
        "OPENAI_BASE_URL": cfg["base_url"],
        "MODEL_NAME": cfg["model"],
        "key_configured": bool(cfg["api_key"]),
    }


def save_settings(values: dict) -> dict:
    """保存页面设置面板提交的配置；留空的字段不覆盖。保存后重建链即时生效。"""
    for field, value in values.items():
        value = (value or "").strip()
        if value:
            database.set_setting(field, value)
    reset_chain()
    return get_config_masked()
