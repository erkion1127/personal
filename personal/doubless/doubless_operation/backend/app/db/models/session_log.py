"""업무일지 (수업 기록) 모델"""

from datetime import datetime
from enum import Enum
from typing import Optional
from sqlmodel import Field, SQLModel


class SessionStatus(str, Enum):
    """세션 상태"""
    COMPLETED = "completed"     # 진행완료
    CANCELLED = "cancelled"     # 취소
    NO_SHOW = "no_show"         # 노쇼
    PAYMENT = "payment"         # 결제건 (수업 미진행)


class SessionLog(SQLModel, table=True):
    """업무일지 테이블"""
    __tablename__ = "session_logs"

    id: Optional[int] = Field(default=None, primary_key=True)

    # 기본 정보
    session_date: str = Field(index=True)           # YYYY-MM-DD
    session_time: str                                # HH:MM
    trainer_name: str = Field(index=True)            # 트레이너명
    member_name: str                                 # 회원명
    member_key: Optional[int] = None                 # CRM jgjm_key (선택)

    # 세션 정보
    session_type: str = Field(default="PT")          # PT, OT, 기타
    session_status: SessionStatus = Field(default=SessionStatus.COMPLETED)
    session_index: Optional[str] = None              # "15/20" 형태

    # 급여 관련
    is_event: bool = Field(default=False)            # 이벤트권 여부
    registration_type: Optional[str] = None          # new, renewal

    # 메모
    note: Optional[str] = None

    # 시스템
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None

    # 내보내기 추적
    exported: bool = Field(default=False)
    export_id: Optional[str] = None
