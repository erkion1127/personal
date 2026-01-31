"""트레이너/직원 모델"""

from datetime import datetime
from enum import Enum
from typing import Optional
from sqlmodel import Field, SQLModel


class StaffStatus(str, Enum):
    """직원 상태"""
    ACTIVE = "active"
    INACTIVE = "inactive"


class Trainer(SQLModel, table=True):
    """트레이너 테이블"""
    __tablename__ = "trainers"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    phone: Optional[str] = None
    status: StaffStatus = Field(default=StaffStatus.ACTIVE)
    created_at: datetime = Field(default_factory=datetime.now)


class Staff(SQLModel, table=True):
    """직원 테이블"""
    __tablename__ = "staff"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    role: str = Field(default="인포")  # 인포, 매니저 등
    phone: Optional[str] = None
    status: StaffStatus = Field(default=StaffStatus.ACTIVE)
    created_at: datetime = Field(default_factory=datetime.now)
