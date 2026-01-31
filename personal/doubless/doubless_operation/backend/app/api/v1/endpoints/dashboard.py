"""대시보드 API"""

from datetime import date
from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.db.session import get_session
from app.db.models.session_log import SessionLog, SessionStatus
from app.db.models.member_cache import MemberCache

router = APIRouter()


@router.get("/today")
async def get_today_dashboard(
    session: Session = Depends(get_session),
):
    """오늘 대시보드 데이터"""
    today = date.today().isoformat()

    # 오늘 세션
    session_query = select(SessionLog).where(SessionLog.session_date == today)
    sessions = session.exec(session_query).all()

    completed = sum(1 for s in sessions if s.session_status == SessionStatus.COMPLETED)
    cancelled = sum(1 for s in sessions if s.session_status == SessionStatus.CANCELLED)
    no_show = sum(1 for s in sessions if s.session_status == SessionStatus.NO_SHOW)

    # 미내보내기 건수
    pending_query = select(SessionLog).where(SessionLog.exported == False)
    pending = session.exec(pending_query).all()

    # 회원 수
    member_query = select(MemberCache)
    members = session.exec(member_query).all()

    return {
        "date": today,
        "sessions": {
            "total": len(sessions),
            "completed": completed,
            "cancelled": cancelled,
            "no_show": no_show,
        },
        "pending_export": len(pending),
        "members_cached": len(members),
        "recent_sessions": [
            {
                "id": s.id,
                "time": s.session_time,
                "trainer": s.trainer_name,
                "member": s.member_name,
                "status": s.session_status.value,
            }
            for s in sorted(sessions, key=lambda x: x.session_time)[:10]
        ],
    }
