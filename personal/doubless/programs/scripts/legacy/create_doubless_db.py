#!/usr/bin/env python3
"""
Doubless 통합 DB 생성 스크립트

모든 데이터를 하나의 DB(doubless.db)로 통합:
1. 회원 관리: members, tickets, lesson_tickets, sync_history
2. 급여 관리: employees, salary_records, trainer_monthly_salary, info_staff_salary, salary_rules

데이터 소스:
- 회원관리/동기화/latest/*.json: 회원, 회원권, 수강권 데이터
- 급여 데이터: 기존 doubless.db에서 보존 또는 xlsx에서 별도 입력
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime
import shutil


def ms_to_datetime(ms_timestamp):
    """밀리초 타임스탬프를 datetime 문자열로 변환"""
    if ms_timestamp is None:
        return None
    try:
        dt = datetime.fromtimestamp(ms_timestamp / 1000)
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except (ValueError, TypeError, OSError):
        return None


# 경로 설정
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / 'data'
SYNC_DIR = BASE_DIR / '회원관리' / '동기화' / 'latest'
DOUBLESS_DB = DATA_DIR / 'doubless.db'


def create_member_tables(cursor):
    """회원 관리 테이블 생성"""

    # 1. 회원 테이블 (members)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS members (
            jgjm_key INTEGER PRIMARY KEY,
            jgjm_member_name TEXT,
            jgjm_member_phone_number TEXT,
            jgjm_member_sex TEXT,
            jgjm_member_birth_dttm TEXT,
            jgjm_address TEXT,
            jgjm_attendance_number TEXT,
            jgjm_remarks TEXT,
            jgjm_send_sms BOOLEAN,

            classification TEXT,
            customer_status TEXT,
            exercise_purpose TEXT,
            visit_route TEXT,
            is_subscriber BOOLEAN,

            created_dttm TEXT,
            first_ticket_purchase_dttm TEXT,
            last_ticket_purchase_dttm TEXT,
            last_attendance TEXT,

            ticket_start TEXT,
            ticket_end TEXT,
            left_days INTEGER,

            sync_id TEXT,
            synced_at TIMESTAMP DEFAULT (datetime('now', 'localtime'))
        )
    """)
    print("   - members 테이블 생성")

    # 2. 회원권 테이블 (tickets)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            jtd_key INTEGER PRIMARY KEY,
            jtd_name TEXT,
            jtd_memo TEXT,
            jtd_started_dttm TEXT,
            jtd_closed_dttm TEXT,
            created TEXT,

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
            synced_at TIMESTAMP DEFAULT (datetime('now', 'localtime')),

            FOREIGN KEY (jgjm_key) REFERENCES members(jgjm_key)
        )
    """)
    print("   - tickets 테이블 생성")

    # 3. 수강권 테이블 (lesson_tickets)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lesson_tickets (
            jglesson_ticket_key INTEGER PRIMARY KEY,
            jglesson_ticket_type TEXT,
            jglesson_ticket_count INTEGER,
            jglesson_origin_ticket_count INTEGER,
            jglesson_ticket_origin_count INTEGER,
            jglesson_ticket_point REAL,
            jglesson_origin_ticket_point REAL,
            jglesson_ticket_origin_point REAL,

            jglesson_ticket_started_dttm TEXT,
            jglesson_ticket_closed_dttm TEXT,
            last_lesson_dttm TEXT,

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
            synced_at TIMESTAMP DEFAULT (datetime('now', 'localtime')),

            FOREIGN KEY (jgjm_key) REFERENCES members(jgjm_key)
        )
    """)
    print("   - lesson_tickets 테이블 생성")

    # 4. 출석 테이블 (attendance)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            jga_key INTEGER UNIQUE,
            jgjm_key INTEGER,
            jgjm_member_name TEXT,
            jgjm_member_phone_number TEXT,
            attendance_dttm TEXT,
            attendance_type TEXT,
            device_name TEXT,
            sync_id TEXT,
            synced_at TIMESTAMP DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (jgjm_key) REFERENCES members(jgjm_key)
        )
    """)
    print("   - attendance 테이블 생성")

    # 5. 동기화 이력 테이블 (sync_history)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sync_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sync_id TEXT UNIQUE NOT NULL,
            sync_time TIMESTAMP,
            members_count INTEGER,
            tickets_count INTEGER,
            lesson_tickets_count INTEGER,
            attendance_count INTEGER,
            success BOOLEAN,
            error_message TEXT,
            created_at TIMESTAMP DEFAULT (datetime('now', 'localtime'))
        )
    """)
    print("   - sync_history 테이블 생성")


