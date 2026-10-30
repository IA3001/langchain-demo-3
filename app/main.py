"""应用入口：创建 FastAPI 实例，装配路由与静态资源。"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.db import database

PROJECT_ROOT = Path(__file__).resolve().parents[1]


@asynccontextmanager
async def lifespan(_: FastAPI):
    database.init_db()
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="AI Inbox", lifespan=lifespan)
    app.include_router(router)
    # 静态页面必须挂在 API 路由之后，避免遮蔽 /api/*
    app.mount("/", StaticFiles(directory=PROJECT_ROOT / "static", html=True), name="static")
    return app


app = create_app()
