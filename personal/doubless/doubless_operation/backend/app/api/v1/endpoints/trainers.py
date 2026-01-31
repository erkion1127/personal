"""트레이너/직원 API"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from app.db.session import get_session
from app.db.models.trainer import Trainer, Staff, StaffStatus

router = APIRouter()


# Request/Response 스키마
class TrainerCreate(BaseModel):
    name: str
    phone: Optional[str] = None


class TrainerUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    status: Optional[StaffStatus] = None


class TrainerResponse(BaseModel):
    id: int
    name: str
    phone: Optional[str]
    status: StaffStatus
    created_at: datetime

    class Config:
        from_attributes = True


class StaffCreate(BaseModel):
    name: str
    role: str = "인포"
    phone: Optional[str] = None


class StaffUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    phone: Optional[str] = None
    status: Optional[StaffStatus] = None


class StaffResponse(BaseModel):
    id: int
    name: str
    role: str
    phone: Optional[str]
    status: StaffStatus
    created_at: datetime

    class Config:
        from_attributes = True


# 트레이너 API
@router.get("/trainers", response_model=list[TrainerResponse])
async def list_trainers(
    status: Optional[StaffStatus] = None,
    session: Session = Depends(get_session),
):
    """트레이너 목록 조회"""
    query = select(Trainer).order_by(Trainer.name)
    if status:
        query = query.where(Trainer.status == status)
    results = session.exec(query).all()
    return results


@router.post("/trainers", response_model=TrainerResponse)
async def create_trainer(
    data: TrainerCreate,
    session: Session = Depends(get_session),
):
    """트레이너 추가"""
    # 중복 체크
    existing = session.exec(
        select(Trainer).where(Trainer.name == data.name)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Trainer already exists")

    trainer = Trainer(**data.model_dump())
    session.add(trainer)
    session.commit()
    session.refresh(trainer)
    return trainer


@router.put("/trainers/{trainer_id}", response_model=TrainerResponse)
async def update_trainer(
    trainer_id: int,
    data: TrainerUpdate,
    session: Session = Depends(get_session),
):
    """트레이너 수정"""
    trainer = session.get(Trainer, trainer_id)
    if not trainer:
        raise HTTPException(status_code=404, detail="Trainer not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(trainer, key, value)

    session.add(trainer)
    session.commit()
    session.refresh(trainer)
    return trainer


@router.delete("/trainers/{trainer_id}")
async def delete_trainer(
    trainer_id: int,
    session: Session = Depends(get_session),
):
    """트레이너 삭제 (비활성화)"""
    trainer = session.get(Trainer, trainer_id)
    if not trainer:
        raise HTTPException(status_code=404, detail="Trainer not found")

    trainer.status = StaffStatus.INACTIVE
    session.add(trainer)
    session.commit()
    return {"message": "Trainer deactivated"}


# 직원 API
@router.get("/staff", response_model=list[StaffResponse])
async def list_staff(
    status: Optional[StaffStatus] = None,
    session: Session = Depends(get_session),
):
    """직원 목록 조회"""
    query = select(Staff).order_by(Staff.name)
    if status:
        query = query.where(Staff.status == status)
    results = session.exec(query).all()
    return results


@router.post("/staff", response_model=StaffResponse)
async def create_staff(
    data: StaffCreate,
    session: Session = Depends(get_session),
):
    """직원 추가"""
    staff = Staff(**data.model_dump())
    session.add(staff)
    session.commit()
    session.refresh(staff)
    return staff


@router.put("/staff/{staff_id}", response_model=StaffResponse)
async def update_staff(
    staff_id: int,
    data: StaffUpdate,
    session: Session = Depends(get_session),
):
    """직원 수정"""
    staff = session.get(Staff, staff_id)
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(staff, key, value)

    session.add(staff)
    session.commit()
    session.refresh(staff)
    return staff


@router.delete("/staff/{staff_id}")
async def delete_staff(
    staff_id: int,
    session: Session = Depends(get_session),
):
    """직원 삭제 (비활성화)"""
    staff = session.get(Staff, staff_id)
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")

    staff.status = StaffStatus.INACTIVE
    session.add(staff)
    session.commit()
    return {"message": "Staff deactivated"}
