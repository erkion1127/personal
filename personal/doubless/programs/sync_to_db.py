#!/usr/bin/env python3
"""
Broj CRM 동기화 데이터를 SQLite DB로 업데이트

이 프로그램은 latest 폴더의 JSON 데이터를 읽어서 SQLite DB를 업데이트합니다.
새로운 테이블 구조에 맞춰 데이터를 동기화합니다.
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime
import sys

class BrojDBSync:
    """Broj CRM 데이터 DB 동기화"""

    def __init__(self, db_path, sync_dir):
        """초기화"""
        self.db_path = Path(db_path)
        self.sync_dir = Path(sync_dir)
        self.conn = None
        self.sync_info = None

    def connect(self):
        """DB 연결"""
        print(f"📂 DB 연결: {self.db_path}")
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        return self.conn

    def close(self):
        """DB 연결 종료"""
        if self.conn:
            self.conn.close()
            print("✅ DB 연결 종료")

    def load_sync_info(self):
        """동기화 정보 로드"""
        sync_info_file = self.sync_dir / "sync_info.json"

        if not sync_info_file.exists():
            print(f"❌ sync_info.json 파일을 찾을 수 없습니다: {sync_info_file}")
            return False

        with open(sync_info_file, 'r', encoding='utf-8') as f:
            self.sync_info = json.load(f)

        print(f"📋 동기화 정보 로드:")
        print(f"   - Sync ID: {self.sync_info['sync_id']}")
        print(f"   - Sync Time: {self.sync_info['sync_time_kr']}")

        return True

    def sync_members(self):
        """회원 정보 동기화"""
        print("\n" + "="*80)
        print("[ 1/3 ] 회원 정보 동기화")
        print("="*80)

        # JSON 파일 로드
        json_file = self.sync_dir / self.sync_info['files']['members']
        if not json_file.exists():
            print(f"❌ 파일을 찾을 수 없습니다: {json_file}")
            return False

        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        members = data['members']
        print(f"📥 {len(members)}명의 회원 데이터 로드")

        # 기존 데이터 삭제
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM members")
        print(f"   ✅ 기존 데이터 삭제")

        # 새 데이터 삽입
        print(f"\n💾 새 데이터 삽입:")
        insert_count = 0
        skip_count = 0

        sync_id = self.sync_info['sync_id']

        for member in members:
            try:
                cursor.execute("""
                    INSERT INTO members (
                        jgjm_key, jgjm_member_name, jgjm_member_phone_number,
                        jgjm_member_sex, jgjm_member_birth_dttm, jgjm_address,
                        jgjm_attendance_number, jgjm_remarks, jgjm_send_sms,
                        classification, customer_status, exercise_purpose,
                        visit_route, is_subscriber,
                        created_dttm, first_ticket_purchase_dttm,
                        last_ticket_purchase_dttm, last_attendance,
                        ticket_start, ticket_end, left_days,
                        sync_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    member.get('jgjm_key'),
                    member.get('jgjm_member_name'),
                    member.get('jgjm_member_phone_number'),
                    member.get('jgjm_member_sex'),
                    member.get('jgjm_member_birth_dttm'),
                    member.get('jgjm_address'),
                    member.get('jgjm_attendance_number'),
                    member.get('jgjm_remarks'),
                    member.get('jgjm_send_sms', False),
                    member.get('classification'),
                    member.get('customer_status'),
                    member.get('exercise_purpose'),
                    member.get('visit_route'),
                    member.get('is_subscriber', False),
                    member.get('created_dttm'),
                    member.get('first_ticket_purchase_dttm'),
                    member.get('last_ticket_purchase_dttm'),
                    member.get('last_attendance'),
                    member.get('ticket_start'),
                    member.get('ticket_end'),
                    member.get('left_days'),
                    sync_id
                ))
                insert_count += 1
            except sqlite3.Error as e:
                skip_count += 1
                if skip_count <= 3:  # 처음 3개만 출력
                    print(f"   ⚠️  삽입 실패: {e}")

        self.conn.commit()
        print(f"   ✅ {insert_count}명 삽입 완료 (스킵: {skip_count})")
        return True

    def sync_tickets(self):
        """회원권 정보 동기화"""
        print("\n" + "="*80)
        print("[ 2/3 ] 회원권 정보 동기화")
        print("="*80)

        # JSON 파일 로드
        json_file = self.sync_dir / self.sync_info['files']['tickets']
        if not json_file.exists():
            print(f"❌ 파일을 찾을 수 없습니다: {json_file}")
            return False

        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        tickets = data['tickets']
        print(f"📥 {len(tickets)}건의 회원권 데이터 로드")

        # 기존 데이터 삭제
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM tickets")
        print(f"   ✅ 기존 데이터 삭제")

        # 새 데이터 삽입
        print(f"\n💾 새 데이터 삽입:")
        insert_count = 0
        skip_count = 0

        sync_id = self.sync_info['sync_id']

        for ticket in tickets:
            try:
                # Customer 정보 추출
                customer = ticket.get('Customer', {}) if ticket.get('Customer') else {}

                cursor.execute("""
                    INSERT INTO tickets (
                        jtd_key, jtd_name, jtd_memo,
                        jtd_started_dttm, jtd_closed_dttm, created,
                        jgjm_key, jgjm_member_name, jgjm_member_phone_number,
                        jgjm_member_sex, jgjm_address,
                        ticket_status, ticket_type, classification,
                        jgp_history_price,
                        type, transferable, transferableCount,
                        has_holding_limits, count_holding_limits, days_holding_limits,
                        pass_origin_count, pass_count,
                        remaining_minutes, remaining_origin_minutes,
                        sync_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    ticket.get('jtd_key'),
                    ticket.get('jtd_name'),
                    ticket.get('jtd_memo'),
                    ticket.get('jtd_started_dttm'),
                    ticket.get('jtd_closed_dttm'),
                    ticket.get('created'),
                    ticket.get('jgjm_key') or customer.get('jgjm_key'),
                    ticket.get('jgjm_member_name') or customer.get('jgjm_member_name'),
                    ticket.get('jgjm_member_phone_number') or customer.get('jgjm_member_phone_number'),
                    ticket.get('jgjm_member_sex') or customer.get('jgjm_member_sex'),
                    ticket.get('jgjm_address') or customer.get('jgjm_address'),
                    ticket.get('ticket_status'),
                    ticket.get('ticket_type'),
                    ticket.get('classification'),
                    ticket.get('jgp_history_price'),
                    ticket.get('type'),
                    ticket.get('transferable', False),
                    ticket.get('transferableCount'),
                    ticket.get('has_holding_limits', False),
                    ticket.get('count_holding_limits'),
                    ticket.get('days_holding_limits'),
                    ticket.get('pass_origin_count'),
                    ticket.get('pass_count'),
                    ticket.get('remaining_minutes'),
                    ticket.get('remaining_origin_minutes'),
                    sync_id
                ))
                insert_count += 1
            except sqlite3.Error as e:
                skip_count += 1
                if skip_count <= 3:
                    print(f"   ⚠️  삽입 실패: {e}")

        self.conn.commit()
        print(f"   ✅ {insert_count}건 삽입 완료 (스킵: {skip_count})")
        return True

    def sync_lesson_tickets(self):
        """수강권 정보 동기화"""
        print("\n" + "="*80)
        print("[ 3/3 ] 수강권 정보 동기화")
        print("="*80)

        # JSON 파일 로드
        json_file = self.sync_dir / self.sync_info['files']['lesson_tickets']
        if not json_file.exists():
            print(f"❌ 파일을 찾을 수 없습니다: {json_file}")
            return False

        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        lesson_tickets = data['lesson_tickets']
        print(f"📥 {len(lesson_tickets)}건의 수강권 데이터 로드")

        # 기존 데이터 삭제
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM lesson_tickets")
        print(f"   ✅ 기존 데이터 삭제")

        # 새 데이터 삽입
        print(f"\n💾 새 데이터 삽입:")
        insert_count = 0
        skip_count = 0

        sync_id = self.sync_info['sync_id']

        for ticket in lesson_tickets:
            try:
                cursor.execute("""
                    INSERT INTO lesson_tickets (
                        jglesson_ticket_key, jglesson_ticket_type,
                        jglesson_ticket_count, jglesson_origin_ticket_count,
                        jglesson_ticket_origin_count,
                        jglesson_ticket_point, jglesson_origin_ticket_point,
                        jglesson_ticket_origin_point,
                        jglesson_ticket_started_dttm, jglesson_ticket_closed_dttm,
                        last_lesson_dttm,
                        jgjm_key, jgjm_member_name, jgjm_member_phone_number,
                        jgjm_member_sex, jgjm_preview_type,
                        jgjm_trainer_key, trainer_key,
                        kind, attendance_type, status,
                        real_used_lesson_count, real_unused_lesson_count,
                        sync_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    ticket.get('jglesson_ticket_key'),
                    ticket.get('jglesson_ticket_type'),
                    ticket.get('jglesson_ticket_count'),
                    ticket.get('jglesson_origin_ticket_count'),
                    ticket.get('jglesson_ticket_origin_count'),
                    ticket.get('jglesson_ticket_point'),
                    ticket.get('jglesson_origin_ticket_point'),
                    ticket.get('jglesson_ticket_origin_point'),
                    ticket.get('jglesson_ticket_started_dttm'),
                    ticket.get('jglesson_ticket_closed_dttm'),
                    ticket.get('last_lesson_dttm'),
                    ticket.get('jgjm_key'),
                    ticket.get('jgjm_member_name'),
                    ticket.get('jgjm_member_phone_number'),
                    ticket.get('jgjm_member_sex'),
                    ticket.get('jgjm_preview_type'),
                    ticket.get('jgjm_trainer_key'),
                    ticket.get('trainer_key'),
                    ticket.get('kind'),
                    ticket.get('attendance_type'),
                    ticket.get('status'),
                    ticket.get('real_used_lesson_count'),
                    ticket.get('real_unused_lesson_count'),
                    sync_id
                ))
                insert_count += 1
            except sqlite3.Error as e:
                skip_count += 1
                if skip_count <= 3:
                    print(f"   ⚠️  삽입 실패: {e}")

        self.conn.commit()
        print(f"   ✅ {insert_count}건 삽입 완료 (스킵: {skip_count})")
        return True

    def update_sync_history(self, members_count, tickets_count, lesson_tickets_count, success):
        """동기화 이력 업데이트"""
        cursor = self.conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO sync_history (
                    sync_id, sync_time, members_count, tickets_count,
                    lesson_tickets_count, success
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                self.sync_info['sync_id'],
                self.sync_info['sync_time'],
                members_count,
                tickets_count,
                lesson_tickets_count,
                success
            ))
            self.conn.commit()
            print(f"\n📜 동기화 이력 기록 완료")
        except sqlite3.Error as e:
            print(f"\n⚠️  이력 기록 실패: {e}")

    def verify_sync(self):
        """동기화 결과 검증"""
        print("\n" + "="*80)
        print("동기화 결과 검증")
        print("="*80)

        cursor = self.conn.cursor()

        # 각 테이블 레코드 수 확인
        tables = {
            'members': '회원',
            'tickets': '회원권',
            'lesson_tickets': '수강권'
        }

        counts = {}
        for table, name in tables.items():
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            counts[table] = count
            print(f"   {name:10s}: {count:5d}건")

        return counts


