#!/usr/bin/env python3
"""
회원 데이터 분석 프로그램
"""

import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

class MemberAnalyzer:
    """회원 분석 클래스"""

    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)

    def __del__(self):
        """소멸자 - 연결 종료"""
        if hasattr(self, 'conn'):
            self.conn.close()

    def search_by_name(self, name):
        """이름으로 회원 검색"""
        query = """
            SELECT 이름, 연락처, 상태, 보유이용권, 남은일수, 최근출석일, 상담담당자
            FROM members
            WHERE 이름 LIKE ?
        """
        df = pd.read_sql(query, self.conn, params=(f'%{name}%',))
        return df

    def search_by_phone(self, phone):
        """연락처로 회원 검색"""
        query = """
            SELECT 이름, 연락처, 상태, 보유이용권, 남은일수, 최근출석일
            FROM members
            WHERE 연락처 LIKE ?
        """
        df = pd.read_sql(query, self.conn, params=(f'%{phone}%',))
        return df

    def get_expiring_members(self, days=7):
        """만료 임박 회원 조회"""
        query = """
            SELECT 이름, 연락처, 보유이용권, 최종만료일, 남은일수, 상담담당자
            FROM members
            WHERE 상태 = '활성' AND 남은일수 <= ?
            ORDER BY 남은일수 ASC
        """
        df = pd.read_sql(query, self.conn, params=(days,))
        return df

    def get_inactive_members(self, days=14):
        """장기 미출석 회원 조회 (이탈 위험군)"""
        query = """
            SELECT
                이름,
                연락처,
                최근출석일,
                남은일수,
                보유이용권,
                상담담당자
            FROM members
            WHERE 상태 = '활성'
              AND 최근출석일 IS NOT NULL
              AND julianday('now') - julianday(최근출석일) > ?
            ORDER BY 최근출석일 ASC
        """
        df = pd.read_sql(query, self.conn, params=(days,))
        return df

    def get_locker_usage(self):
        """락커 사용 현황"""
        query = """
            SELECT
                락커룸,
                락커번호,
                이름,
                연락처,
                보유대여권,
                최종만료일
            FROM members
            WHERE 락커번호 IS NOT NULL
            ORDER BY 락커룸, CAST(락커번호 AS INTEGER)
        """
        df = pd.read_sql(query, self.conn)
        return df

    def get_trainer_stats(self):
        """트레이너별 회원 통계"""
        query = """
            SELECT
                상담담당자 as 트레이너,
                COUNT(*) as 총회원수,
                SUM(CASE WHEN 상태 = '활성' THEN 1 ELSE 0 END) as 활성회원수,
                SUM(CASE WHEN 최근출석일 >= date('now', '-7 days') THEN 1 ELSE 0 END) as 주간출석,
                ROUND(AVG(남은일수), 1) as 평균잔여일수
            FROM members
            WHERE 상담담당자 != '-' AND 상담담당자 IS NOT NULL
            GROUP BY 상담담당자
            ORDER BY 활성회원수 DESC
        """
        df = pd.read_sql(query, self.conn)
        return df

    def get_product_stats(self):
        """상품(이용권) 통계"""
        query = """
            SELECT
                CASE
                    WHEN 보유이용권 LIKE '%2개월%' THEN '2개월권'
                    WHEN 보유이용권 LIKE '%3개월%' THEN '3개월권'
                    WHEN 보유이용권 LIKE '%6개월%' THEN '6개월권'
                    WHEN 보유이용권 LIKE '%10개월%' THEN '10개월권'
                    WHEN 보유이용권 LIKE '%12개월%' THEN '12개월권'
                    ELSE '기타'
                END as 상품구분,
                COUNT(*) as 구매수,
                ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM members WHERE 상태 = '활성'), 1) as 비율
            FROM members
            WHERE 상태 = '활성'
            GROUP BY 상품구분
            ORDER BY 구매수 DESC
        """
        df = pd.read_sql(query, self.conn)
        return df

    def get_age_distribution(self):
        """나이대별 분포"""
        query = """
            SELECT
                (나이/10)*10 as 나이대,
                COUNT(*) as 회원수,
                SUM(CASE WHEN 성별 = '남' THEN 1 ELSE 0 END) as 남성,
                SUM(CASE WHEN 성별 = '여' THEN 1 ELSE 0 END) as 여성
            FROM members
            WHERE 나이 IS NOT NULL AND 상태 = '활성'
            GROUP BY 나이대
            ORDER BY 나이대
        """
        df = pd.read_sql(query, self.conn)
        df['나이대'] = df['나이대'].astype(int).astype(str) + '대'
        return df

    def get_monthly_registration(self):
        """월별 신규 가입 추이"""
        query = """
            SELECT
                strftime('%Y-%m', 최초등록일) as 월,
                COUNT(*) as 신규가입,
                SUM(CASE WHEN 구분 = '신규' THEN 1 ELSE 0 END) as 신규,
                SUM(CASE WHEN 구분 != '신규' THEN 1 ELSE 0 END) as 재등록
            FROM members
            WHERE 최초등록일 IS NOT NULL
            GROUP BY 월
            ORDER BY 월 DESC
            LIMIT 12
        """
        df = pd.read_sql(query, self.conn)
        return df

    def check_member_exists(self, name):
        """회원 존재 여부 확인 (급여 분석 연동용)"""
        query = "SELECT COUNT(*) FROM members WHERE 이름 = ?"
        result = self.conn.execute(query, (name,)).fetchone()[0]
        return result > 0

    def get_member_info(self, name):
        """회원 상세 정보 조회"""
        query = "SELECT * FROM members WHERE 이름 = ?"
        df = pd.read_sql(query, self.conn, params=(name,))
        return df

