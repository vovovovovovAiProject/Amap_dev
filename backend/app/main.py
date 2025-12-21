"""
智途无忧 - 基于高德开发平台的AI智能助手
后端主入口
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api import routes
import os

from contextlib import asynccontextmanager
from app.db.database import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(
    title="智途无忧 API",
    description="基于高德MCP + 通义千问的智能出行规划API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS配置 - 允许前端跨域访问
# 虽然合并部署后不再涉及跨域，但保留以支持开发环境分离调试
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. 先注册 API 路由
app.include_router(routes.router, prefix="/api/v1")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# 2. 挂载静态文件 (前端)
# 获取项目根目录 (假设运行目录为 backend)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

if os.path.exists(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
else:
    print(f"Warning: Frontend directory not found at {FRONTEND_DIR}")
