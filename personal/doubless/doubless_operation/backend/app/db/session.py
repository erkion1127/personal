"""데이터베이스 세션 관리"""

from contextlib import contextmanager
from typing import Generator
from sqlmodel import Session, SQLModel, create_engine
from pathlib import Path

from app.core.config import get_settings

settings = get_settings()

# 데이터 디렉토리 생성
settings.data_dir.mkdir(parents=True, exist_ok=True)

# SQLite 엔진 생성
engine = create_engine(
    settings.database_url,
    echo=settings.debug,
    connect_args={"check_same_thread": False},
)


def init_db() -> None:
    """데이터베이스 초기화 (테이블 생성)"""
    # 모델 임포트 (테이블 생성을 위해)
    from app.db.models import session_log, member_cache, export_log  # noqa: F401

    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """FastAPI 의존성용 세션"""
    with Session(engine) as session:
        yield session


@contextmanager
def get_session_context() -> Generator[Session, None, None]:
    """컨텍스트 매니저용 세션"""
    session = Session(engine)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
