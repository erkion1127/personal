#!/usr/bin/env python3
"""회원 동기화 CLI 스크립트

사용법:
    python scripts/sync_members.py
"""

import asyncio
import sys
from pathlib import Path

# backend 모듈 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from datetime import datetime
from sqlmodel import Session, delete
from app.db.session import engine
from app.db.models.member_cache import MemberCache
from app.services.broj_client import BrojClient


async def sync_members():
    """CRM에서 회원 데이터를 가져와 로컬 DB에 저장"""
    print("=" * 50)
    print("회원 동기화 시작")
    print("=" * 50)

    try:
        # CRM 로그인
        print("\n[1/3] CRM 로그인 중...")
        client = BrojClient()
        await client.login()
        print("      로그인 성공")

        # 회원 데이터 가져오기
        print("\n[2/3] 회원 데이터 가져오는 중...")
        members_data = await client.fetch_members()
        print(f"      {len(members_data)}명 조회됨")

        # DB에 저장
        print("\n[3/3] 로컬 DB에 저장 중...")
        with Session(engine) as session:
            # 기존 데이터 삭제
            session.exec(delete(MemberCache))
            session.commit()

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

        print(f"      {count}명 저장 완료")

        print("\n" + "=" * 50)
        print(f"동기화 완료! 총 {count}명")
        print("=" * 50)

        return count

    except Exception as e:
        print(f"\n오류 발생: {e}")
        return 0


if __name__ == "__main__":
    count = asyncio.run(sync_members())
    sys.exit(0 if count > 0 else 1)
