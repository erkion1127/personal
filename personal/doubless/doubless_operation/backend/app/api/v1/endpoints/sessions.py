"""업무일지 (세션) API"""

from datetime import datetime, date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlmodel import Session, select

from app.db.session import get_session
from app.db.models.session_log import SessionLog, SessionStatus

router = APIRouter()


# Request/Response 스키마
class SessionCreate(BaseModel):
    """세션 생성 요청"""
    session_date: str
    session_time: str
    trainer_name: str
    member_name: str
    member_key: Optional[int] = None
    session_type: str = "PT"
    session_status: SessionStatus = SessionStatus.COMPLETED
    session_index: Optional[str] = None
    is_event: bool = False
    registration_type: Optional[str] = None
    note: Optional[str] = None


class SessionUpdate(BaseModel):
    """세션 수정 요청"""
    session_date: Optional[str] = None
    session_time: Optional[str] = None
    trainer_name: Optional[str] = None
    member_name: Optional[str] = None
    member_key: Optional[int] = None
    session_type: Optional[str] = None
    session_status: Optional[SessionStatus] = None
    session_index: Optional[str] = None
    is_event: Optional[bool] = None
    registration_type: Optional[str] = None
    note: Optional[str] = None


class SessionResponse(BaseModel):
    """세션 응답"""
    id: int
    session_date: str
    session_time: str
    trainer_name: str
    member_name: str
    member_key: Optional[int]
    session_type: str
    session_status: SessionStatus
    session_index: Optional[str]
    is_event: bool
    registration_type: Optional[str]
    note: Optional[str]
    created_at: datetime
    exported: bool

    class Config:
        from_attributes = True


@router.get("", response_model=list[SessionResponse])
async def list_sessions(
    date: Optional[str] = Query(None, description="날짜 필터 (YYYY-MM-DD)"),
    trainer: Optional[str] = Query(None, description="트레이너 필터"),
    session: Session = Depends(get_session),
):
    """세션 목록 조회"""
    query = select(SessionLog).order_by(SessionLog.session_date.desc(), SessionLog.session_time)

    if date:
        query = query.where(SessionLog.session_date == date)
    if trainer:
        query = query.where(SessionLog.trainer_name == trainer)

    results = session.exec(query).all()
    return results


@router.get("/daily/{date}", response_model=list[SessionResponse])
async def get_daily_sessions(
    date: str,
    session: Session = Depends(get_session),
):
    """일별 세션 조회"""
    query = (
        select(SessionLog)
        .where(SessionLog.session_date == date)
        .order_by(SessionLog.session_time)
    )
    results = session.exec(query).all()
    return results


@router.get("/trainers")
async def get_trainers(
    session: Session = Depends(get_session),
):
    """트레이너 목록 조회"""
    query = select(SessionLog.trainer_name).distinct()
    results = session.exec(query).all()
    return {"trainers": sorted(set(results))}


@router.post("", response_model=SessionResponse)
async def create_session(
    data: SessionCreate,
    session: Session = Depends(get_session),
):
    """세션 생성"""
    log = SessionLog(**data.model_dump())
    session.add(log)
    session.commit()
    session.refresh(log)
    return log


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session_by_id(
    session_id: int,
    session: Session = Depends(get_session),
):
    """세션 상세 조회"""
    log = session.get(SessionLog, session_id)
    if not log:
        raise HTTPException(status_code=404, detail="Session not found")
    return log


@router.put("/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: int,
    data: SessionUpdate,
    session: Session = Depends(get_session),
):
    """세션 수정"""
    log = session.get(SessionLog, session_id)
    if not log:
        raise HTTPException(status_code=404, detail="Session not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(log, key, value)

    log.updated_at = datetime.now()
    session.add(log)
    session.commit()
    session.refresh(log)
    return log


@router.delete("/{session_id}")
async def delete_session(
    session_id: int,
    session: Session = Depends(get_session),
):
    """세션 삭제"""
    log = session.get(SessionLog, session_id)
    if not log:
        raise HTTPException(status_code=404, detail="Session not found")

    session.delete(log)
    session.commit()
    return {"message": "Session deleted"}


@router.get("/stats/today")
async def get_today_stats(
    session: Session = Depends(get_session),
):
    """오늘 통계"""
    today = date.today().isoformat()

    query = select(SessionLog).where(SessionLog.session_date == today)
    results = session.exec(query).all()

    completed = sum(1 for r in results if r.session_status == SessionStatus.COMPLETED)
    cancelled = sum(1 for r in results if r.session_status == SessionStatus.CANCELLED)
    no_show = sum(1 for r in results if r.session_status == SessionStatus.NO_SHOW)

    return {
        "date": today,
        "total": len(results),
        "completed": completed,
        "cancelled": cancelled,
        "no_show": no_show,
    }
