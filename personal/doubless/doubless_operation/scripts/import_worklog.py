#!/usr/bin/env python3
"""업무일지 엑셀 임포트 스크립트

사용법:
    python scripts/import_worklog.py <엑셀파일경로>

예시:
    python scripts/import_worklog.py "/Users/valkyrion/Downloads/26년1월 트레이너 업무일지_20260131.xlsx"
"""

import sys
from pathlib import Path
from datetime import datetime
import re

# backend 모듈 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import pandas as pd
from sqlmodel import Session
from app.db.session import engine
from app.db.models.session_log import SessionLog


def parse_session_index(text: str) -> tuple[str, str, bool]:
    """
    세션 표기 파싱

    Returns:
        (session_type, session_index, is_event)
    """
    if pd.isna(text) or not str(text).strip():
        return "PT", None, False

    text = str(text).strip()

    # OT 체크
    if text.upper().startswith("OT"):
        ot_num = re.search(r'\d+', text)
        return "OT", f"OT{ot_num.group()}" if ot_num else "OT", False

    # 상담/체험
    if text in ["상담", "체험"]:
        return text, None, False

    # 이벤트 체크 (+E 또는 이벤트)
    is_event = "+E" in text or "이벤트" in text

    # PT 회차 파싱 (예: 5/20, 12/30)
    match = re.search(r'(\d+)/(\d+)', text)
    if match:
        return "PT", f"{match.group(1)}/{match.group(2)}", is_event

    return "PT", None, is_event


def import_worklog(excel_path: str, year: int = 2026, month: int = 1):
    """엑셀 업무일지를 DB에 임포트"""

    print("=" * 60)
    print(f"업무일지 임포트: {excel_path}")
    print("=" * 60)

    xl = pd.ExcelFile(excel_path)

    # 일자 시트만 필터링 (1~31)
    day_sheets = [s for s in xl.sheet_names if s.isdigit()]
    print(f"\n처리할 시트: {len(day_sheets)}개 (일자: {day_sheets})")

    all_sessions = []

    for sheet_name in day_sheets:
        day = int(sheet_name)
        try:
            session_date = f"{year}-{month:02d}-{day:02d}"
        except:
            continue

        df = pd.read_excel(excel_path, sheet_name=sheet_name, header=None)

        # 헤더 행 찾기 (TR이 있는 행)
        header_row = None
        for i in range(min(10, len(df))):
            row_values = [str(x).strip() if pd.notna(x) else '' for x in df.iloc[i]]
            if 'TR' in row_values:
                header_row = i
                break

        if header_row is None:
            print(f"  {sheet_name}일: 헤더를 찾을 수 없음, 건너뜀")
            continue

        # 시간대 컬럼 매핑 (06:00 ~ 23:00)
        time_cols = {}
        header = df.iloc[header_row]
        for col_idx, val in enumerate(header):
            if pd.notna(val):
                val_str = str(val)
                # 시간 형식 파싱 (06:00:00 또는 06:00)
                time_match = re.match(r'(\d{1,2}):(\d{2})', val_str)
                if time_match:
                    hour = int(time_match.group(1))
                    time_str = f"{hour:02d}:00"
                    time_cols[col_idx] = time_str

        # TR 컬럼 인덱스 찾기
        tr_col = None
        for col_idx, val in enumerate(header):
            if pd.notna(val) and str(val).strip() == 'TR':
                tr_col = col_idx
                break

        if tr_col is None:
            print(f"  {sheet_name}일: TR 컬럼을 찾을 수 없음, 건너뜀")
            continue

        # 트레이너별 데이터 파싱 (헤더 다음 행부터)
        day_sessions = []
        i = header_row + 1

        while i < len(df):
            row = df.iloc[i]
            trainer_name = row.iloc[tr_col] if pd.notna(row.iloc[tr_col]) else None

            if trainer_name and str(trainer_name).strip():
                trainer_name = str(trainer_name).strip()

                # 다음 행에서 회차 정보 가져오기
                next_row = df.iloc[i + 1] if i + 1 < len(df) else None

                # 각 시간대별 수업 파싱
                for col_idx, time_str in time_cols.items():
                    member_name = row.iloc[col_idx] if col_idx < len(row) and pd.notna(row.iloc[col_idx]) else None

                    if member_name and str(member_name).strip():
                        member_name = str(member_name).strip()

                        # 특수 케이스 제외 (회의/식사 등)
                        if member_name in ['회의/식사', '회의', '식사', '휴식', '']:
                            continue

                        # 회차 정보 파싱
                        session_info = None
                        if next_row is not None and col_idx < len(next_row):
                            session_info = next_row.iloc[col_idx]

                        session_type, session_index, is_event = parse_session_index(session_info)

                        session = SessionLog(
                            session_date=session_date,
                            session_time=time_str,
                            trainer_name=trainer_name,
                            member_name=member_name,
                            session_type=session_type,
                            session_status="completed",
                            session_index=session_index,
                            is_event=is_event,
                            note=f"엑셀 임포트 ({sheet_name}일)",
                        )
                        day_sessions.append(session)

                i += 2  # 트레이너당 2행씩 건너뜀
            else:
                i += 1

        if day_sessions:
            print(f"  {session_date}: {len(day_sessions)}건")
            all_sessions.extend(day_sessions)

    # DB에 저장
    print(f"\n총 {len(all_sessions)}건 저장 중...")

    with Session(engine) as session:
        for log in all_sessions:
            session.add(log)
        session.commit()

    print("\n" + "=" * 60)
    print(f"임포트 완료! 총 {len(all_sessions)}건")
    print("=" * 60)

    return len(all_sessions)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용법: python import_worklog.py <엑셀파일경로>")
        sys.exit(1)

    excel_path = sys.argv[1]

    if not Path(excel_path).exists():
        print(f"파일을 찾을 수 없습니다: {excel_path}")
        sys.exit(1)

    count = import_worklog(excel_path)
    sys.exit(0 if count > 0 else 1)
