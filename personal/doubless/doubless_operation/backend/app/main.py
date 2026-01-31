"""
Doubless Operation - 센터 운영 시스템
업무일지 작성 및 데이터 추출
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.api.v1.router import api_router
from app.db.session import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 라이프사이클 관리"""
    # 시작 시 DB 초기화
    init_db()
    yield
    # 종료 시 정리 작업


app = FastAPI(
    title="Doubless Operation API",
    description="센터 운영 시스템 - 업무일지 및 데이터 관리",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 라우터 등록
app.include_router(api_router, prefix="/api/v1")

# 정적 파일 서빙 (프론트엔드 빌드)
static_path = Path(__file__).parent.parent / "static"
if static_path.exists():
    app.mount("/", StaticFiles(directory=static_path, html=True), name="static")


@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {"status": "healthy", "service": "doubless-operation"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
