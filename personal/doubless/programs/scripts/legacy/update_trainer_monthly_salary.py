#!/usr/bin/env python3
"""
salary_records에서 trainer_monthly_salary로 집계하는 스크립트

salary_records의 데이터를 기반으로 트레이너별 월간 급여를 자동 계산하여
trainer_monthly_salary 테이블에 저장합니다.
"""

import sqlite3
from pathlib import Path
import sys


def calculate_trainer_monthly_salary(db_path, year, month_str):
    """특정 연월의 트레이너별 급여 집계"""

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print(f"\n{'='*80}")
    print(f"📊 {year}년 {month_str} 트레이너별 급여 집계")
    print('='*80)

    # salary_records에서 트레이너별 집계
    cursor.execute("""
        SELECT
            트레이너,
            COUNT(DISTINCT 회원명) as 회원수,
            SUM(당월진행세션) as 총진행세션,
            SUM(당월수업료) as 총수업료,
            SUM(수업료_정산) as 총수업료정산,
            SUM(이달의매출) as 총매출
        FROM salary_records
        WHERE 년도 = ? AND 월 = ?
        GROUP BY 트레이너
        ORDER BY 트레이너
    """, (year, month_str))

    results = cursor.fetchall()

    if not results:
        print(f"⚠️  {year}년 {month_str} 데이터가 없습니다.")
        conn.close()
        return 0

    print(f"\n📋 집계 결과:")
    print(f"{'트레이너':<10} {'회원수':<8} {'진행세션':<10} {'총수업료':<15} {'총매출':<15}")
    print('-'*70)

    for row in results:
        trainer_name = row[0]
        member_count = row[1]
        total_sessions = row[2] or 0
        total_tuition = row[3] or 0
        total_tuition_settlement = row[4] or 0
        total_revenue = row[5] or 0

        print(f"{trainer_name:<10} {member_count:<8} {total_sessions:<10.0f} {total_tuition:<15,.0f} {total_revenue:<15,.0f}")

    # 사용자 확인
    print(f"\n⚠️  이 데이터를 trainer_monthly_salary 테이블에 저장하시겠습니까?")
    print(f"   (기존 {year}년 {month_str} 데이터가 있으면 업데이트됩니다)")
    response = input("계속하시겠습니까? (yes/no): ")

    if response.lower() != 'yes':
        print("\n❌ 취소되었습니다.")
        conn.close()
        return 0

    # trainer_monthly_salary에 저장
    print(f"\n💾 저장 중...")
    month_num = int(month_str.replace('월', ''))

    insert_count = 0
    update_count = 0

    for row in results:
        trainer_name = row[0]
        total_tuition = row[3] or 0
        total_revenue = row[5] or 0

        # 기존 데이터 확인
        cursor.execute("""
            SELECT id FROM trainer_monthly_salary
            WHERE trainer_name = ? AND year = ? AND month = ?
        """, (trainer_name, year, month_num))

        existing = cursor.fetchone()

        if existing:
            # 업데이트
            cursor.execute("""
                UPDATE trainer_monthly_salary
                SET tuition_fee = ?,
                    monthly_revenue = ?,
                    total_salary = base_salary + incentive + ?
                WHERE trainer_name = ? AND year = ? AND month = ?
            """, (total_tuition, total_revenue, total_tuition, trainer_name, year, month_num))
            update_count += 1
        else:
            # 신규 삽입 (기본급은 0으로 설정, 나중에 수동 업데이트 필요)
            cursor.execute("""
                INSERT INTO trainer_monthly_salary
                (trainer_name, year, month, base_salary, incentive, tuition_fee, monthly_revenue, total_salary)
                VALUES (?, ?, ?, 0, 0, ?, ?, ?)
            """, (trainer_name, year, month_num, total_tuition, total_revenue, total_tuition))
            insert_count += 1

    conn.commit()
    print(f"   ✅ 신규 {insert_count}건, 업데이트 {update_count}건")

    # 결과 확인
    print(f"\n✅ 저장 완료! 결과 확인:")
    cursor.execute("""
        SELECT trainer_name, base_salary, tuition_fee, monthly_revenue, total_salary
        FROM trainer_monthly_salary
        WHERE year = ? AND month = ?
        ORDER BY trainer_name
    """, (year, month_num))

    print(f"\n{'트레이너':<10} {'기본급':<12} {'수업료':<12} {'매출':<12} {'총급여':<12}")
    print('-'*70)
    for row in cursor.fetchall():
        print(f"{row[0]:<10} {row[1]:<12,.0f} {row[2]:<12,.0f} {row[3]:<12,.0f} {row[4]:<12,.0f}")

    conn.close()
    return insert_count + update_count


def main():
    """메인 함수"""
    print("="*80)
    print("트레이너 월간 급여 집계")
    print("="*80)

    # DB 경로
    base_dir = Path(__file__).parent.parent
    db_path = base_dir / "data" / "doubless.db"

    if not db_path.exists():
        print(f"❌ DB 파일을 찾을 수 없습니다: {db_path}")
        sys.exit(1)

    # 인자 확인
    if len(sys.argv) < 3:
        print("\n사용법: python update_trainer_monthly_salary.py <년도> <월>")
        print("\n예시:")
        print("  python update_trainer_monthly_salary.py 2025 12월")
        print("  python update_trainer_monthly_salary.py 2025 11월")
        sys.exit(1)

    year = int(sys.argv[1])
    month_str = sys.argv[2]

    # 월 형식 확인
    if not month_str.endswith('월'):
        month_str = month_str + '월'

    # 집계 실행
    count = calculate_trainer_monthly_salary(db_path, year, month_str)

    if count > 0:
        print(f"\n{'='*80}")
        print(f"✅ 완료: {year}년 {month_str} 데이터가 저장되었습니다.")
        print('='*80)
        print("\n⚠️  주의: 기본급(base_salary)은 0으로 설정되었습니다.")
        print("   필요시 수동으로 업데이트하거나, 급여 규칙을 적용하세요.")
    else:
        print(f"\n❌ 처리된 데이터가 없습니다.")


if __name__ == "__main__":
    main()
