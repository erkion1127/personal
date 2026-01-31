"""데이터 내보내기 API"""

from datetime import datetime, date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlmodel import Session, select

from app.db.session import get_session
from app.db.models.session_log import SessionLog
from app.db.models.export_log import ExportLog
from app.services.export_service import ExportService

router = APIRouter()


class ExportRequest(BaseModel):
    """내보내기 요청"""
    start_date: str
    end_date: str


class ExportResponse(BaseModel):
    """내보내기 응답"""
    export_id: str
    file_path: str
    session_count: int
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("")
async def list_exports(
    limit: int = Query(20, le=100),
    session: Session = Depends(get_session),
):
    """내보내기 이력 조회"""
    query = (
        select(ExportLog)
        .order_by(ExportLog.created_at.desc())
        .limit(limit)
    )
    results = session.exec(query).all()
    return {"exports": results}


@router.get("/pending")
async def get_pending_count(
    session: Session = Depends(get_session),
):
    """미내보내기 건수 조회"""
    query = select(SessionLog).where(SessionLog.exported == False)
    results = session.exec(query).all()
    return {
        "pending_count": len(results),
        "message": f"{len(results)}건의 미내보내기 데이터가 있습니다.",
    }


@router.post("", response_model=ExportResponse)
async def create_export(
    data: ExportRequest,
    session: Session = Depends(get_session),
):
    """데이터 내보내기 실행"""
    try:
        service = ExportService(session)
        result = service.export_sessions(data.start_date, data.end_date)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.get("/{export_id}/download")
async def download_export(
    export_id: str,
    session: Session = Depends(get_session),
):
    """내보내기 파일 다운로드"""
    query = select(ExportLog).where(ExportLog.export_id == export_id)
    export_log = session.exec(query).first()

    if not export_log:
        raise HTTPException(status_code=404, detail="Export not found")

    from pathlib import Path
    file_path = Path(export_log.file_path)

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=file_path,
        filename=file_path.name,
        media_type="application/json",
    )
