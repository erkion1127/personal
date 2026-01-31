"""데이터 내보내기 서비스"""

import json
from datetime import datetime
from pathlib import Path
from sqlmodel import Session, select

from app.core.config import get_settings
from app.db.models.session_log import SessionLog, SessionStatus
from app.db.models.export_log import ExportLog


class ExportService:
    """데이터 내보내기 서비스"""

    def __init__(self, session: Session):
        self.session = session
        self.settings = get_settings()

    def export_sessions(self, start_date: str, end_date: str) -> ExportLog:
        """세션 데이터 내보내기"""
        # 내보내기 ID 생성
        now = datetime.now()
        export_id = f"exp-{now.strftime('%Y%m%d-%H%M%S')}"

        # 세션 데이터 조회
        query = (
            select(SessionLog)
            .where(SessionLog.session_date >= start_date)
            .where(SessionLog.session_date <= end_date)
            .order_by(SessionLog.session_date, SessionLog.session_time)
        )
        sessions = self.session.exec(query).all()

        # 통계 계산
        completed = sum(1 for s in sessions if s.session_status == SessionStatus.COMPLETED)
        cancelled = sum(1 for s in sessions if s.session_status == SessionStatus.CANCELLED)
        no_show = sum(1 for s in sessions if s.session_status == SessionStatus.NO_SHOW)

        # JSON 데이터 구성
        export_data = {
            "export_info": {
                "export_id": export_id,
                "center_name": self.settings.center_name,
                "center_code": self.settings.center_code,
                "export_date": now.strftime("%Y-%m-%d"),
                "export_time": now.strftime("%H:%M:%S"),
                "period": {
                    "start_date": start_date,
                    "end_date": end_date,
                },
                "version": "1.0.0",
            },
            "statistics": {
                "total_sessions": len(sessions),
                "completed": completed,
                "cancelled": cancelled,
                "no_show": no_show,
            },
            "sessions": [
                {
                    "id": s.id,
                    "session_date": s.session_date,
                    "session_time": s.session_time,
                    "trainer_name": s.trainer_name,
                    "member_name": s.member_name,
                    "member_key": s.member_key,
                    "session_type": s.session_type,
                    "session_status": s.session_status.value,
                    "session_index": s.session_index,
                    "is_event": s.is_event,
                    "registration_type": s.registration_type,
                    "note": s.note,
                    "created_at": s.created_at.isoformat() if s.created_at else None,
                }
                for s in sessions
            ],
        }

        # 파일 저장
        exports_dir = self.settings.exports_dir
        exports_dir.mkdir(parents=True, exist_ok=True)

        file_name = f"export_{now.strftime('%Y%m%d_%H%M%S')}.json"
        file_path = exports_dir / file_name

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)

        file_size = file_path.stat().st_size

        # 세션 exported 플래그 업데이트
        for s in sessions:
            s.exported = True
            s.export_id = export_id
            self.session.add(s)

        # 내보내기 로그 저장
        export_log = ExportLog(
            export_id=export_id,
            export_date=now.strftime("%Y-%m-%d"),
            start_date=start_date,
            end_date=end_date,
            session_count=len(sessions),
            file_path=str(file_path),
            file_size_bytes=file_size,
            status="completed",
        )
        self.session.add(export_log)
        self.session.commit()
        self.session.refresh(export_log)

        return export_log
