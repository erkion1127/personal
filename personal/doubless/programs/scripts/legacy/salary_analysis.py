#!/usr/bin/env python3
"""
급여 지급 분석 보고서 생성 및 이상 내역 체크
2025년 6월 ~ 11월 데이터 분석

검증 규칙:
1. 이번달 잔여세션 = 지난달 잔여세션 - 이번달 진행세션
2. 잔여세션이 늘어나는 경우는 수강권 PT횟수가 추가되어야 함
"""

import sqlite3
from pathlib import Path
from datetime import datetime
from collections import defaultdict

def connect_dbs():
    """데이터베이스 연결"""
    base_dir = Path(__file__).parent.parent
    salary_db = base_dir / "data" / "doubless.db"
    members_db = base_dir / "data" / "doubless.db"

    salary_conn = sqlite3.connect(salary_db)
    members_conn = sqlite3.connect(members_db)

    return salary_conn, members_conn

def check_session_anomalies(conn):
    """세션 이상 내역 체크"""
    cursor = conn.cursor()

    # 월 순서 정의
    month_order = {'6월': 6, '7월': 7, '8월': 8, '9월': 9, '10월': 10, '11월': 11}

    # 회원별, 트레이너별 월별 데이터 조회
    query = """
    SELECT
        트레이너,
        회원명,
        월,
        등록세션,
        총진행세션,
        남은세션,
        당월진행세션,
        등록비용,
        당월수업료
    FROM salary_records
    WHERE 년도 = 2025 AND 월 IN ('6월', '7월', '8월', '9월', '10월', '11월')
    ORDER BY 트레이너, 회원명, CASE
        WHEN 월 = '6월' THEN 1
        WHEN 월 = '7월' THEN 2
        WHEN 월 = '8월' THEN 3
        WHEN 월 = '9월' THEN 4
        WHEN 월 = '10월' THEN 5
        WHEN 월 = '11월' THEN 6
    END
    """

    cursor.execute(query)
    records = cursor.fetchall()

    # 회원별로 그룹화
    member_records = defaultdict(list)
    for record in records:
        trainer, member, month, reg_session, total_session, remain_session, monthly_session, reg_cost, monthly_fee = record
        key = f"{trainer}_{member}"
        member_records[key].append({
            'trainer': trainer,
            'member': member,
            'month': month,
            'month_num': month_order.get(month, 0),
            'reg_session': reg_session or 0,
            'total_session': total_session or 0,
            'remain_session': remain_session or 0,
            'monthly_session': monthly_session or 0,
            'reg_cost': reg_cost or 0,
            'monthly_fee': monthly_fee or 0
        })

    # 이상 내역 분석
    anomalies = []

    for key, history in member_records.items():
        # 월별로 정렬
        history.sort(key=lambda x: x['month_num'])

        for i in range(1, len(history)):
            prev = history[i-1]
            curr = history[i]

            # 규칙 1: 이번달 잔여세션 = 지난달 잔여세션 - 이번달 진행세션
            expected_remain = prev['remain_session'] - curr['monthly_session']
            actual_remain = curr['remain_session']

            tolerance = 0.1  # 소수점 오차 허용

            if abs(expected_remain - actual_remain) > tolerance:
                # 규칙 2: 잔여세션이 늘어난 경우 등록세션이 증가했는지 확인
                remain_increased = actual_remain > prev['remain_session']
                session_added = curr['reg_session'] > prev['reg_session']

                anomaly_type = ""
                if remain_increased and not session_added:
                    anomaly_type = "⚠️ 잔여세션 증가, 등록세션 불변"
                elif remain_increased and session_added:
                    anomaly_type = "✅ 잔여세션 증가, 등록세션 추가 (정상)"
                else:
                    anomaly_type = "⚠️ 세션 계산 불일치"

                anomalies.append({
                    'trainer': curr['trainer'],
                    'member': curr['member'],
                    'prev_month': prev['month'],
                    'curr_month': curr['month'],
                    'prev_remain': prev['remain_session'],
                    'curr_monthly': curr['monthly_session'],
                    'expected_remain': expected_remain,
                    'actual_remain': actual_remain,
                    'diff': actual_remain - expected_remain,
                    'prev_reg': prev['reg_session'],
                    'curr_reg': curr['reg_session'],
                    'type': anomaly_type
                })

    return anomalies

def check_negative_values(conn):
    """음수 값 체크"""
    cursor = conn.cursor()

    query = """
    SELECT
        트레이너,
        회원명,
        월,
        남은세션,
        당월진행세션,
        당월수업료,
        등록비용
    FROM salary_records
    WHERE 년도 = 2025 AND 월 IN ('6월', '7월', '8월', '9월', '10월', '11월')
        AND (남은세션 < 0 OR 당월진행세션 < 0 OR 당월수업료 < 0 OR 등록비용 < 0)
    ORDER BY 월, 트레이너, 회원명
    """

    cursor.execute(query)
    return cursor.fetchall()

