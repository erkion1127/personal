#!/usr/bin/env python3
"""
HTML 회원 리스트를 SQLite DB로 변환하는 프로그램
"""

import sqlite3
import re
from bs4 import BeautifulSoup
from pathlib import Path
from datetime import datetime

def create_database(db_path):
    """회원 데이터베이스 생성"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 회원 테이블 생성
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            상태 TEXT,
            이름 TEXT NOT NULL,
            성별 TEXT,
            생년월일 TEXT,
            나이 INTEGER,
            연락처 TEXT,
            보유이용권 TEXT,
            보유대여권 TEXT,
            구독플랜 TEXT,
            락커룸 TEXT,
            락커번호 TEXT,
            구분 TEXT,
            최초등록일 TEXT,
            최종만료일 TEXT,
            남은일수 INTEGER,
            남은일수_텍스트 TEXT,
            최근구매일 TEXT,
            최근출석일 TEXT,
            BROJ운톡 TEXT,
            출석번호 TEXT,
            특이사항 TEXT,
            운동목적 TEXT,
            방문경로 TEXT,
            상담담당자 TEXT,
            주소 TEXT,
            등록일시 TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 인덱스 생성 (검색 성능 향상)
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_name ON members(이름)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_status ON members(상태)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_phone ON members(연락처)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_expire ON members(최종만료일)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_counselor ON members(상담담당자)')

    conn.commit()
    return conn

def parse_days_remaining(text):
    """남은 일수 텍스트에서 숫자 추출"""
    if not text or text == '-':
        return None
    match = re.search(r'(\d+)일', text)
    if match:
        return int(match.group(1))
    return None

def parse_locker_info(text):
    """락커 정보 파싱 (락커룸/락커번호)"""
    if not text or text.strip() == '':
        return None, None

    # "남자개인락카/383번" 형태
    if '/' in text:
        parts = text.split('/')
        locker_room = parts[0].strip()
        locker_num = parts[1].replace('번', '').strip()
        return locker_room, locker_num

    return text.strip(), None

def clean_text(text):
    """텍스트 정리 (공백, 개행 제거)"""
    if not text:
        return None
    text = text.strip()
    text = re.sub(r'\s+', ' ', text)
    return text if text and text != '-' else None

def parse_html_to_db(html_file, conn):
    """HTML 파일을 파싱하여 DB에 저장"""
    print(f"📄 파일 읽는 중: {html_file}")

    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, 'html.parser')

    # 테이블 행 찾기
    rows = soup.find_all('tr', {'valign': 'middle'})

    print(f"✅ {len(rows)}명의 회원 데이터 발견")

    cursor = conn.cursor()
    inserted = 0

    for row in rows:
        cells = row.find_all('td')

        if len(cells) < 23:  # 최소 컬럼 수 확인
            continue

        try:
            # 각 셀에서 텍스트 추출
            상태 = clean_text(cells[0].get_text())
            이름 = clean_text(cells[1].get_text())
            성별 = clean_text(cells[2].get_text())
            생년월일 = clean_text(cells[3].get_text())
            나이_text = clean_text(cells[4].get_text())
            나이 = int(re.search(r'\d+', 나이_text).group()) if 나이_text and re.search(r'\d+', 나이_text) else None
            연락처 = clean_text(cells[5].get_text())
            보유이용권 = clean_text(cells[6].get_text())
            보유대여권 = clean_text(cells[7].get_text())
            구독플랜 = clean_text(cells[8].get_text())

            락커룸, 락커번호 = parse_locker_info(clean_text(cells[9].get_text()))

            구분 = clean_text(cells[10].get_text())
            최초등록일 = clean_text(cells[11].get_text())
            최종만료일 = clean_text(cells[12].get_text())
            남은일수_텍스트 = clean_text(cells[13].get_text())
            남은일수 = parse_days_remaining(남은일수_텍스트)
            최근구매일 = clean_text(cells[14].get_text())
            최근출석일 = clean_text(cells[15].get_text())
            BROJ운톡 = clean_text(cells[16].get_text())
            출석번호 = clean_text(cells[17].get_text())
            특이사항 = clean_text(cells[18].get_text())
            운동목적 = clean_text(cells[19].get_text())
            방문경로 = clean_text(cells[20].get_text())
            상담담당자 = clean_text(cells[21].get_text())
            주소 = clean_text(cells[22].get_text())

            # DB에 삽입
            cursor.execute('''
                INSERT INTO members (
                    상태, 이름, 성별, 생년월일, 나이, 연락처,
                    보유이용권, 보유대여권, 구독플랜, 락커룸, 락커번호,
                    구분, 최초등록일, 최종만료일, 남은일수, 남은일수_텍스트,
                    최근구매일, 최근출석일, BROJ운톡, 출석번호,
                    특이사항, 운동목적, 방문경로, 상담담당자, 주소
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                상태, 이름, 성별, 생년월일, 나이, 연락처,
                보유이용권, 보유대여권, 구독플랜, 락커룸, 락커번호,
                구분, 최초등록일, 최종만료일, 남은일수, 남은일수_텍스트,
                최근구매일, 최근출석일, BROJ운톡, 출석번호,
                특이사항, 운동목적, 방문경로, 상담담당자, 주소
            ))

            inserted += 1

        except Exception as e:
            print(f"⚠️  오류 발생 (회원: {이름 if '이름' in locals() else 'Unknown'}): {e}")
            continue

    conn.commit()
    print(f"✅ {inserted}명의 회원 데이터 저장 완료")
    return inserted

def print_statistics(conn):
    """데이터베이스 통계 출력"""
    cursor = conn.cursor()

    print("\n" + "="*80)
    print("📊 데이터베이스 통계")
    print("="*80)

    # 전체 회원 수
    total = cursor.execute("SELECT COUNT(*) FROM members").fetchone()[0]
    print(f"총 회원 수: {total}명")

    # 상태별 회원 수
    print("\n[상태별 분류]")
    status_stats = cursor.execute("""
        SELECT 상태, COUNT(*) as cnt
        FROM members
        GROUP BY 상태
        ORDER BY cnt DESC
    """).fetchall()
    for status, count in status_stats:
        print(f"  {status}: {count}명")

    # 성별 통계
    print("\n[성별 분류]")
    gender_stats = cursor.execute("""
        SELECT 성별, COUNT(*) as cnt
        FROM members
        GROUP BY 성별
    """).fetchall()
    for gender, count in gender_stats:
        print(f"  {gender}: {count}명")

    # 나이대별 통계
    print("\n[나이대별 분류]")
    age_stats = cursor.execute("""
        SELECT (나이/10)*10 as 나이대, COUNT(*) as cnt
        FROM members
        WHERE 나이 IS NOT NULL
        GROUP BY 나이대
        ORDER BY 나이대
    """).fetchall()
    for age_group, count in age_stats:
        print(f"  {int(age_group)}대: {count}명")

    # 만료 임박 회원
    print("\n[만료 임박 회원]")
    expiring_stats = cursor.execute("""
        SELECT
            SUM(CASE WHEN 남은일수 <= 7 THEN 1 ELSE 0 END) as within_7days,
            SUM(CASE WHEN 남은일수 <= 30 THEN 1 ELSE 0 END) as within_30days
        FROM members
        WHERE 상태 = '활성'
    """).fetchone()
    print(f"  7일 이내 만료: {expiring_stats[0]}명")
    print(f"  30일 이내 만료: {expiring_stats[1]}명")

    # 락커 사용 현황
    locker_count = cursor.execute("""
        SELECT COUNT(*) FROM members WHERE 락커번호 IS NOT NULL
    """).fetchone()[0]
    print(f"\n락커 사용 회원: {locker_count}명")

    print("="*80)

def main():
    """메인 함수"""
    print("="*80)
    print("🏋️  Doubless 회원 관리 DB 구축 프로그램")
    print("="*80)

    # 경로 설정
    base_dir = Path(__file__).parent.parent
    html_files = [
        base_dir / "회원관리" / "회원리스트.html",
        base_dir / "회원관리" / "회원리스트_2.html"
    ]
    db_file = base_dir / "data" / "members.db"

    # HTML 파일 확인
    existing_files = [f for f in html_files if f.exists()]
    if not existing_files:
        print(f"❌ HTML 파일을 찾을 수 없습니다")
        print(f"   다음 위치에 '회원리스트.html' 또는 '회원리스트_2.html' 파일이 있는지 확인하세요:")
        print(f"   {base_dir / '회원관리'}")
        return

    print(f"📋 발견된 HTML 파일: {len(existing_files)}개")
    for f in existing_files:
        print(f"   - {f.name}")

    # 기존 DB 백업
    if db_file.exists():
        backup_file = db_file.parent / f"members_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        import shutil
        shutil.copy(db_file, backup_file)
        print(f"📦 기존 DB 백업: {backup_file.name}")
        db_file.unlink()  # 기존 DB 삭제

    # 데이터베이스 생성
    print(f"\n🔧 데이터베이스 생성: {db_file}")
    conn = create_database(db_file)

    # 모든 HTML 파일 파싱 및 데이터 저장
    total_inserted = 0
    for html_file in existing_files:
        inserted = parse_html_to_db(html_file, conn)
        total_inserted += inserted

    print(f"\n✅ 총 {total_inserted}명의 회원 데이터 저장 완료")

    # 통계 출력
    print_statistics(conn)

    conn.close()

    print(f"\n✅ 데이터베이스 저장 완료: {db_file}")
    print(f"\n💡 사용 방법:")
    print(f"   python member_analysis.py  # 회원 분석 프로그램 실행")

if __name__ == "__main__":
    main()
