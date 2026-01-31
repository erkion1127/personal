"""수강권 캐시 모델"""

from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel


class LessonTicketCache(SQLModel, table=True):
    """수강권 캐시 테이블 (CRM 데이터)"""
    __tablename__ = "lesson_ticket_cache"

    id: Optional[int] = Field(default=None, primary_key=True)

    # CRM 키
    jglesson_ticket_key: int = Field(unique=True, index=True)
    jgjm_key: int = Field(index=True)  # 회원 키

    # 회원 정보
    member_name: str
    member_phone: Optional[str] = None

    # 수강권 정보
    ticket_type: str  # PT 20회, OT 등
    total_count: int
    remaining_count: int

    # 담당 트레이너
    trainer_key: Optional[int] = None
    trainer_name: Optional[str] = None

    # 기간
    start_date: Optional[str] = None
    end_date: Optional[str] = None

    # 상태
    status: Optional[str] = None  # 활성, 만료 등

    # 동기화
    synced_at: datetime = Field(default_factory=datetime.now)
