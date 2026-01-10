#!/usr/bin/env python3
"""
월별 급여 지급 분석 프로그램

급여 데이터를 월별로 분석하여 다음 정보를 제공:
1. 월별 전체 통계 (트레이너 수, 회원 수, 총 급여액 등)
2. 월별 트레이너 실적 분석
3. 회원별 급여 추이 분석
4. 이상 케이스 탐지 (급여 규칙 검증)
"""

import sqlite3
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import sys
import shutil
import json

class MonthlySalaryAnalyzer:
    """월별 급여 분석"""

    def __init__(self, salary_db_path, members_db_path):
        self.salary_db_path = salary_db_path
        self.members_db_path = members_db_path
        self.salary_conn = None
        self.members_conn = None

    def connect(self):
        """DB 연결"""
        self.salary_conn = sqlite3.connect(self.salary_db_path)
        self.salary_conn.row_factory = sqlite3.Row
        self.members_conn = sqlite3.connect(self.members_db_path)
        self.members_conn.row_factory = sqlite3.Row

    def close(self):
        """DB 연결 종료"""
        if self.salary_conn:
            self.salary_conn.close()
        if self.members_conn:
            self.members_conn.close()

    def get_month_order(self, month_str):
        """월 문자열을 숫자로 변환"""
        month_map = {
            '1월': 1, '2월': 2, '3월': 3, '4월': 4,
            '5월': 5, '6월': 6, '7월': 7, '8월': 8,
            '9월': 9, '10월': 10, '11월': 11, '12월': 12
        }
        return month_map.get(month_str, 0)

    def get_available_months(self, year=2025):
        """사용 가능한 월 목록 조회"""
        cursor = self.salary_conn.cursor()
        cursor.execute("""
            SELECT DISTINCT 년도, 월
            FROM salary_records
            WHERE 년도 = ?
            ORDER BY 년도,
                CASE 월
                    WHEN '1월' THEN 1 WHEN '2월' THEN 2 WHEN '3월' THEN 3
                    WHEN '4월' THEN 4 WHEN '5월' THEN 5 WHEN '6월' THEN 6
                    WHEN '7월' THEN 7 WHEN '8월' THEN 8 WHEN '9월' THEN 9
                    WHEN '10월' THEN 10 WHEN '11월' THEN 11 WHEN '12월' THEN 12
                END
        """, (year,))
        return [(row[0], row[1]) for row in cursor.fetchall()]

    def analyze_monthly_overview(self, year=2025):
        """월별 전체 개요 분석"""
        cursor = self.salary_conn.cursor()

        query = """
            SELECT
                월,
                COUNT(DISTINCT 트레이너) as 트레이너수,
                COUNT(DISTINCT 회원명) as 회원수,
                COUNT(*) as 총건수,
                SUM(당월진행세션) as 총진행세션,
                SUM(당월수업료) as 총수업료,
                SUM(이달의매출) as 총매출,
                AVG(당월수업료) as 평균수업료,
                MIN(당월수업료) as 최소수업료,
                MAX(당월수업료) as 최대수업료
            FROM salary_records
            WHERE 년도 = ?
            GROUP BY 월
            ORDER BY CASE 월
                WHEN '1월' THEN 1 WHEN '2월' THEN 2 WHEN '3월' THEN 3
                WHEN '4월' THEN 4 WHEN '5월' THEN 5 WHEN '6월' THEN 6
                WHEN '7월' THEN 7 WHEN '8월' THEN 8 WHEN '9월' THEN 9
                WHEN '10월' THEN 10 WHEN '11월' THEN 11 WHEN '12월' THEN 12
            END
        """

        cursor.execute(query, (year,))
        return cursor.fetchall()

    def analyze_trainer_by_month(self, year=2025, month=None):
        """월별 트레이너 실적 분석"""
        cursor = self.salary_conn.cursor()

        if month:
            query = """
                SELECT
                    트레이너,
                    월,
                    COUNT(DISTINCT 회원명) as 담당회원수,
                    SUM(당월진행세션) as 총진행세션,
                    SUM(당월수업료) as 총수업료,
                    SUM(이달의매출) as 총매출,
                    AVG(당월수업료) as 평균수업료,
                    AVG(당월진행세션) as 평균진행세션
                FROM salary_records
                WHERE 년도 = ? AND 월 = ?
                GROUP BY 트레이너, 월
                ORDER BY 총수업료 DESC
            """
            cursor.execute(query, (year, month))
        else:
            query = """
                SELECT
                    트레이너,
                    월,
                    COUNT(DISTINCT 회원명) as 담당회원수,
                    SUM(당월진행세션) as 총진행세션,
                    SUM(당월수업료) as 총수업료,
                    SUM(이달의매출) as 총매출,
                    AVG(당월수업료) as 평균수업료,
                    AVG(당월진행세션) as 평균진행세션
                FROM salary_records
                WHERE 년도 = ?
                GROUP BY 트레이너, 월
                ORDER BY 월, 총수업료 DESC
            """
            cursor.execute(query, (year,))

        return cursor.fetchall()

    def analyze_member_monthly_trend(self, member_name, year=2025):
        """특정 회원의 월별 추이 분석"""
        cursor = self.salary_conn.cursor()

        query = """
            SELECT
                월,
                트레이너,
                등록세션,
                총진행세션,
                남은세션,
                당월진행세션,
                당월수업료,
                이달의매출
            FROM salary_records
            WHERE 년도 = ? AND 회원명 = ?
            ORDER BY CASE 월
                WHEN '1월' THEN 1 WHEN '2월' THEN 2 WHEN '3월' THEN 3
                WHEN '4월' THEN 4 WHEN '5월' THEN 5 WHEN '6월' THEN 6
                WHEN '7월' THEN 7 WHEN '8월' THEN 8 WHEN '9월' THEN 9
                WHEN '10월' THEN 10 WHEN '11월' THEN 11 WHEN '12월' THEN 12
            END
        """

        cursor.execute(query, (year, member_name))
        return cursor.fetchall()

    def check_session_anomalies_by_month(self, year=2025, month=None):
        """월별 세션 이상 케이스 탐지

        규칙 1: 이번달 잔여세션 = 지난달 잔여세션 - 이번달 진행세션
        규칙 2: 잔여세션이 늘어나는 경우 등록세션 증가 확인
        """
        cursor = self.salary_conn.cursor()

        # 월별로 데이터 조회
        if month:
            months = [month]
        else:
            available_months = self.get_available_months(year)
            months = [m[1] for m in available_months]

        # 회원별, 트레이너별 월별 데이터
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
            WHERE 년도 = ?
            ORDER BY 트레이너, 회원명, CASE 월
                WHEN '1월' THEN 1 WHEN '2월' THEN 2 WHEN '3월' THEN 3
                WHEN '4월' THEN 4 WHEN '5월' THEN 5 WHEN '6월' THEN 6
                WHEN '7월' THEN 7 WHEN '8월' THEN 8 WHEN '9월' THEN 9
                WHEN '10월' THEN 10 WHEN '11월' THEN 11 WHEN '12월' THEN 12
            END
        """

        cursor.execute(query, (year,))
        records = cursor.fetchall()

        # 회원별로 그룹화
        member_records = defaultdict(list)
        for record in records:
            key = f"{record['트레이너']}_{record['회원명']}"
            member_records[key].append(dict(record))

        # 이상 케이스 탐지
        anomalies = []
        for key, history in member_records.items():
            history.sort(key=lambda x: self.get_month_order(x['월']))

            for i in range(1, len(history)):
                prev = history[i-1]
                curr = history[i]

                # 규칙 1: 이번달 잔여세션 = 지난달 잔여세션 - 이번달 진행세션
                expected_remain = (prev['남은세션'] or 0) - (curr['당월진행세션'] or 0)
                actual_remain = curr['남은세션'] or 0

                tolerance = 0.1
                diff = actual_remain - expected_remain

                if abs(diff) > tolerance:
                    # 규칙 2: 잔여세션 증가 시 등록세션 확인
                    remain_increased = actual_remain > (prev['남은세션'] or 0)
                    session_added = (curr['등록세션'] or 0) > (prev['등록세션'] or 0)

                    anomaly_type = ""
                    if remain_increased and session_added:
                        anomaly_type = "✅ 잔여증가+등록증가 (정상)"
                    elif remain_increased and not session_added:
                        anomaly_type = "⚠️ 잔여증가+등록불변"
                    else:
                        anomaly_type = "⚠️ 계산불일치"

                    anomalies.append({
                        'trainer': curr['트레이너'],
                        'member': curr['회원명'],
                        'prev_month': prev['월'],
                        'curr_month': curr['월'],
                        'prev_remain': prev['남은세션'] or 0,
                        'curr_monthly': curr['당월진행세션'] or 0,
                        'expected_remain': expected_remain,
                        'actual_remain': actual_remain,
                        'diff': diff,
                        'prev_reg': prev['등록세션'] or 0,
                        'curr_reg': curr['등록세션'] or 0,
                        'type': anomaly_type
                    })

        return anomalies

    def generate_single_month_report(self, year, month, output_file=None):
        """특정 월의 급여 지급 보고서 생성"""
        if output_file:
            original_stdout = sys.stdout
            sys.stdout = open(output_file, 'w', encoding='utf-8')

        print("="*120)
        print(f"{year}년 {month} 급여 지급 분석 보고서")
        print("="*120)
        print(f"생성일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        cursor = self.salary_conn.cursor()

        # 1. 월 개요
        print("\n" + "="*120)
        print(f"[ 1. {month} 개요 ]")
        print("="*120)

        cursor.execute("""
            SELECT
                COUNT(DISTINCT 트레이너) as 트레이너수,
                COUNT(DISTINCT 회원명) as 회원수,
                COUNT(*) as 총건수,
                SUM(당월진행세션) as 총진행세션,
                SUM(당월수업료) as 총수업료,
                SUM(이달의매출) as 총매출,
                AVG(당월수업료) as 평균수업료
            FROM salary_records
            WHERE 년도 = ? AND 월 = ?
        """, (year, month))

        overview = cursor.fetchone()

        print(f"\n트레이너 수: {overview['트레이너수']}명")
        print(f"회원 수: {overview['회원수']}명")
        print(f"총 건수: {overview['총건수']}건")
        print(f"총 진행 세션: {overview['총진행세션'] or 0:,.1f}회")
        print(f"총 수업료: {overview['총수업료'] or 0:,.0f}원")
        print(f"총 매출: {overview['총매출'] or 0:,.0f}원")
        print(f"평균 수업료: {overview['평균수업료'] or 0:,.0f}원")

        # 2. 트레이너별 실적
        print("\n\n" + "="*120)
        print(f"[ 2. {month} 트레이너별 실적 ]")
        print("="*120)

        trainer_stats = self.analyze_trainer_by_month(year, month)

        print(f"\n{'트레이너':<12} {'회원수':>8} {'진행세션':>12} {'총수업료(원)':>15} "
              f"{'총매출(원)':>15} {'평균수업료':>12} {'평균세션':>10}")
        print("-"*120)

        for row in trainer_stats:
            print(f"{row['트레이너']:<12} {row['담당회원수']:>8} {row['총진행세션'] or 0:>12,.1f} "
                  f"{row['총수업료'] or 0:>15,.0f} {row['총매출'] or 0:>15,.0f} "
                  f"{row['평균수업료'] or 0:>12,.0f} {row['평균진행세션'] or 0:>10,.1f}")

        # 3. 세션 이상 케이스 (해당 월에 발생한 것만)
        print("\n\n" + "="*120)
        print(f"[ 3. {month} 세션 이상 케이스 ]")
        print("="*120)

        all_anomalies = self.check_session_anomalies_by_month(year)
        month_anomalies = [a for a in all_anomalies if a['curr_month'] == month]

        if month_anomalies:
            by_type = defaultdict(list)
            for anomaly in month_anomalies:
                by_type[anomaly['type']].append(anomaly)

            for anomaly_type in ['⚠️ 잔여증가+등록불변', '⚠️ 계산불일치', '✅ 잔여증가+등록증가 (정상)']:
                if anomaly_type in by_type:
                    print(f"\n▶ {anomaly_type} ({len(by_type[anomaly_type])}건)")
                    print("-"*120)
                    print(f"{'트레이너':<10} {'회원명':<10} {'이전월':<6} "
                          f"{'이전잔여':>8} {'진행':>6} {'예상잔여':>8} {'실제잔여':>8} {'차이':>6}")
                    print("-"*120)

                    for a in by_type[anomaly_type]:
                        print(f"{a['trainer']:<10} {a['member']:<10} {a['prev_month']:<6} "
                              f"{a['prev_remain']:>8.1f} {a['curr_monthly']:>6.1f} "
                              f"{a['expected_remain']:>8.1f} {a['actual_remain']:>8.1f} {a['diff']:>6.1f}")
        else:
            print("\n✅ 이상 케이스 없음")

        print("\n" + "="*120)
        print("보고서 생성 완료")
        print("="*120)

        if output_file:
            sys.stdout.close()
            sys.stdout = original_stdout

        return {
            'month': month,
            'trainers': overview['트레이너수'],
            'members': overview['회원수'],
            'total_sessions': overview['총진행세션'] or 0,
            'total_salary': overview['총수업료'] or 0,
            'total_revenue': overview['총매출'] or 0,
            'anomalies': len(month_anomalies)
        }

    def generate_monthly_report(self, year=2025, output_file=None):
        """월별 종합 보고서 생성"""
        if output_file:
            original_stdout = sys.stdout
            sys.stdout = open(output_file, 'w', encoding='utf-8')

        print("="*120)
        print(f"{year}년 월별 급여 지급 분석 보고서")
        print("="*120)
        print(f"생성일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # 1. 월별 전체 개요
        print("\n" + "="*120)
        print("[ 1. 월별 전체 개요 ]")
        print("="*120)

        monthly_overview = self.analyze_monthly_overview(year)

        print(f"\n{'월':<8} {'트레이너':>8} {'회원수':>8} {'총건수':>8} {'진행세션':>12} "
              f"{'총수업료(원)':>15} {'총매출(원)':>15} {'평균수업료':>12}")
        print("-"*120)

        total_sessions = 0
        total_salary = 0
        total_revenue = 0

        for row in monthly_overview:
            total_sessions += row['총진행세션'] or 0
            total_salary += row['총수업료'] or 0
            total_revenue += row['총매출'] or 0

            print(f"{row['월']:<8} {row['트레이너수']:>8} {row['회원수']:>8} {row['총건수']:>8} "
                  f"{row['총진행세션'] or 0:>12,.1f} {row['총수업료'] or 0:>15,.0f} "
                  f"{row['총매출'] or 0:>15,.0f} {row['평균수업료'] or 0:>12,.0f}")

        print("-"*120)
        print(f"{'합계':<8} {'':>8} {'':>8} {'':>8} {total_sessions:>12,.1f} "
              f"{total_salary:>15,.0f} {total_revenue:>15,.0f} {'':>12}")

        # 2. 월별 트레이너 실적
        print("\n\n" + "="*120)
        print("[ 2. 월별 트레이너 실적 ]")
        print("="*120)

        trainer_stats = self.analyze_trainer_by_month(year)

        current_month = None
        for row in trainer_stats:
            if current_month != row['월']:
                current_month = row['월']
                print(f"\n▶ {current_month}")
                print("-"*120)
                print(f"{'트레이너':<12} {'회원수':>8} {'진행세션':>12} {'총수업료(원)':>15} "
                      f"{'총매출(원)':>15} {'평균수업료':>12} {'평균세션':>10}")
                print("-"*120)

            print(f"{row['트레이너']:<12} {row['담당회원수']:>8} {row['총진행세션'] or 0:>12,.1f} "
                  f"{row['총수업료'] or 0:>15,.0f} {row['총매출'] or 0:>15,.0f} "
                  f"{row['평균수업료'] or 0:>12,.0f} {row['평균진행세션'] or 0:>10,.1f}")

        # 3. 세션 이상 케이스
        print("\n\n" + "="*120)
        print("[ 3. 세션 이상 케이스 탐지 ]")
        print("="*120)

        anomalies = self.check_session_anomalies_by_month(year)

        if anomalies:
            # 타입별로 분류
            by_type = defaultdict(list)
            for anomaly in anomalies:
                by_type[anomaly['type']].append(anomaly)

            for anomaly_type in ['⚠️ 잔여증가+등록불변', '⚠️ 계산불일치', '✅ 잔여증가+등록증가 (정상)']:
                if anomaly_type in by_type:
                    print(f"\n▶ {anomaly_type} ({len(by_type[anomaly_type])}건)")
                    print("-"*120)
                    print(f"{'트레이너':<10} {'회원명':<10} {'이전월':<6} {'현재월':<6} "
                          f"{'이전잔여':>8} {'진행':>6} {'예상잔여':>8} {'실제잔여':>8} {'차이':>6}")
                    print("-"*120)

                    for a in by_type[anomaly_type][:30]:  # 최대 30건만 출력
                        print(f"{a['trainer']:<10} {a['member']:<10} {a['prev_month']:<6} {a['curr_month']:<6} "
                              f"{a['prev_remain']:>8.1f} {a['curr_monthly']:>6.1f} "
                              f"{a['expected_remain']:>8.1f} {a['actual_remain']:>8.1f} {a['diff']:>6.1f}")

                    if len(by_type[anomaly_type]) > 30:
                        print(f"... 외 {len(by_type[anomaly_type]) - 30}건")
        else:
            print("\n✅ 이상 케이스 없음")

        # 4. 요약
        print("\n\n" + "="*120)
        print("[ 4. 종합 요약 ]")
        print("="*120)

        available_months = self.get_available_months(year)
        print(f"\n분석 기간: {year}년 {available_months[0][1]} ~ {available_months[-1][1]} ({len(available_months)}개월)")
        print(f"총 진행 세션: {total_sessions:,.1f}회")
        print(f"총 지급액: {total_salary:,.0f}원")
        print(f"총 매출: {total_revenue:,.0f}원")
        print(f"월 평균 지급액: {total_salary / len(available_months):,.0f}원")
        print(f"월 평균 매출: {total_revenue / len(available_months):,.0f}원")
        print(f"\n세션 이상 케이스: {len(anomalies)}건")

        print("\n" + "="*120)
        print("보고서 생성 완료")
        print("="*120)

        if output_file:
            sys.stdout.close()
            sys.stdout = original_stdout
            print(f"\n✅ 보고서가 저장되었습니다: {output_file}")


def main():
    """메인 함수"""
    print("="*80)
    print("월별 급여 지급 분석")
    print("="*80)

    # 경로 설정
    base_dir = Path(__file__).parent.parent
    salary_db = base_dir / "data" / "doubless.db"
    members_db = base_dir / "data" / "doubless.db"

    # 분석기 생성
    analyzer = MonthlySalaryAnalyzer(salary_db, members_db)

    try:
        analyzer.connect()

        # 사용 가능한 월 조회
        available_months = analyzer.get_available_months(year=2025)

        if not available_months:
            print("⚠️  분석 가능한 데이터가 없습니다.")
            return

        # 분석 실행 시간
        analysis_time = datetime.now()
        analysis_id = analysis_time.strftime('%Y%m%d_%H%M%S')

        # 보고서 기본 경로
        report_base_dir = base_dir / "pay" / "report"

        # 분석 폴더 생성 (타임스탬프)
        analysis_dir = report_base_dir / analysis_id
        analysis_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n📊 분석 대상: {len(available_months)}개월")
        print(f"📁 저장 폴더: {analysis_dir}")

        # 월별 리포트 생성
        monthly_summaries = []

        for year, month in available_months:
            print(f"\n▶ {year}년 {month} 분석 중...")

            # 월별 리포트 파일명
            month_file = analysis_dir / f"{year}년_{month}_급여분석.txt"

            # 월별 리포트 생성
            summary = analyzer.generate_single_month_report(
                year=year,
                month=month,
                output_file=month_file
            )
            summary['year'] = year
            monthly_summaries.append(summary)

            print(f"   ✅ {month_file.name} 생성 완료")

        # 전체 종합 리포트 생성
        print(f"\n▶ 종합 보고서 생성 중...")
        summary_file = analysis_dir / f"종합분석_{analysis_id}.txt"
        analyzer.generate_monthly_report(year=2025, output_file=summary_file)
        print(f"   ✅ {summary_file.name} 생성 완료")

        # 분석 메타데이터 저장
        metadata = {
            'analysis_id': analysis_id,
            'analysis_time': analysis_time.isoformat(),
            'analysis_time_kr': analysis_time.strftime('%Y년 %m월 %d일 %H시 %M분 %S초'),
            'year': 2025,
            'months_analyzed': len(available_months),
            'monthly_summaries': monthly_summaries,
            'files': {
                'summary': summary_file.name,
                'monthly_reports': [f"{s['year']}년_{s['month']}_급여분석.txt" for s in monthly_summaries]
            }
        }

        metadata_file = analysis_dir / "analysis_info.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        print(f"   ✅ analysis_info.json 생성 완료")

        # latest 폴더 업데이트
        latest_dir = report_base_dir / "latest"

        if latest_dir.exists():
            shutil.rmtree(latest_dir)

        latest_dir.mkdir(parents=True, exist_ok=True)

        # 모든 파일을 latest로 복사
        for file_path in analysis_dir.glob("*"):
            if file_path.is_file():
                dest = latest_dir / file_path.name
                shutil.copy2(file_path, dest)

        print(f"\n✅ latest 폴더 업데이트 완료")

        # 분석 이력 파일 업데이트
        history_file = report_base_dir / "analysis_history.json"

        if history_file.exists():
            with open(history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
        else:
            history = []

        history.append({
            'analysis_id': analysis_id,
            'analysis_time': analysis_time.isoformat(),
            'analysis_time_kr': analysis_time.strftime('%Y년 %m월 %d일 %H시 %M분 %S초'),
            'year': 2025,
            'months_count': len(available_months),
            'total_sessions': sum(s['total_sessions'] for s in monthly_summaries),
            'total_salary': sum(s['total_salary'] for s in monthly_summaries),
            'total_anomalies': sum(s['anomalies'] for s in monthly_summaries)
        })

        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)

        print(f"✅ 분석 이력 업데이트 완료")

        # 최종 결과 출력
        print("\n" + "="*80)
        print("분석 완료")
        print("="*80)
        print(f"\n생성된 파일:")
        print(f"  - 월별 리포트: {len(monthly_summaries)}개")
        print(f"  - 종합 리포트: 1개")
        print(f"  - 메타데이터: 1개")
        print(f"\n저장 위치:")
        print(f"  - 분석 폴더: {analysis_dir}")
        print(f"  - 최신 폴더: {latest_dir}")

    finally:
        analyzer.close()


if __name__ == "__main__":
    main()
