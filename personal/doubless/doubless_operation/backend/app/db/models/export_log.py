"""내보내기 이력 모델"""

from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel


class ExportLog(SQLModel, table=True):
    """내보내기 이력 테이블"""
    __tablename__ = "export_logs"

    id: Optional[int] = Field(default=None, primary_key=True)

    # 내보내기 식별
    export_id: str = Field(unique=True, index=True)  # exp-YYYYMMDD-HHMMSS

    # 기간
    export_date: str                                  # YYYY-MM-DD
    start_date: str                                   # 시작일
    end_date: str                                     # 종료일

    # 통계
    session_count: int = 0

    # 파일 정보
    file_path: str
    file_size_bytes: int = 0

    # 상태
    status: str = "completed"                         # completed, failed
    error_message: Optional[str] = None

    # 시스템
    created_at: datetime = Field(default_factory=datetime.now)