def check_zero_session_with_fee(conn):
    """세션 0회인데 수업료가 있는 경우 체크"""
    cursor = conn.cursor()

    query = """
    SELECT
        트레이너,
        회원명,
        월,
        당월진행세션,
        당월수업료
    FROM salary_records
    WHERE 년도 = 2025 AND 월 IN ('6월', '7월', '8월', '9월', '10월', '11월')
        AND (당월진행세션 = 0 OR 당월진행세션 IS NULL)
        AND 당월수업료 > 0
    ORDER BY 월, 트레이너, 회원명
    """

    cursor.execute(query)
    return cursor.fetchall()

def analyze_monthly_summary(conn):
    """월별 요약"""
    cursor = conn.cursor()

    query = """
    SELECT
        월,
        COUNT(DISTINCT 트레이너) as 트레이너수,
        COUNT(DISTINCT 회원명) as 회원수,
        COUNT(*) as 총건수,
        SUM(당월진행세션) as 총진행세션,
        SUM(당월수업료) as 총수업료,
        SUM(이달의매출) as 총매출,
        AVG(당월수업료) as 평균수업료
    FROM salary_records
    WHERE 년도 = 2025 AND 월 IN ('6월', '7월', '8월', '9월', '10월', '11월')
    GROUP BY 월
    ORDER BY CASE
        WHEN 월 = '6월' THEN 1
        WHEN 월 = '7월' THEN 2
        WHEN 월 = '8월' THEN 3
        WHEN 월 = '9월' THEN 4
        WHEN 월 = '10월' THEN 5
        WHEN 월 = '11월' THEN 6
    END
    """

    cursor.execute(query)
    return cursor.fetchall()

def analyze_trainer_summary(conn):
    """트레이너별 요약"""
    cursor = conn.cursor()

    query = """
    SELECT
        트레이너,
        COUNT(DISTINCT 회원명) as 담당회원수,
        SUM(당월진행세션) as 총진행세션,
        SUM(당월수업료) as 총수업료,
        SUM(이달의매출) as 총매출,
        AVG(당월수업료) as 평균수업료
    FROM salary_records
    WHERE 년도 = 2025 AND 월 IN ('6월', '7월', '8월', '9월', '10월', '11월')
    GROUP BY 트레이너
    ORDER BY 총수업료 DESC
    """

    cursor.execute(query)
    return cursor.fetchall()

