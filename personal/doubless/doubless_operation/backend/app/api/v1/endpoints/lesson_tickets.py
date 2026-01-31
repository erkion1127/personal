"""수강권 API"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlmodel import Session, select, delete

from app.db.session import get_session
from app.db.models.lesson_ticket_cache import LessonTicketCache
from app.services.broj_client import BrojClient

router = APIRouter()


class LessonTicketResponse(BaseModel):
    """수강권 응답"""
    id: int
    jglesson_ticket_key: int
    jgjm_key: int
    member_name: str
    member_phone: Optional[str]
    ticket_type: str
    total_count: int
    remaining_count: int
    trainer_name: Optional[str]
    start_date: Optional[str]
    end_date: Optional[str]
    status: Optional[str]
    synced_at: datetime

    class Config:
        from_attributes = True


def ms_to_date(ms: Optional[int]) -> Optional[str]:
    """밀리초 타임스탬프를 날짜 문자열로 변환"""
    if ms is None:
        return None
    try:
        return datetime.fromtimestamp(ms / 1000).strftime("%Y-%m-%d")
    except (ValueError, TypeError, OSError):
        return None


@router.get("", response_model=list[LessonTicketResponse])
async def list_lesson_tickets(
    trainer: Optional[str] = Query(None, description="트레이너 필터"),
    limit: int = Query(100, le=1000),
    offset: int = Query(0),
    session: Session = Depends(get_session),
):
    """수강권 목록 조회"""
    query = select(LessonTicketCache).offset(offset).limit(limit)

    if trainer:
        query = query.where(LessonTicketCache.trainer_name == trainer)

    # 잔여 횟수가 있는 것만 (선택)
    query = query.where(LessonTicketCache.remaining_count > 0)
    query = query.order_by(LessonTicketCache.member_name)

    results = session.exec(query).all()
    return results


@router.get("/search")
async def search_lesson_tickets(
    q: str = Query(..., min_length=1, description="회원명 검색"),
    limit: int = Query(20, le=100),
    session: Session = Depends(get_session),
):
    """수강권 검색 (회원명 기준)"""
    query = (
        select(LessonTicketCache)
        .where(LessonTicketCache.member_name.contains(q))
        .where(LessonTicketCache.remaining_count > 0)
        .limit(limit)
    )
    results = session.exec(query).all()

    return {
        "query": q,
        "count": len(results),
        "tickets": [
            {
                "jglesson_ticket_key": t.jglesson_ticket_key,
                "jgjm_key": t.jgjm_key,
                "member_name": t.member_name,
                "ticket_type": t.ticket_type,
                "remaining_count": t.remaining_count,
                "total_count": t.total_count,
                "trainer_name": t.trainer_name,
            }
            for t in results
        ],
    }


@router.get("/by-member/{jgjm_key}")
async def get_member_lesson_tickets(
    jgjm_key: int,
    session: Session = Depends(get_session),
):
    """특정 회원의 수강권 조회"""
    query = (
        select(LessonTicketCache)
        .where(LessonTicketCache.jgjm_key == jgjm_key)
        .order_by(LessonTicketCache.remaining_count.desc())
    )
    results = session.exec(query).all()
    return results


@router.post("/sync")
async def sync_lesson_tickets(
    session: Session = Depends(get_session),
):
    """CRM에서 수강권 동기화"""
    try:
        client = BrojClient()
        await client.login()
        tickets_data = await client.fetch_lesson_tickets()

        # 기존 데이터 삭제
        session.exec(delete(LessonTicketCache))

        count = 0
        for ticket in tickets_data:
            cache = LessonTicketCache(
                jglesson_ticket_key=ticket.get("jglesson_ticket_key"),
                jgjm_key=ticket.get("jgjm_key"),
                member_name=ticket.get("jgjm_member_name", ""),
                member_phone=ticket.get("jgjm_member_phone_number"),
                ticket_type=ticket.get("jglesson_ticket_type", ""),
                total_count=ticket.get("jglesson_ticket_origin_count", 0) or ticket.get("jglesson_origin_ticket_count", 0) or 0,
                remaining_count=ticket.get("jglesson_ticket_count", 0) or 0,
                trainer_key=ticket.get("jgjm_trainer_key"),
                trainer_name=ticket.get("trainer_name"),
                start_date=ms_to_date(ticket.get("jglesson_ticket_started_dttm")),
                end_date=ms_to_date(ticket.get("jglesson_ticket_closed_dttm")),
                status=ticket.get("status"),
                synced_at=datetime.now(),
            )
            session.add(cache)
            count += 1

        session.commit()

        return {
            "success": True,
            "message": f"Synced {count} lesson tickets",
            "count": count,
            "synced_at": datetime.now().isoformat(),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


@router.get("/stats")
async def get_lesson_ticket_stats(
    session: Session = Depends(get_session),
):
    """수강권 통계"""
    query = select(LessonTicketCache)
    results = session.exec(query).all()

    active = sum(1 for t in results if t.remaining_count > 0)

    return {
        "total": len(results),
        "active": active,
        "synced_at": results[0].synced_at.isoformat() if results else None,
    }
