#!/usr/bin/env python3
"""
트레이너 급여 명세표 조회
사용법: python view_salary_report.py [년도] [월]
예시: python view_salary_report.py 2025 12
"""

import sqlite3
from pathlib import Path
import sys


def view_salary_report(db_path, year, month):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            trainer_name, job_type,
            year || '년 ' || month || '월' as salary_month,
            base_salary, incentive, base_incentive_after_tax, base_payment_date,
            tuition_fee, tuition_after_tax, tuition_payment_date,
            total_salary, total_after_tax,
            account_number, bank, resident_number
        FROM trainer_salary_report
        WHERE year = ? AND month = ?
        ORDER BY
            CASE trainer_name
                WHEN '이준수' THEN 1
                WHEN '한길수' THEN 2
                WHEN '신지훈' THEN 3
                WHEN '이현수' THEN 4
                ELSE 5
            END
    """, (year, month))

    results = cursor.fetchall()
    conn.close()

    if not results:
        print(f"❌ {year}년 {month}월 데이터가 없습니다.")
        return

    print("=" * 120)
    print(f"📋 {year}년 {month}월 트레이너 급여 명세표")
    print("=" * 120)
    print()

    for row in results:
        name, job, month_str, base, incentive, base_tax, base_date, tuition, tuition_tax, tuition_date, total, total_tax, account, bank, resident = row

        print(f"▶ {name} ({job})")
        print("-" * 60)
        print(f"  급여월: {month_str}")
        print(f"  기본급: {base:,}원 | 인센티브: {incentive:,}원")
        print(f"  (기본급+인센) 3.3% 적용: {base_tax:,}원 → 지급일: {base_date}")
        print(f"  수업료: {tuition:,}원")
        print(f"  수업료 3.3% 적용: {tuition_tax:,}원 → 지급일: {tuition_date}")
        print(f"  ─────────────────────────────")
        print(f"  총급여: {total:,}원 | 총지급액: {total_tax:,}원")
        print(f"  입금계좌: {bank} {account}")
        print()

    # 합계
    cursor = sqlite3.connect(db_path).cursor()
    cursor.execute("""
        SELECT SUM(total_salary), SUM(total_after_tax)
        FROM trainer_salary_report
        WHERE year = ? AND month = ?
    """, (year, month))
    total_sum, total_tax_sum = cursor.fetchone()

    print("=" * 60)
    print(f"💰 합계: 총급여 {total_sum:,}원 | 총지급액 {total_tax_sum:,}원")
    print("=" * 60)


def main():
    base_dir = Path(__file__).parent.parent
    db_path = base_dir / "data" / "doubless.db"

    if len(sys.argv) >= 3:
        year = int(sys.argv[1])
        month = int(sys.argv[2])
    else:
        # 최신 데이터 조회
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT year, month FROM trainer_salary_report ORDER BY year DESC, month DESC LIMIT 1")
        result = cursor.fetchone()
        conn.close()

        if result:
            year, month = result
        else:
            print("❌ 저장된 급여 명세가 없습니다.")
            return

    view_salary_report(db_path, year, month)


if __name__ == "__main__":
    main()