def generate_report(salary_conn, members_conn, output_file=None):
    """보고서 생성"""
    # 출력 대상 결정
    if output_file:
        import sys
        original_stdout = sys.stdout
        sys.stdout = open(output_file, 'w', encoding='utf-8')

    print("="*120)
    print("급여 지급 분석 및 이상 내역 체크 보고서 (2025년 6월 ~ 11월)")
    print("="*120)
    print(f"생성일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # ========== 이상 내역 체크 ==========
    print("\n" + "="*120)
    print("[ 이상 내역 체크 ]")
    print("="*120)

    # 1. 세션 이상 내역
    print("\n1. 세션 계산 이상 내역")
    print("-"*120)
    anomalies = check_session_anomalies(salary_conn)

    if anomalies:
        print(f"{'트레이너':<12} {'회원명':<12} {'이전월':<8} {'현재월':<8} {'이전잔여':>10} {'진행':>8} {'예상잔여':>10} {'실제잔여':>10} {'차이':>8} {'유형':<30}")
        print("-"*120)

        warning_count = 0
        for anomaly in anomalies:
            if "⚠️" in anomaly['type']:
                warning_count += 1
                print(f"{anomaly['trainer']:<12} {anomaly['member']:<12} {anomaly['prev_month']:<8} {anomaly['curr_month']:<8} "
                      f"{anomaly['prev_remain']:>10.1f} {anomaly['curr_monthly']:>8.1f} {anomaly['expected_remain']:>10.1f} "
                      f"{anomaly['actual_remain']:>10.1f} {anomaly['diff']:>8.1f} {anomaly['type']:<30}")

        print(f"\n총 {len(anomalies)}건 중 경고 {warning_count}건")
    else:
        print("✅ 이상 내역 없음")

    # 2. 음수 값 체크
    print("\n2. 음수 값 이상 내역")
    print("-"*120)
    negative_records = check_negative_values(salary_conn)

    if negative_records:
        print(f"{'트레이너':<12} {'회원명':<12} {'월':<8} {'남은세션':>10} {'진행세션':>10} {'수업료':>12} {'등록비용':>12}")
        print("-"*120)

        for record in negative_records:
            trainer, member, month, remain, monthly, fee, reg_cost = record
            print(f"{trainer:<12} {member:<12} {month:<8} {remain or 0:>10.1f} {monthly or 0:>10.1f} "
                  f"{fee or 0:>12,.0f} {reg_cost or 0:>12,.0f}")

        print(f"\n총 {len(negative_records)}건의 음수 값 발견")
    else:
        print("✅ 음수 값 없음")

    # 3. 세션 0회인데 수업료 발생
    print("\n3. 세션 0회인데 수업료 발생 내역")
    print("-"*120)
    zero_session_records = check_zero_session_with_fee(salary_conn)

    if zero_session_records:
        print(f"{'트레이너':<12} {'회원명':<12} {'월':<8} {'진행세션':>10} {'수업료':>12}")
        print("-"*120)

        for record in zero_session_records:
            trainer, member, month, session, fee = record
            print(f"{trainer:<12} {member:<12} {month:<8} {session or 0:>10.1f} {fee or 0:>12,.0f}")

        print(f"\n총 {len(zero_session_records)}건 발견")
    else:
        print("✅ 이상 내역 없음")

    # ========== 통계 분석 ==========
    print("\n\n" + "="*120)
    print("[ 통계 분석 ]")
    print("="*120)

    # 월별 요약
    print("\n1. 월별 급여 지급 현황")
    print("-"*120)
    monthly_data = analyze_monthly_summary(salary_conn)

    print(f"{'월':<8} {'트레이너':>10} {'회원수':>10} {'총건수':>10} {'진행세션':>12} {'총수업료(원)':>15} {'총매출(원)':>15} {'평균수업료':>12}")
    print("-"*120)

    total_sessions = 0
    total_fee = 0
    total_revenue = 0

    for row in monthly_data:
        month, trainers, members, count, sessions, fee, revenue, avg_fee = row
        total_sessions += sessions or 0
        total_fee += fee or 0
        total_revenue += revenue or 0
        print(f"{month:<8} {trainers:>10} {members:>10} {count:>10} {sessions or 0:>12,.1f} "
              f"{fee or 0:>15,.0f} {revenue or 0:>15,.0f} {avg_fee or 0:>12,.0f}")

    print("-"*120)
    print(f"{'합계':<8} {'':>10} {'':>10} {'':>10} {total_sessions:>12,.1f} {total_fee:>15,.0f} {total_revenue:>15,.0f} {'':<12}")

    # 트레이너별 요약
    print("\n2. 트레이너별 실적 현황 (상위 15명)")
    print("-"*120)
    trainer_data = analyze_trainer_summary(salary_conn)

    print(f"{'트레이너':<15} {'담당회원':>10} {'진행세션':>12} {'총수업료(원)':>15} {'총매출(원)':>15} {'평균수업료':>12}")
    print("-"*120)

    for row in trainer_data[:15]:
        trainer, members, sessions, fee, revenue, avg_fee = row
        print(f"{trainer:<15} {members:>10} {sessions or 0:>12,.1f} {fee or 0:>15,.0f} "
              f"{revenue or 0:>15,.0f} {avg_fee or 0:>12,.0f}")

    # 종합 요약
    print("\n" + "="*120)
    print("[ 종합 요약 ]")
    print("="*120)

    cursor = salary_conn.cursor()
    cursor.execute("""
        SELECT
            COUNT(DISTINCT 트레이너) as 총트레이너수,
            COUNT(DISTINCT 회원명) as 총회원수,
            SUM(당월진행세션) as 총진행세션,
            SUM(당월수업료) as 총지급액,
            SUM(이달의매출) as 총매출
        FROM salary_records
        WHERE 년도 = 2025 AND 월 IN ('6월', '7월', '8월', '9월', '10월', '11월')
    """)

    summary = cursor.fetchone()
    trainers, members, sessions, total_salary, total_rev = summary

    print(f"분석 기간: 2025년 6월 ~ 11월 (6개월)")
    print(f"총 트레이너 수: {trainers}명")
    print(f"총 회원 수: {members}명")
    print(f"총 진행 세션: {sessions or 0:,.1f}회")
    print(f"총 지급액: {total_salary or 0:,.0f}원")
    print(f"총 매출: {total_rev or 0:,.0f}원")
    print(f"월 평균 지급액: {(total_salary or 0) / 6:,.0f}원")
    print(f"월 평균 매출: {(total_rev or 0) / 6:,.0f}원")

    # 회원권/수강권 현황
    cursor = members_conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM lesson_tickets")
    lesson_tickets_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM tickets")
    tickets_count = cursor.fetchone()[0]

    print(f"\n현재 수강권 등록: {lesson_tickets_count}건")
    print(f"현재 회원권 등록: {tickets_count}건")

    print("\n" + "="*120)
    print("보고서 생성 완료")
    print("="*120)

    # 파일로 출력했다면 원래대로 복원
    if output_file:
        import sys
        sys.stdout.close()
        sys.stdout = original_stdout
        print(f"\n✅ 보고서가 저장되었습니다: {output_file}")

def main():
    salary_conn, members_conn = connect_dbs()

    try:
        # 보고서 출력 파일 경로 설정
        base_dir = Path(__file__).parent.parent
        report_dir = base_dir / "pay" / "report"
        report_dir.mkdir(parents=True, exist_ok=True)

        report_file = report_dir / f"급여분석보고서_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

        # 보고서 생성
        generate_report(salary_conn, members_conn, output_file=report_file)
    finally:
        salary_conn.close()
        members_conn.close()

if __name__ == "__main__":
    main()