def main():
    """메인 함수"""
    print("="*80)
    print("Broj CRM 데이터 DB 동기화")
    print("="*80)

    # 경로 설정
    base_dir = Path(__file__).parent.parent
    db_path = base_dir / "data" / "members.db"
    sync_dir = base_dir / "회원관리" / "동기화" / "latest"

    # DB 동기화 객체 생성
    syncer = BrojDBSync(db_path, sync_dir)

    # DB 연결
    try:
        syncer.connect()

        # 동기화 정보 로드
        if not syncer.load_sync_info():
            print("\n❌ 동기화 정보를 로드할 수 없습니다.")
            sys.exit(1)

        # 확인 메시지
        print("\n⚠️  주의: 기존 데이터가 모두 삭제되고 새 데이터로 교체됩니다.")
        response = input("계속하시겠습니까? (yes/no): ")

        if response.lower() != 'yes':
            print("\n❌ 동기화 취소")
            sys.exit(0)

        # 동기화 실행
        success_count = 0
        total_count = 3

        if syncer.sync_members():
            success_count += 1

        if syncer.sync_tickets():
            success_count += 1

        if syncer.sync_lesson_tickets():
            success_count += 1

        # 결과 검증
        counts = syncer.verify_sync()

        # 동기화 이력 기록
        syncer.update_sync_history(
            counts.get('members', 0),
            counts.get('tickets', 0),
            counts.get('lesson_tickets', 0),
            success_count == total_count
        )

        # 최종 결과
        print("\n" + "="*80)
        print("동기화 완료")
        print("="*80)
        print(f"성공: {success_count}/{total_count}")

        if success_count == total_count:
            print("\n✅ 모든 데이터가 성공적으로 동기화되었습니다!")
        else:
            print("\n⚠️  일부 동기화가 실패했습니다.")

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        syncer.close()


if __name__ == "__main__":
    main()