def create_salary_tables(cursor):
    """급여 관리 테이블 생성"""

    # 1. 직원 테이블 (employees)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            job_type TEXT NOT NULL,
            bank TEXT,
            account_number TEXT,
            resident_number TEXT,
            status TEXT DEFAULT '근무',
            role TEXT DEFAULT '일반',
            work_type TEXT DEFAULT '종일',
            start_date DATE,
            created_at TIMESTAMP DEFAULT (datetime('now', 'localtime')),
            updated_at TIMESTAMP DEFAULT (datetime('now', 'localtime')),
            UNIQUE(name, resident_number)
        )
    ''')
    print("   - employees 테이블 생성")

    # 2. 수업내역 테이블 (salary_records)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS salary_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            년도 INTEGER NOT NULL,
            월 TEXT NOT NULL,
            트레이너 TEXT NOT NULL,
            NO INTEGER,
            회원명 TEXT NOT NULL,
            성별 TEXT,
            등록세션 REAL,
            총진행세션 REAL,
            남은세션 REAL,
            결제형태 TEXT,
            등록비용 REAL,
            공급가 REAL,
            회단가 REAL,
            매출대비율 REAL,
            수업료_정산 REAL,
            당월진행세션 REAL,
            당월수업료 REAL,
            이달의매출 REAL,
            등록일시 TEXT DEFAULT (datetime('now', 'localtime')),
            UNIQUE(년도, 월, 트레이너, 회원명)
        )
    ''')
    print("   - salary_records 테이블 생성")

    # 3. 트레이너 월별 급여 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trainer_monthly_salary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER,
            trainer_name TEXT NOT NULL,
            year INTEGER NOT NULL,
            month INTEGER NOT NULL,
            base_salary REAL DEFAULT 0,
            incentive REAL DEFAULT 0,
            tuition_fee REAL DEFAULT 0,
            monthly_revenue REAL DEFAULT 0,
            base_incentive_payment_date DATE,
            tuition_payment_date DATE,
            total_salary REAL,
            notes TEXT,
            created_at TIMESTAMP DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (employee_id) REFERENCES employees(id),
            UNIQUE(trainer_name, year, month)
        )
    ''')
    print("   - trainer_monthly_salary 테이블 생성")

    # 4. 인포 직원 급여 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS info_staff_salary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER,
            staff_name TEXT NOT NULL,
            year INTEGER NOT NULL,
            month INTEGER NOT NULL,
            base_salary REAL DEFAULT 0,
            salary_after_tax REAL,
            payment_date DATE,
            extra_pay REAL DEFAULT 0,
            extra_pay_note TEXT,
            total_salary REAL,
            notes TEXT,
            created_at TIMESTAMP DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (employee_id) REFERENCES employees(id),
            UNIQUE(staff_name, year, month)
        )
    ''')
    print("   - info_staff_salary 테이블 생성")

    # 5. 급여 규칙 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS salary_rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            period TEXT NOT NULL,
            role TEXT NOT NULL,
            min_revenue INTEGER NOT NULL,
            base_salary INTEGER NOT NULL,
            tuition_rate REAL NOT NULL,
            UNIQUE(period, role, min_revenue)
        )
    ''')
    print("   - salary_rules 테이블 생성")


def create_indexes(cursor):
    """인덱스 생성"""
    # 회원 관련 인덱스
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_members_name ON members(jgjm_member_name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_members_phone ON members(jgjm_member_phone_number)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_members_status ON members(customer_status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tickets_member ON tickets(jgjm_key)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(ticket_status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_lesson_member ON lesson_tickets(jgjm_key)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_lesson_trainer ON lesson_tickets(jgjm_trainer_key)")

    # 급여 관련 인덱스
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_salary_trainer ON salary_records(트레이너)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_salary_month ON salary_records(년도, 월)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_trainer_salary_month ON trainer_monthly_salary(trainer_name, year, month)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_info_salary_month ON info_staff_salary(staff_name, year, month)')

    print("   - 인덱스 생성 완료")


def load_members_from_json(cursor, sync_dir):
    """JSON에서 회원 데이터 로드"""
    sync_info_file = sync_dir / 'sync_info.json'
    if not sync_info_file.exists():
        print("   - sync_info.json 없음, 스킵")
        return 0

    with open(sync_info_file, 'r', encoding='utf-8') as f:
        sync_info = json.load(f)

    sync_id = sync_info['sync_id']
    members_file = sync_dir / sync_info['files']['members']

    if not members_file.exists():
        print(f"   - {members_file.name} 없음, 스킵")
        return 0

    with open(members_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    members = data['members']
    count = 0

    for member in members:
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO members (
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
                ms_to_datetime(member.get('jgjm_member_birth_dttm')),
                member.get('jgjm_address'),
                member.get('jgjm_attendance_number'),
                member.get('jgjm_remarks'),
                member.get('jgjm_send_sms', False),
                member.get('classification'),
                member.get('customer_status'),
                member.get('exercise_purpose'),
                member.get('visit_route'),
                member.get('is_subscriber', False),
                ms_to_datetime(member.get('created_dttm')),
                ms_to_datetime(member.get('first_ticket_purchase_dttm')),
                ms_to_datetime(member.get('last_ticket_purchase_dttm')),
                ms_to_datetime(member.get('last_attendance')),
                ms_to_datetime(member.get('ticket_start')),
                ms_to_datetime(member.get('ticket_end')),
                member.get('left_days'),
                sync_id
            ))
            count += 1
        except sqlite3.Error as e:
            if count == 0:
                print(f"   - 회원 입력 오류: {e}")

    print(f"   - members: {count}명 입력")
    return count


def load_tickets_from_json(cursor, sync_dir):
    """JSON에서 회원권 데이터 로드"""
    sync_info_file = sync_dir / 'sync_info.json'
    if not sync_info_file.exists():
        return 0

    with open(sync_info_file, 'r', encoding='utf-8') as f:
        sync_info = json.load(f)

    sync_id = sync_info['sync_id']
    tickets_file = sync_dir / sync_info['files']['tickets']

    if not tickets_file.exists():
        print(f"   - {tickets_file.name} 없음, 스킵")
        return 0

    with open(tickets_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    tickets = data['tickets']
    count = 0

    for ticket in tickets:
        try:
            customer = ticket.get('Customer', {}) if ticket.get('Customer') else {}

            cursor.execute("""
                INSERT OR REPLACE INTO tickets (
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
                ms_to_datetime(ticket.get('jtd_started_dttm')),
                ms_to_datetime(ticket.get('jtd_closed_dttm')),
                ms_to_datetime(ticket.get('created')),
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
            count += 1
        except sqlite3.Error as e:
            if count == 0:
                print(f"   - 회원권 입력 오류: {e}")

    print(f"   - tickets: {count}건 입력")
    return count


def load_lesson_tickets_from_json(cursor, sync_dir):
    """JSON에서 수강권 데이터 로드"""
    sync_info_file = sync_dir / 'sync_info.json'
    if not sync_info_file.exists():
        return 0

    with open(sync_info_file, 'r', encoding='utf-8') as f:
        sync_info = json.load(f)

    sync_id = sync_info['sync_id']
    lesson_file = sync_dir / sync_info['files']['lesson_tickets']

    if not lesson_file.exists():
        print(f"   - {lesson_file.name} 없음, 스킵")
        return 0

    with open(lesson_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    lesson_tickets = data['lesson_tickets']
    count = 0

    for ticket in lesson_tickets:
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO lesson_tickets (
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
                ms_to_datetime(ticket.get('jglesson_ticket_started_dttm')),
                ms_to_datetime(ticket.get('jglesson_ticket_closed_dttm')),
                ms_to_datetime(ticket.get('last_lesson_dttm')),
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
            count += 1
        except sqlite3.Error as e:
            if count == 0:
                print(f"   - 수강권 입력 오류: {e}")

    print(f"   - lesson_tickets: {count}건 입력")
    return count


def restore_salary_data(cursor, backup_db_path):
    """백업 DB에서 급여 데이터 복원"""
    if not backup_db_path or not backup_db_path.exists():
        print("   - 급여 데이터 백업 없음, 스킵")
        return

    src_conn = sqlite3.connect(backup_db_path)
    src_cursor = src_conn.cursor()

    tables = ['employees', 'salary_records', 'trainer_monthly_salary', 'info_staff_salary', 'salary_rules']

    for table in tables:
        try:
            src_cursor.execute(f'SELECT * FROM {table}')
            rows = src_cursor.fetchall()
            src_cursor.execute(f'PRAGMA table_info({table})')
            cols = [col[1] for col in src_cursor.fetchall()]

            for row in rows:
                try:
                    values = row[1:]  # id 제외
                    col_names = ','.join(cols[1:])
                    placeholders = ','.join(['?' for _ in cols[1:]])
                    cursor.execute(f'INSERT OR REPLACE INTO {table} ({col_names}) VALUES ({placeholders})', values)
                except:
                    pass
            print(f"   - {table}: {len(rows)}건 복원")
        except:
            print(f"   - {table}: 없음")

    src_conn.close()



def add_sync_history(cursor, members_count, tickets_count, lesson_count):
    """동기화 이력 추가"""
    sync_id = datetime.now().strftime('%Y%m%d_%H%M%S')
    cursor.execute("""
        INSERT INTO sync_history (
            sync_id, sync_time, members_count, tickets_count, lesson_tickets_count, success
        ) VALUES (?, ?, ?, ?, ?, ?)
    """, (sync_id, datetime.now().isoformat(), members_count, tickets_count, lesson_count, True))
    print(f"   - sync_history 기록 완료 (sync_id: {sync_id})")


def show_summary(db_path):
    """DB 요약 출력"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("\n" + "=" * 60)
    print("Doubless 통합 DB 요약")
    print("=" * 60)

    # 테이블별 건수
    tables = [
        ('members', '회원'),
        ('tickets', '회원권'),
        ('lesson_tickets', '수강권'),
        ('employees', '직원'),
        ('salary_records', '수업내역'),
        ('trainer_monthly_salary', '트레이너급여'),
        ('info_staff_salary', '인포급여'),
        ('salary_rules', '급여규칙'),
        ('sync_history', '동기화이력')
    ]

    print("\n테이블별 레코드 수:")
    for table, name in tables:
        try:
            cursor.execute(f'SELECT COUNT(*) FROM {table}')
            count = cursor.fetchone()[0]
            print(f"  {name:12s} ({table:22s}): {count:>6,}건")
        except:
            print(f"  {name:12s} ({table:22s}): 없음")

    conn.close()


def main():
    print("=" * 60)
    print("Doubless 통합 DB 생성")
    print("=" * 60)
    print(f"동기화 데이터: {SYNC_DIR}")
    print(f"통합 DB: {DOUBLESS_DB}")

    # 기존 DB 백업
    backup_path = None
    if DOUBLESS_DB.exists():
        backup_dir = DATA_DIR / 'backups'
        backup_dir.mkdir(exist_ok=True)
        backup_path = backup_dir / f'doubless_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
        shutil.copy(DOUBLESS_DB, backup_path)
        print(f"\n기존 DB 백업: {backup_path.name}")
        DOUBLESS_DB.unlink()

    # DB 생성
    conn = sqlite3.connect(DOUBLESS_DB)
    cursor = conn.cursor()

    # 1. 테이블 생성
    print("\n[1/4] 테이블 생성...")
    create_member_tables(cursor)
    create_salary_tables(cursor)
    create_indexes(cursor)
    conn.commit()

    # 2. 회원 데이터 로드
    print("\n[2/4] 회원 데이터 로드 (JSON)...")
    members_count = load_members_from_json(cursor, SYNC_DIR)
    tickets_count = load_tickets_from_json(cursor, SYNC_DIR)
    lesson_count = load_lesson_tickets_from_json(cursor, SYNC_DIR)
    conn.commit()

    # 3. 급여 데이터 복원 (백업에서)
    print("\n[3/4] 급여 데이터 복원...")
    restore_salary_data(cursor, backup_path)
    conn.commit()

    # 4. 동기화 이력 추가
    print("\n[4/4] 동기화 이력 기록...")
    add_sync_history(cursor, members_count, tickets_count, lesson_count)
    conn.commit()

    conn.close()

    # 요약 출력
    show_summary(DOUBLESS_DB)

    print("\n" + "=" * 60)
    print("Doubless 통합 DB 생성 완료!")
    print("=" * 60)


if __name__ == '__main__':
    main()
