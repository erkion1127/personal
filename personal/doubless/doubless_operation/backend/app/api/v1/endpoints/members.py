"""회원 API"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlmodel import Session, select

from app.db.session import get_session
from app.db.models.member_cache import MemberCache
from app.services.broj_client import BrojClient

router = APIRouter()


class MemberResponse(BaseModel):
    """회원 응답"""
    id: int
    jgjm_key: int
    name: str
    phone: Optional[str]
    gender: Optional[str]
    trainer_name: Optional[str]
    pt_remaining: Optional[int]
    pt_total: Optional[int]
    membership_end: Optional[str]
    classification: Optional[str]
    customer_status: Optional[str]
    synced_at: datetime

    class Config:
        from_attributes = True


@router.get("", response_model=list[MemberResponse])
async def list_members(
    limit: int = Query(100, le=1000),
    offset: int = Query(0),
    session: Session = Depends(get_session),
):
    """회원 목록 조회 (캐시된 데이터)"""
    query = select(MemberCache).offset(offset).limit(limit)
    results = session.exec(query).all()
    return results


@router.get("/search")
async def search_members(
    q: str = Query(..., min_length=1, description="검색어 (이름 또는 전화번호)"),
    limit: int = Query(20, le=100),
    session: Session = Depends(get_session),
):
    """회원 검색 (자동완성용)"""
    query = (
        select(MemberCache)
        .where(
            (MemberCache.name.contains(q)) |
            (MemberCache.phone.contains(q))
        )
        .limit(limit)
    )
    results = session.exec(query).all()

    return {
        "query": q,
        "count": len(results),
        "members": [
            {
                "jgjm_key": m.jgjm_key,
                "name": m.name,
                "phone": m.phone,
                "trainer_name": m.trainer_name,
                "pt_remaining": m.pt_remaining,
            }
            for m in results
        ],
    }


@router.post("/sync")
async def sync_members(
    session: Session = Depends(get_session),
):
    """CRM에서 회원 동기화"""
    try:
        client = BrojClient()
        await client.login()
        members_data = await client.fetch_members()

        # 기존 데이터 삭제 후 새로 삽입
        session.exec(select(MemberCache)).all()
        # Delete all existing
        from sqlmodel import delete
        session.exec(delete(MemberCache))

        count = 0
        for member in members_data:
            cache = MemberCache(
                jgjm_key=member.get("jgjm_key"),
                name=member.get("jgjm_member_name", ""),
                phone=member.get("jgjm_member_phone_number"),
                gender=member.get("jgjm_member_sex"),
                classification=member.get("classification"),
                customer_status=member.get("customer_status"),
                synced_at=datetime.now(),
            )
            session.add(cache)
            count += 1

        session.commit()

        return {
            "success": True,
            "message": f"Synced {count} members",
            "count": count,
            "synced_at": datetime.now().isoformat(),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


@router.get("/stats")
async def get_member_stats(
    session: Session = Depends(get_session),
):
    """회원 통계"""
    query = select(MemberCache)
    results = session.exec(query).all()

    return {
        "total": len(results),
        "synced_at": results[0].synced_at.isoformat() if results else None,
    }
