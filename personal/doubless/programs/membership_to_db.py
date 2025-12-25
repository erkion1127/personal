#!/usr/bin/env python3
"""
수강권 및 회원권 데이터를 HTML에서 파싱하여 DB로 저장

- 수강권: PT 및 예약권 데이터
- 회원권: 헬스 회원권 데이터
"""

import sqlite3
from pathlib import Path
from bs4 import BeautifulSoup
from datetime import datetime

def parse_suganggwon_html(html_file):
    """수강권 HTML 파싱"""
    with open(html_file, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')

    table = soup.find('table')
    if not table:
        print(f"⚠️  테이블을 찾을 수 없습니다: {html_file}")
        return []

    rows = table.find('tbody').find_all('tr')
    data = []

    for row in rows:
        cols = row.find_all('td')
        if len(cols) < 16:
            continue

        record = {
            '강사명': cols[0].text.strip(),
            '수강권명': cols[1].text.strip(),
            '수강권종류': cols[2].text.strip(),
            '이름': cols[3].text.strip(),
            '연락처': cols[4].text.strip(),
            '마지막수업일': cols[5].text.strip(),
            '미진행수업횟수': cols[6].text.strip(),
            '잔여횟수': cols[7].text.strip(),
            '총횟수': cols[8].text.strip(),
            '시작일': cols[9].text.strip(),
            '종료일': cols[10].text.strip(),
            '남은일수': cols[11].text.strip(),
            '포인트': cols[12].text.strip(),
            'BROJ상태': cols[13].text.strip(),
            '상담담당자': cols[14].text.strip(),
            '주소': cols[15].text.strip()
        }
        data.append(record)

    return data

def parse_hoewongwon_html(html_file):
    """회원권 HTML 파싱"""
    with open(html_file, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')

    table = soup.find('table')
    if not table:
        print(f"⚠️  테이블을 찾을 수 없습니다: {html_file}")
        return []

    rows = table.find('tbody').find_all('tr')
    data = []

    for row in rows:
        cols = row.find_all('td')
        if len(cols) < 14:
            continue

        record = {
            '상태': cols[0].text.strip(),
            '이름': cols[1].text.strip(),
            '성별': cols[2].text.strip(),
            '연락처': cols[3].text.strip(),
            '회원권명': cols[4].text.strip(),
            '통합회원권여부': cols[5].text.strip(),
            '판매금액': cols[6].text.strip().replace(',', ''),
            '구매일': cols[7].text.strip(),
            '시작일': cols[8].text.strip(),
            '종료일': cols[9].text.strip(),
            '잔여횟수': cols[10].text.strip(),
            '총횟수': cols[11].text.strip(),
            '일일입장가능횟수': cols[12].text.strip(),
            '주소': cols[13].text.strip()
        }
        data.append(record)

    return data

def create_suganggwon_table(conn):
    """수강권 테이블 생성"""
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS suganggwon (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            강사명 TEXT,
            수강권명 TEXT,
            수강권종류 TEXT,
            이름 TEXT,
            연락처 TEXT,
            마지막수업일 TEXT,
            미진행수업횟수 TEXT,
            잔여횟수 TEXT,
            총횟수 TEXT,
            시작일 TEXT,
            종료일 TEXT,
            남은일수 TEXT,
            포인트 TEXT,
            BROJ상태 TEXT,
            상담담당자 TEXT,
            주소 TEXT,
            수집일시 TEXT
        )
    ''')
    conn.commit()

def create_hoewongwon_table(conn):
    """회원권 테이블 생성"""
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS hoewongwon (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            상태 TEXT,
            이름 TEXT,
            성별 TEXT,
            연락처 TEXT,
            회원권명 TEXT,
            통합회원권여부 TEXT,
            판매금액 INTEGER,
            구매일 TEXT,
            시작일 TEXT,
            종료일 TEXT,
            잔여횟수 TEXT,
            총횟수 TEXT,
            일일입장가능횟수 TEXT,
            주소 TEXT,
            수집일시 TEXT
        )
    ''')
    conn.commit()

def insert_suganggwon_data(conn, data):
    """수강권 데이터 삽입"""
    cursor = conn.cursor()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    for record in data:
        cursor.execute('''
            INSERT INTO suganggwon (
                강사명, 수강권명, 수강권종류, 이름, 연락처, 마지막수업일,
                미진행수업횟수, 잔여횟수, 총횟수, 시작일, 종료일, 남은일수,
                포인트, BROJ상태, 상담담당자, 주소, 수집일시
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            record['강사명'], record['수강권명'], record['수강권종류'],
            record['이름'], record['연락처'], record['마지막수업일'],
            record['미진행수업횟수'], record['잔여횟수'], record['총횟수'],
            record['시작일'], record['종료일'], record['남은일수'],
            record['포인트'], record['BROJ상태'], record['상담담당자'],
            record['주소'], now
        ))

    conn.commit()
    return len(data)

def insert_hoewongwon_data(conn, data):
    """회원권 데이터 삽입"""
    cursor = conn.cursor()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    for record in data:
        # 판매금액 처리
        try:
            price = int(record['판매금액']) if record['판매금액'] and record['판매금액'] != '-' else 0
        except:
            price = 0

        cursor.execute('''
            INSERT INTO hoewongwon (
                상태, 이름, 성별, 연락처, 회원권명, 통합회원권여부,
                판매금액, 구매일, 시작일, 종료일, 잔여횟수, 총횟수,
                일일입장가능횟수, 주소, 수집일시
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            record['상태'], record['이름'], record['성별'], record['연락처'],
            record['회원권명'], record['통합회원권여부'], price,
            record['구매일'], record['시작일'], record['종료일'],
            record['잔여횟수'], record['총횟수'], record['일일입장가능횟수'],
            record['주소'], now
        ))

    conn.commit()
    return len(data)

def main():
    print("="*80)
    print("🎫 수강권 및 회원권 데이터 DB 구축")
    print("="*80)

    # 경로 설정
    base_dir = Path(__file__).parent.parent
    suganggwon_dir = base_dir / "회원관리" / "수강권"
    hoewongwon_dir = base_dir / "회원관리" / "회원권"
    db_file = base_dir / "data" / "members.db"

    # DB 연결
    conn = sqlite3.connect(db_file)

    # 테이블 생성
    create_suganggwon_table(conn)
    create_hoewongwon_table(conn)

    total_suganggwon = 0
    total_hoewongwon = 0

    # 수강권 데이터 처리
    print(f"\n📋 수강권 데이터 처리 중...")
    suganggwon_files = list(suganggwon_dir.glob("*.html"))

    for html_file in suganggwon_files:
        print(f"   파싱 중: {html_file.name}")
        data = parse_suganggwon_html(html_file)
        count = insert_suganggwon_data(conn, data)
        total_suganggwon += count
        print(f"   ✅ {count}건 삽입 완료")

    # 회원권 데이터 처리
    print(f"\n🎟️  회원권 데이터 처리 중...")
    hoewongwon_files = list(hoewongwon_dir.glob("*.html"))

    for html_file in hoewongwon_files:
        print(f"   파싱 중: {html_file.name}")
        data = parse_hoewongwon_html(html_file)
        count = insert_hoewongwon_data(conn, data)
        total_hoewongwon += count
        print(f"   ✅ {count}건 삽입 완료")

    conn.close()

    # 요약
    print(f"\n{'='*80}")
    print(f"✅ DB 구축 완료")
    print(f"{'='*80}")
    print(f"수강권 데이터: {total_suganggwon}건")
    print(f"회원권 데이터: {total_hoewongwon}건")
    print(f"\nDB 위치: {db_file}")

if __name__ == "__main__":
    main()
