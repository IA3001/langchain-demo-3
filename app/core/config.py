"""配置管理：.env 兜底 + 数据库 settings 表热更新（页面设置面板优先）。"""

import os
from dotenv import load_dotenv

load_dotenv()

# .env 默认值（回退配置）
ENV_API_KEY = os.getenv("OPENAI_API_KEY", "")
ENV_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com/v1")
ENV_MODEL = os.getenv("MODEL_NAME", "deepseek-chat")

SETTING_KEYS = ("OPENAI_API_KEY", "OPENAI_BASE_URL", "MODEL_NAME")


def get_effective_config(db_settings: dict) -> dict:
    """合并配置：数据库保存值优先，.env 兜底。"""
    return {
        "api_key": db_settings.get("OPENAI_API_KEY") or ENV_API_KEY,
        "base_url": db_settings.get("OPENAI_BASE_URL") or ENV_BASE_URL,
        "model": db_settings.get("MODEL_NAME") or ENV_MODEL,
    }


def mask_key(key: str) -> str:
    if len(key) > 8:
        return f"{key[:3]}****{key[-4:]}"
    return "已配置" if key else ""
