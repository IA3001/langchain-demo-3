"""LangChain 结构化提取链：Prompt -> ChatOpenAI(云端) -> with_structured_output。"""

import os
from typing import Literal

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "deepseek-chat")


class ExtractedData(BaseModel):
    """从用户输入中提取出的结构化信息。"""

    type: Literal["todo", "note", "chat"] = Field(
        description="信息类型：todo 表示待办任务，note 表示笔记/备忘录，"
        "chat 表示纯闲聊/提问（无需记录）"
    )
    content: str = Field(
        description="提取出的核心内容，去除语气词等冗余表达；chat 类型原样返回输入"
    )


EXTRACT_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "你是一个信息提取助手。请判断用户的输入属于哪一类，"
            "以 JSON 格式输出，只包含两个字段：\n"
            '1. "type"：字符串，取值三选一：\n'
            '   - "todo"：包含需要完成的任务、安排或行动项（如"明天要买牛奶"）；\n'
            '   - "note"：值得记录下来以备后用的灵感、想法、备忘录等信息；\n'
            '   - "chat"：纯闲聊、问候、向助手提问、咨询能做什么等'
            "没有任何需要记录内容的话，只是想和助手对话。\n"
            '2. "content"：字符串，当 type 为 todo 或 note 时提取核心内容'
            "（去除\"帮我记一下\"\"我想要\"等语气词和冗余表达），"
            '当 type 为 chat 时原样返回用户输入。\n'
            '例如："帮我记一下明天要买牛奶" 输出 {{"type": "todo", "content": "明天买牛奶"}}；'
            '"我突然想到这个产品可以用区块链重做" 输出 '
            '{{"type": "note", "content": "这个产品可以用区块链重做"}}；'
            '"你可以帮我干什么" 输出 {{"type": "chat", "content": "你可以帮我干什么"}}。',
        ),
        ("human", "{user_input}"),
    ]
)

_chain = None
_llm = None


REPLY_PROMPT = (
    "你是「AI Inbox」个人收件箱助手。用户刚刚记录了一条{kind}：「{content}」。\n"
    "请用自然友好的中文简短回复（1~2 句话）：确认已记录，并视内容给一句有用的"
    "补充或建议。不要机械重复用户原话，不要用 markdown 列表。"
)

CHAT_PROMPT = (
    "你是「AI Inbox」个人收件箱助手，可以帮用户记录待办和灵感笔记。\n"
    "用户这句话没有任何需要记录的内容，只是想和你对话。"
    "请用自然友好的中文简短回复（一般 1~3 句话），直接回答问题或继续闲聊；"
    "如果用户的话里其实藏了待办或值得记录的想法，可以提醒他直接说出来，你会帮他记下。"
    "不要说「已记录」之类的话。"
)


def _get_config() -> dict:
    """配置来源：settings 表（页面设置面板保存）优先，.env 作为回退。"""
    import database

    saved = database.get_settings()
    return {
        "api_key": saved.get("OPENAI_API_KEY") or OPENAI_API_KEY,
        "base_url": saved.get("OPENAI_BASE_URL") or OPENAI_BASE_URL,
        "model": saved.get("MODEL_NAME") or MODEL_NAME,
    }


def get_config_masked() -> dict:
    """返回给前端的配置：key 打码，只显示末 4 位。"""
    cfg = _get_config()
    key = cfg["api_key"]
    masked = f"{key[:3]}****{key[-4:]}" if len(key) > 8 else ("已配置" if key else "")
    return {
        "OPENAI_API_KEY": masked,
        "OPENAI_BASE_URL": cfg["base_url"],
        "MODEL_NAME": cfg["model"],
        "key_configured": bool(key),
    }


def reset_chain() -> None:
    """配置变更后重建 LLM 与提取链。"""
    global _chain, _llm
    _chain = None
    _llm = None


def _get_llm() -> ChatOpenAI:
    global _llm
    if _llm is None:
        cfg = _get_config()
        if not cfg["api_key"]:
            raise RuntimeError(
                "未配置 OPENAI_API_KEY，请点击页面右上角「设置」填写，"
                "或在 .env 中配置后重启"
            )
        _llm = ChatOpenAI(
            api_key=cfg["api_key"],
            base_url=cfg["base_url"],
            model=cfg["model"],
            temperature=0.7,
        )
    return _llm


def _get_chain():
    """惰性构建提取链：未配置 key 时应用仍能启动，调用时才报清晰错误。"""
    global _chain
    if _chain is None:
        # json_mode：兼容 DeepSeek 思考型模型（它们不支持强制 tool_choice /
        # json_schema 响应格式）
        _chain = EXTRACT_PROMPT | _get_llm().with_structured_output(
            ExtractedData, method="json_mode"
        )
    return _chain


def stream_reply(
    user_input: str, extracted: ExtractedData, history: list[dict]
):
    """流式生成对话式回复。

    history: 最近几轮对话，格式 [{"role": "user"|"assistant", "content": str}]。
    生成器逐段产出文本；网络异常时产出错误提示而不是抛异常，保证前端流不中断。
    """
    try:
        llm = _get_llm()
    except Exception as exc:
        yield f"配置异常：{exc}"
        return

    if extracted.type == "chat":
        system = CHAT_PROMPT
    else:
        kind = "待办" if extracted.type == "todo" else "笔记"
        system = REPLY_PROMPT.format(kind=kind, content=extracted.content)
    messages = [SystemMessage(content=system)]
    for m in history[-8:]:
        content = (m.get("content") or "").strip()
        if not content:
            continue
        if m.get("role") == "user":
            messages.append(HumanMessage(content=content))
        else:
            messages.append(AIMessage(content=content))
    messages.append(HumanMessage(content=user_input))

    try:
        for chunk in llm.stream(messages):
            if chunk.content:
                yield chunk.content
    except Exception as exc:
        yield f"\n[回复生成失败：{exc}]"


def extract_info(user_input: str) -> ExtractedData:
    """调用云端大模型，把一段自由文本提取为结构化的 todo / note。

    网络异常、鉴权失败等都会被转换为 RuntimeError，由上层接口统一处理。
    """
    try:
        result = _get_chain().invoke({"user_input": user_input})
    except Exception as exc:  # 网络/鉴权/限流等异常统一兜底
        raise RuntimeError(f"调用大模型失败：{exc}") from exc

    if not isinstance(result, ExtractedData):
        raise RuntimeError("模型返回结果无法解析为结构化数据")
    return result