def print_menu():
    """메뉴 출력"""
    print("\n" + "="*80)
    print("🏋️  Doubless 회원 분석 프로그램")
    print("="*80)
    print("1. 이름으로 회원 검색")
    print("2. 연락처로 회원 검색")
    print("3. 만료 임박 회원 (D-7)")
    print("4. 만료 임박 회원 (D-30)")
    print("5. 장기 미출석 회원 (2주)")
    print("6. 락커 사용 현황")
    print("7. 트레이너별 통계")
    print("8. 상품(이용권) 통계")
    print("9. 나이대별 분포")
    print("10. 월별 신규 가입 추이")
    print("0. 종료")
    print("="*80)

def main():
    """메인 함수"""
    # DB 경로 설정
    base_dir = Path(__file__).parent.parent
    db_file = base_dir / "data" / "members.db"

    if not db_file.exists():
        print(f"❌ 데이터베이스를 찾을 수 없습니다: {db_file}")
        print(f"   먼저 html_to_db.py를 실행하여 DB를 생성하세요.")
        return

    analyzer = MemberAnalyzer(db_file)

    while True:
        print_menu()
        choice = input("\n선택 (0-10): ").strip()

        if choice == '0':
            print("👋 프로그램을 종료합니다.")
            break

        elif choice == '1':
            name = input("검색할 이름: ").strip()
            result = analyzer.search_by_name(name)
            print(f"\n🔍 검색 결과: {len(result)}명")
            if not result.empty:
                print(result.to_string(index=False))
            else:
                print("검색 결과가 없습니다.")

        elif choice == '2':
            phone = input("검색할 연락처: ").strip()
            result = analyzer.search_by_phone(phone)
            print(f"\n🔍 검색 결과: {len(result)}명")
            if not result.empty:
                print(result.to_string(index=False))
            else:
                print("검색 결과가 없습니다.")

        elif choice == '3':
            result = analyzer.get_expiring_members(7)
            print(f"\n⚠️  7일 이내 만료 회원: {len(result)}명")
            if not result.empty:
                print(result.to_string(index=False))

        elif choice == '4':
            result = analyzer.get_expiring_members(30)
            print(f"\n⚠️  30일 이내 만료 회원: {len(result)}명")
            if not result.empty:
                print(result.to_string(index=False))

        elif choice == '5':
            result = analyzer.get_inactive_members(14)
            print(f"\n⚠️  2주 이상 미출석 회원: {len(result)}명")
            if not result.empty:
                print(result.to_string(index=False))

        elif choice == '6':
            result = analyzer.get_locker_usage()
            print(f"\n🔒 락커 사용 현황: {len(result)}개")
            if not result.empty:
                print(result.to_string(index=False))

        elif choice == '7':
            result = analyzer.get_trainer_stats()
            print("\n👨‍🏫 트레이너별 통계")
            if not result.empty:
                print(result.to_string(index=False))

        elif choice == '8':
            result = analyzer.get_product_stats()
            print("\n📦 상품(이용권) 통계")
            if not result.empty:
                print(result.to_string(index=False))

        elif choice == '9':
            result = analyzer.get_age_distribution()
            print("\n📊 나이대별 분포")
            if not result.empty:
                print(result.to_string(index=False))

        elif choice == '10':
            result = analyzer.get_monthly_registration()
            print("\n📈 월별 신규 가입 추이 (최근 12개월)")
            if not result.empty:
                print(result.to_string(index=False))

        else:
            print("❌ 잘못된 선택입니다.")

        input("\n계속하려면 Enter를 누르세요...")

if __name__ == "__main__":
    main()
