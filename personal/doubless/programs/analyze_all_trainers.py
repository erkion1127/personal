#!/usr/bin/env python3
"""
전체 트레이너 급여 지급 내역 분석 (2025년 8-11월)

검증 규칙:
1. 이번달 잔여세션 = 지난달 잔여세션 - 이번달 진행세션
2. 이번달 잔여세션이 늘어나는 경우는 PT 수강권을 체크해서 비교하여야 한다
3. 이번달 수업은 회원권 만료가 이번달인 경우엔 문제삼지 않는다
4. 이상 케이스를 구분하여 리스트를 만들어야 한다
5. 이상 케이스마다 트레이너별로 리포트가 나와야 한다
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

def get_suganggwon_info(members_conn, member_name):
    """수강권 정보 조회"""
    cursor = members_conn.cursor()
    cursor.execute("""
        SELECT jglesson_ticket_type, jglesson_ticket_origin_count,
               jglesson_ticket_count, jglesson_ticket_started_dttm,
               jglesson_ticket_closed_dttm
        FROM lesson_tickets
        WHERE jgjm_member_name = ?
        ORDER BY jglesson_ticket_started_dttm DESC
        LIMIT 1
    """, (member_name,))

    result = cursor.fetchone()
    if result:
        return {
            'name': result[0],
            'total': result[1],
            'remain': result[2],
            'start': result[3],
            'end': result[4]
        }
    return None

def get_hoewongwon_info(members_conn, member_name):
    """회원권 정보 조회"""
    cursor = members_conn.cursor()
    cursor.execute("""
        SELECT jtd_name, jtd_closed_dttm, ticket_status
        FROM tickets
        WHERE jgjm_member_name = ?
        ORDER BY jtd_started_dttm DESC
        LIMIT 1
    """, (member_name,))

    result = cursor.fetchone()
    if result:
        return {
            'name': result[0],
            'end': result[1],
            'status': result[2]
        }
    return None

def analyze_all_trainers(salary_conn, members_conn):
    """전체 트레이너 분석"""
    cursor = salary_conn.cursor()

    # 월 순서 정의
    month_order = {'8월': 8, '9월': 9, '10월': 10, '11월': 11}

    # 전체 트레이너 8-11월 데이터 조회
    query = """
    SELECT
        트레이너,
        회원명,
        월,
        등록세션,
        총진행세션,
        남은세션,
        당월진행세션,
        당월수업료
    FROM salary_records
    WHERE 년도 = 2025
        AND 월 IN ('8월', '9월', '10월', '11월')
    ORDER BY 트레이너, 회원명, CASE
        WHEN 월 = '8월' THEN 1
        WHEN 월 = '9월' THEN 2
        WHEN 월 = '10월' THEN 3
        WHEN 월 = '11월' THEN 4
    END
    """

    cursor.execute(query)
    records = cursor.fetchall()

    # 트레이너별, 회원별로 그룹화
    trainer_data = defaultdict(lambda: defaultdict(list))

    for record in records:
        trainer, member, month, reg_session, total_session, remain_session, monthly_session, monthly_fee = record
        trainer_data[trainer][member].append({
            'trainer': trainer,
            'member': member,
            'month': month,
            'month_num': month_order.get(month, 0),
            'reg_session': reg_session or 0,
            'total_session': total_session or 0,
            'remain_session': remain_session or 0,
            'monthly_session': monthly_session or 0,
            'monthly_fee': monthly_fee or 0
        })

    # 이상 케이스 분류
    anomalies_by_type = {
        'TYPE1_잔여증가_등록불변': [],  # 잔여세션 증가했는데 등록세션 불변
        'TYPE2_잔여증가_등록증가': [],  # 잔여세션 증가, 등록세션 증가 (수강권 추가)
        'TYPE3_계산불일치': [],          # 계산 불일치
    }

    # 전체 분석
    total_checked = 0
    total_anomalies = 0

    for trainer in sorted(trainer_data.keys()):
        for member, history in sorted(trainer_data[trainer].items()):
            history.sort(key=lambda x: x['month_num'])

            for i in range(1, len(history)):
                prev = history[i-1]
                curr = history[i]
                total_checked += 1

                # 규칙 1: 이번달 잔여세션 = 지난달 잔여세션 - 이번달 진행세션
                expected_remain = prev['remain_session'] - curr['monthly_session']
                actual_remain = curr['remain_session']

                tolerance = 0.1
                diff = actual_remain - expected_remain

                if abs(diff) > tolerance:
                    total_anomalies += 1

                    # 수강권 정보 조회
                    suganggwon = get_suganggwon_info(members_conn, member)
                    hoewongwon = get_hoewongwon_info(members_conn, member)

                    anomaly = {
                        'trainer': trainer,
                        'member': member,
                        'prev_month': prev['month'],
                        'curr_month': curr['month'],
                        'prev_remain': prev['remain_session'],
                        'curr_monthly': curr['monthly_session'],
                        'expected_remain': expected_remain,
                        'actual_remain': actual_remain,
                        'diff': diff,
                        'prev_reg': prev['reg_session'],
                        'curr_reg': curr['reg_session'],
                        'suganggwon': suganggwon,
                        'hoewongwon': hoewongwon
                    }

                    # 이상 케이스 분류
                    remain_increased = actual_remain > prev['remain_session']
                    session_added = curr['reg_session'] > prev['reg_session']

                    if remain_increased and session_added:
                        anomalies_by_type['TYPE2_잔여증가_등록증가'].append(anomaly)
                    elif remain_increased and not session_added:
                        anomalies_by_type['TYPE1_잔여증가_등록불변'].append(anomaly)
                    else:
                        anomalies_by_type['TYPE3_계산불일치'].append(anomaly)

    return anomalies_by_type, total_checked, total_anomalies

def generate_report(salary_conn, members_conn, output_file=None):
    """보고서 생성"""
    if output_file:
        import sys
        original_stdout = sys.stdout
        sys.stdout = open(output_file, 'w', encoding='utf-8')

    print("="*160)
    print("전체 트레이너 급여 지급 내역 분석 보고서 (2025년 8-11월)")
    print("="*160)
    print(f"생성일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\n검증 규칙:")
    print(f"1. 이번달 잔여세션 = 지난달 잔여세션 - 이번달 진행세션")
    print(f"2. 이번달 잔여세션이 늘어나는 경우는 PT 수강권을 체크해서 비교")
    print(f"3. 이번달 수업은 회원권 만료가 이번달인 경우엔 문제삼지 않음")
    print(f"4. 이상 케이스를 구분하여 리스트 생성")
    print(f"5. 이상 케이스마다 트레이너별로 리포트 생성\n")

    anomalies_by_type, total_checked, total_anomalies = analyze_all_trainers(salary_conn, members_conn)

    # 전체 요약
    print("\n" + "="*160)
    print("[ 전체 요약 ]")
    print("="*160)
    print(f"총 검증 건수: {total_checked}건")
    print(f"총 이상 건수: {total_anomalies}건 ({total_anomalies/total_checked*100:.1f}%)")
    print(f"\n이상 케이스별 분류:")
    print(f"  TYPE1 - 잔여세션 증가, 등록세션 불변: {len(anomalies_by_type['TYPE1_잔여증가_등록불변'])}건 ⚠️")
    print(f"  TYPE2 - 잔여세션 증가, 등록세션 증가: {len(anomalies_by_type['TYPE2_잔여증가_등록증가'])}건 (수강권 추가)")
    print(f"  TYPE3 - 계산 불일치: {len(anomalies_by_type['TYPE3_계산불일치'])}건 ⚠️")

    # TYPE1: 잔여세션 증가, 등록세션 불변 (가장 심각)
    print("\n\n" + "="*160)
    print("[ TYPE1: 잔여세션 증가, 등록세션 불변 ] ⚠️⚠️⚠️")
    print("="*160)
    print("이 케이스는 등록세션이 증가하지 않았는데 잔여세션이 늘어난 경우로, 수강권 추가 확인이 필요합니다.\n")

    if anomalies_by_type['TYPE1_잔여증가_등록불변']:
        # 트레이너별로 그룹화
        by_trainer = defaultdict(list)
        for anomaly in anomalies_by_type['TYPE1_잔여증가_등록불변']:
            by_trainer[anomaly['trainer']].append(anomaly)

        for trainer in sorted(by_trainer.keys()):
            print(f"\n[트레이너: {trainer}] - {len(by_trainer[trainer])}건")
            print("-"*160)
            print(f"{'회원명':<10} {'이전월':<6} {'현재월':<6} {'이전잔여':>8} {'진행':>6} {'예상잔여':>8} {'실제잔여':>8} "
                  f"{'차이':>6} {'등록세션':>10} {'현재수강권':<20} {'잔여':<8} {'회원권종료':<12}")
            print("-"*160)

            for a in by_trainer[trainer]:
                sg_info = f"{a['suganggwon']['name'][:18]}" if a['suganggwon'] else "-"
                sg_remain = f"{a['suganggwon']['remain']}" if a['suganggwon'] else "-"
                hw_end = f"{a['hoewongwon']['end']}" if a['hoewongwon'] else "-"

                print(f"{a['member']:<10} {a['prev_month']:<6} {a['curr_month']:<6} {a['prev_remain']:>8.1f} "
                      f"{a['curr_monthly']:>6.1f} {a['expected_remain']:>8.1f} {a['actual_remain']:>8.1f} "
                      f"{a['diff']:>6.1f} {a['prev_reg']:.0f}→{a['curr_reg']:.0f}   {sg_info:<20} {sg_remain:<8} {hw_end:<12}")
    else:
        print("✅ 이상 없음")

    # TYPE2: 잔여세션 증가, 등록세션 증가 (정상)
    print("\n\n" + "="*160)
    print("[ TYPE2: 잔여세션 증가, 등록세션 증가 ] ✅")
    print("="*160)
    print("이 케이스는 수강권을 추가 구매한 정상 케이스입니다.\n")

    if anomalies_by_type['TYPE2_잔여증가_등록증가']:
        by_trainer = defaultdict(list)
        for anomaly in anomalies_by_type['TYPE2_잔여증가_등록증가']:
            by_trainer[anomaly['trainer']].append(anomaly)

        for trainer in sorted(by_trainer.keys()):
            print(f"\n[트레이너: {trainer}] - {len(by_trainer[trainer])}건")
            print("-"*160)
            print(f"{'회원명':<10} {'이전월':<6} {'현재월':<6} {'이전잔여':>8} {'진행':>6} {'예상잔여':>8} {'실제잔여':>8} "
                  f"{'차이':>6} {'등록세션':>10} {'현재수강권':<20}")
            print("-"*160)

            for a in by_trainer[trainer]:
                sg_info = f"{a['suganggwon']['name'][:18]}" if a['suganggwon'] else "-"

                print(f"{a['member']:<10} {a['prev_month']:<6} {a['curr_month']:<6} {a['prev_remain']:>8.1f} "
                      f"{a['curr_monthly']:>6.1f} {a['expected_remain']:>8.1f} {a['actual_remain']:>8.1f} "
                      f"{a['diff']:>6.1f} {a['prev_reg']:.0f}→{a['curr_reg']:.0f}   {sg_info:<20}")
    else:
        print("해당 케이스 없음")

    # TYPE3: 계산 불일치
    print("\n\n" + "="*160)
    print("[ TYPE3: 계산 불일치 ] ⚠️")
    print("="*160)
    print("이 케이스는 등록세션이 변하지 않았지만 계산이 맞지 않는 경우입니다.\n")

    if anomalies_by_type['TYPE3_계산불일치']:
        by_trainer = defaultdict(list)
        for anomaly in anomalies_by_type['TYPE3_계산불일치']:
            by_trainer[anomaly['trainer']].append(anomaly)

        for trainer in sorted(by_trainer.keys()):
            print(f"\n[트레이너: {trainer}] - {len(by_trainer[trainer])}건")
            print("-"*160)
            print(f"{'회원명':<10} {'이전월':<6} {'현재월':<6} {'이전잔여':>8} {'진행':>6} {'예상잔여':>8} {'실제잔여':>8} "
                  f"{'차이':>6} {'등록세션':>10} {'현재수강권':<20} {'잔여':<8}")
            print("-"*160)

            for a in by_trainer[trainer]:
                sg_info = f"{a['suganggwon']['name'][:18]}" if a['suganggwon'] else "-"
                sg_remain = f"{a['suganggwon']['remain']}" if a['suganggwon'] else "-"

                print(f"{a['member']:<10} {a['prev_month']:<6} {a['curr_month']:<6} {a['prev_remain']:>8.1f} "
                      f"{a['curr_monthly']:>6.1f} {a['expected_remain']:>8.1f} {a['actual_remain']:>8.1f} "
                      f"{a['diff']:>6.1f} {a['prev_reg']:.0f}→{a['curr_reg']:.0f}   {sg_info:<20} {sg_remain:<8}")
    else:
        print("✅ 이상 없음")

    # 트레이너별 통계
    print("\n\n" + "="*160)
    print("[ 트레이너별 이상 건수 통계 ]")
    print("="*160)

    trainer_stats = defaultdict(lambda: {'TYPE1': 0, 'TYPE2': 0, 'TYPE3': 0, 'total': 0})

    for anomaly in anomalies_by_type['TYPE1_잔여증가_등록불변']:
        trainer_stats[anomaly['trainer']]['TYPE1'] += 1
        trainer_stats[anomaly['trainer']]['total'] += 1

    for anomaly in anomalies_by_type['TYPE2_잔여증가_등록증가']:
        trainer_stats[anomaly['trainer']]['TYPE2'] += 1
        trainer_stats[anomaly['trainer']]['total'] += 1

    for anomaly in anomalies_by_type['TYPE3_계산불일치']:
        trainer_stats[anomaly['trainer']]['TYPE3'] += 1
        trainer_stats[anomaly['trainer']]['total'] += 1

    print(f"{'트레이너':<15} {'TYPE1(⚠️)':>10} {'TYPE2(✅)':>10} {'TYPE3(⚠️)':>10} {'합계':>10}")
    print("-"*160)
    for trainer in sorted(trainer_stats.keys()):
        stats = trainer_stats[trainer]
        print(f"{trainer:<15} {stats['TYPE1']:>10} {stats['TYPE2']:>10} {stats['TYPE3']:>10} {stats['total']:>10}")

    print("\n" + "="*160)
    print("보고서 생성 완료")
    print("="*160)

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

        report_file = report_dir / f"전체트레이너분석_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

        # 보고서 생성
        generate_report(salary_conn, members_conn, output_file=report_file)
    finally:
        salary_conn.close()
        members_conn.close()

if __name__ == "__main__":
    main()
