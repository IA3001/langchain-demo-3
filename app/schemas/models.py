"""Pydantic 数据模型：LLM 结构化输出约束 + API 请求体。"""

from typing import Literal

from pydantic import BaseModel, Field


class ExtractedData(BaseModel):
    """从用户输入中提取出的结构化信息。"""

    type: Literal["todo", "note", "chat"] = Field(
        description="信息类型：todo 表示待办任务，note 表示笔记/备忘录，"
        "chat 表示纯闲聊/提问（无需记录）"
    )
    content: str = Field(
        description="提取出的核心内容，去除语气词等冗余表达；chat 类型原样返回输入"
    )


class ProcessRequest(BaseModel):
    text: str


class ChatRequest(BaseModel):
    text: str


class ContentRequest(BaseModel):
    content: str


class DoneRequest(BaseModel):
    done: bool


class SettingsRequest(BaseModel):
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = ""
    MODEL_NAME: str = ""
