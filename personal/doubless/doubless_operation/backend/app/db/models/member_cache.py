"""회원 캐시 모델 (CRM 데이터 로컬 저장)"""

from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel


class MemberCache(SQLModel, table=True):
    """회원 캐시 테이블"""
    __tablename__ = "member_cache"

    id: Optional[int] = Field(default=None, primary_key=True)

    # CRM 키
    jgjm_key: int = Field(unique=True, index=True)

    # 기본 정보
    name: str = Field(index=True)
    phone: Optional[str] = None
    gender: Optional[str] = None                    # M, F

    # 이용권 현황
    trainer_name: Optional[str] = None              # 담당 트레이너
    pt_remaining: Optional[int] = None              # 잔여 PT 횟수
    pt_total: Optional[int] = None                  # 총 PT 횟수
    membership_end: Optional[str] = None            # 회원권 종료일

    # 분류
    classification: Optional[str] = None            # 회원 분류
    customer_status: Optional[str] = None           # 회원 상태

    # 동기화
    synced_at: datetime = Field(default_factory=datetime.now)
