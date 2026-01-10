#!/usr/bin/env python3
"""
이준수 트레이너 8-11월 세션 검증
규칙: 이번달 잔여세션 = 지난달 잔여세션 - 이번달 진행세션
"""

import sqlite3
from pathlib import Path
from collections import defaultdict

def check_leejunsoo_anomalies():
    """이준수 트레이너 세션 이상 내역 체크"""
    base_dir = Path(__file__).parent.parent
    salary_db = base_dir / "data" / "doubless.db"

    conn = sqlite3.connect(salary_db)
    cursor = conn.cursor()

    # 월 순서 정의
    month_order = {'8월': 8, '9월': 9, '10월': 10, '11월': 11}

    # 이준수 트레이너 8-11월 데이터 조회
    query = """
    SELECT
        회원명,
        월,
        등록세션,
        총진행세션,
        남은세션,
        당월진행세션,
        당월수업료
    FROM salary_records
    WHERE 년도 = 2025
        AND 트레이너 = '이준수'
        AND 월 IN ('8월', '9월', '10월', '11월')
    ORDER BY 회원명, CASE
        WHEN 월 = '8월' THEN 1
        WHEN 월 = '9월' THEN 2
        WHEN 월 = '10월' THEN 3
        WHEN 월 = '11월' THEN 4
    END
    """

    cursor.execute(query)
    records = cursor.fetchall()
    conn.close()

    # 회원별로 그룹화
    member_records = defaultdict(list)
    for record in records:
        member, month, reg_session, total_session, remain_session, monthly_session, monthly_fee = record
        member_records[member].append({
            'member': member,
            'month': month,
            'month_num': month_order.get(month, 0),
            'reg_session': reg_session or 0,
            'total_session': total_session or 0,
            'remain_session': remain_session or 0,
            'monthly_session': monthly_session or 0,
            'monthly_fee': monthly_fee or 0
        })

    # 이상 내역 분석
    print("="*140)
    print("이준수 트레이너 8-11월 세션 검증 결과")
    print("="*140)
    print(f"\n{'회원명':<10} {'이전월':<6} {'현재월':<6} {'이전잔여':>8} {'진행':>6} {'예상잔여':>8} {'실제잔여':>8} {'차이':>6} {'등록세션변화':>12} {'문제유형':<30}")
    print("-"*140)

    anomaly_count = 0
    checked_count = 0

    for member, history in sorted(member_records.items()):
        # 월별로 정렬
        history.sort(key=lambda x: x['month_num'])

        for i in range(1, len(history)):
            prev = history[i-1]
            curr = history[i]
            checked_count += 1

            # 규칙: 이번달 잔여세션 = 지난달 잔여세션 - 이번달 진행세션
            expected_remain = prev['remain_session'] - curr['monthly_session']
            actual_remain = curr['remain_session']

            tolerance = 0.1  # 소수점 오차 허용
            diff = actual_remain - expected_remain

            if abs(diff) > tolerance:
                anomaly_count += 1

                # 문제 유형 분류
                remain_increased = actual_remain > prev['remain_session']
                session_added = curr['reg_session'] > prev['reg_session']

                if remain_increased and session_added:
                    problem_type = "✅ 등록세션 추가 (정상)"
                elif remain_increased and not session_added:
                    problem_type = "⚠️ 잔여 증가, 등록 불변"
                else:
                    problem_type = "⚠️ 계산 불일치"

                reg_change = f"{prev['reg_session']:.0f}→{curr['reg_session']:.0f}"

                print(f"{member:<10} {prev['month']:<6} {curr['month']:<6} {prev['remain_session']:>8.1f} "
                      f"{curr['monthly_session']:>6.1f} {expected_remain:>8.1f} {actual_remain:>8.1f} "
                      f"{diff:>6.1f} {reg_change:>12} {problem_type:<30}")

    print("-"*140)
    print(f"\n총 {checked_count}건 검증, {anomaly_count}건 이상")
    print("="*140)

if __name__ == "__main__":
    check_leejunsoo_anomalies()
