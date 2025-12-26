#!/usr/bin/env python3
"""
새로운 DB 구조 생성

JSON 데이터 구조에 맞춘 새로운 테이블 설계
"""

import sqlite3
from pathlib import Path
from datetime import datetime

def create_new_database(db_path):
    """새로운 DB 구조 생성"""

    # 기존 DB 백업
    backup_path = db_path.parent / f"members_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"

    if db_path.exists():
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"✅ 기존 DB 백업: {backup_path.name}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("\n🔨 새로운 테이블 생성 중...")

    # 1. 회원 테이블 (members)
    cursor.execute("DROP TABLE IF EXISTS members")
    cursor.execute("""
        CREATE TABLE members (
            jgjm_key INTEGER PRIMARY KEY,
            jgjm_member_name TEXT,
            jgjm_member_phone_number TEXT,
            jgjm_member_sex TEXT,
            jgjm_member_birth_dttm INTEGER,
            jgjm_address TEXT,
            jgjm_attendance_number TEXT,
            jgjm_remarks TEXT,
            jgjm_send_sms BOOLEAN,

            classification TEXT,
            customer_status TEXT,
            exercise_purpose TEXT,
            visit_route TEXT,
            is_subscriber BOOLEAN,

            created_dttm INTEGER,
            first_ticket_purchase_dttm INTEGER,
            last_ticket_purchase_dttm INTEGER,
            last_attendance INTEGER,

            ticket_start INTEGER,
            ticket_end INTEGER,
            left_days INTEGER,

            sync_id TEXT,
            synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("   ✅ members 테이블 생성")

    # 2. 회원권 테이블 (tickets)
    cursor.execute("DROP TABLE IF EXISTS tickets")
    cursor.execute("""
        CREATE TABLE tickets (
            jtd_key INTEGER PRIMARY KEY,
            jtd_name TEXT,
            jtd_memo TEXT,
            jtd_started_dttm INTEGER,
            jtd_closed_dttm INTEGER,
            created INTEGER,

            jgjm_key INTEGER,
            jgjm_member_name TEXT,
            jgjm_member_phone_number TEXT,
            jgjm_member_sex TEXT,
            jgjm_address TEXT,

            ticket_status TEXT,
            ticket_type TEXT,
            classification TEXT,

            jgp_history_price INTEGER,

            type INTEGER,
            transferable BOOLEAN,
            transferableCount INTEGER,
            has_holding_limits BOOLEAN,
            count_holding_limits INTEGER,
            days_holding_limits INTEGER,

            pass_origin_count INTEGER,
            pass_count INTEGER,
            remaining_minutes INTEGER,
            remaining_origin_minutes INTEGER,

            sync_id TEXT,
            synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (jgjm_key) REFERENCES members(jgjm_key)
        )
    """)
    print("   ✅ tickets 테이블 생성")

    # 3. 수강권 테이블 (lesson_tickets)
    cursor.execute("DROP TABLE IF EXISTS lesson_tickets")
    cursor.execute("""
        CREATE TABLE lesson_tickets (
            jglesson_ticket_key INTEGER PRIMARY KEY,
            jglesson_ticket_type TEXT,
            jglesson_ticket_count INTEGER,
            jglesson_origin_ticket_count INTEGER,
            jglesson_ticket_origin_count INTEGER,
            jglesson_ticket_point REAL,
            jglesson_origin_ticket_point REAL,
            jglesson_ticket_origin_point REAL,

            jglesson_ticket_started_dttm INTEGER,
            jglesson_ticket_closed_dttm INTEGER,
            last_lesson_dttm INTEGER,

            jgjm_key INTEGER,
            jgjm_member_name TEXT,
            jgjm_member_phone_number TEXT,
            jgjm_member_sex TEXT,
            jgjm_preview_type TEXT,

            jgjm_trainer_key INTEGER,
            trainer_key INTEGER,

            kind TEXT,
            attendance_type TEXT,
            status TEXT,

            real_used_lesson_count INTEGER,
            real_unused_lesson_count INTEGER,

            sync_id TEXT,
            synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (jgjm_key) REFERENCES members(jgjm_key)
        )
    """)
    print("   ✅ lesson_tickets 테이블 생성")

    # 4. 동기화 이력 테이블 (sync_history)
    cursor.execute("DROP TABLE IF EXISTS sync_history")
    cursor.execute("""
        CREATE TABLE sync_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sync_id TEXT UNIQUE NOT NULL,
            sync_time TIMESTAMP,
            members_count INTEGER,
            tickets_count INTEGER,
            lesson_tickets_count INTEGER,
            success BOOLEAN,
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("   ✅ sync_history 테이블 생성")

    # 인덱스 생성
    print("\n📊 인덱스 생성 중...")

    cursor.execute("CREATE INDEX idx_members_name ON members(jgjm_member_name)")
    cursor.execute("CREATE INDEX idx_members_phone ON members(jgjm_member_phone_number)")
    cursor.execute("CREATE INDEX idx_members_status ON members(customer_status)")
    cursor.execute("CREATE INDEX idx_members_sync ON members(sync_id)")

    cursor.execute("CREATE INDEX idx_tickets_member ON tickets(jgjm_key)")
    cursor.execute("CREATE INDEX idx_tickets_status ON tickets(ticket_status)")
    cursor.execute("CREATE INDEX idx_tickets_sync ON tickets(sync_id)")

    cursor.execute("CREATE INDEX idx_lesson_member ON lesson_tickets(jgjm_key)")
    cursor.execute("CREATE INDEX idx_lesson_trainer ON lesson_tickets(jgjm_trainer_key)")
    cursor.execute("CREATE INDEX idx_lesson_sync ON lesson_tickets(sync_id)")

    print("   ✅ 인덱스 생성 완료")

    conn.commit()
    conn.close()

    print(f"\n✅ 새로운 DB 구조 생성 완료: {db_path}")
    return True


def main():
    """메인 함수"""
    print("="*80)
    print("새로운 DB 구조 생성")
    print("="*80)

    base_dir = Path(__file__).parent.parent
    db_path = base_dir / "data" / "members.db"

    print(f"\n⚠️  주의: 기존 테이블이 모두 삭제되고 새로 생성됩니다.")
    print(f"DB 경로: {db_path}")

    response = input("\n계속하시겠습니까? (yes/no): ")

    if response.lower() != 'yes':
        print("\n❌ 취소되었습니다.")
        return

    if create_new_database(db_path):
        print("\n" + "="*80)
        print("완료")
        print("="*80)
        print("\n다음 단계:")
        print("1. sync_to_db.py를 실행하여 데이터 동기화")
        print("2. 기존 분석 프로그램 테이블명 확인 및 수정")


if __name__ == "__main__":
    main()
