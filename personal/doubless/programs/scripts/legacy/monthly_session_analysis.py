#!/usr/bin/env python3
"""
월별 세션 정합성 분석 프로그램

분석 내용:
1. 트레이너 현황 (퇴직자 정보 반영)
2. 월별 트레이너 실적 요약
3. 잔여세션 vs 진행세션 비교 (초과 진행 탐지)
4. lesson_tickets 테이블 연계 PT 추가 등록 검증
5. 누락/사라진 회원 분석
6. 세션 급감 회원 분석
"""

import sqlite3
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import json
import sys


class MonthlySessionAnalyzer:
    """월별 세션 정합성 분석"""

    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = None

    def connect(self):
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row

    def close(self):
        if self.conn:
            self.conn.close()

    def get_month_order(self, month_str):
        """월 문자열을 숫자로 변환"""
        month_map = {f'{i}월': i for i in range(1, 13)}
        return month_map.get(month_str, 0)

    def get_available_months(self, year=2025):
        """사용 가능한 월 목록"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT DISTINCT 월 FROM salary_records
            WHERE 년도 = ?
            ORDER BY CASE 월
                WHEN '1월' THEN 1 WHEN '2월' THEN 2 WHEN '3월' THEN 3
                WHEN '4월' THEN 4 WHEN '5월' THEN 5 WHEN '6월' THEN 6
                WHEN '7월' THEN 7 WHEN '8월' THEN 8 WHEN '9월' THEN 9
                WHEN '10월' THEN 10 WHEN '11월' THEN 11 WHEN '12월' THEN 12
            END
        """, (year,))
        return [row[0] for row in cursor.fetchall()]

    def get_trainer_status(self):
        """트레이너 현황 (퇴직 정보 포함)"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, name, status, start_date
            FROM employees
            WHERE job_type = '트레이너'
            ORDER BY status, name
        """)
        return {row['name']: {'id': row['id'], 'status': row['status'], 'start_date': row['start_date']}
                for row in cursor.fetchall()}

    def get_monthly_summary(self, year, month):
        """월별 트레이너 실적 요약"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT
                트레이너,
                COUNT(DISTINCT 회원명) as 회원수,
                SUM(당월진행세션) as 진행세션,
                SUM(당월수업료) as 수업료
            FROM salary_records
            WHERE 년도 = ? AND 월 = ?
            GROUP BY 트레이너
            ORDER BY 진행세션 DESC
        """, (year, month))
        return cursor.fetchall()

    def get_lesson_tickets_in_period(self, start_date, end_date):
        """특정 기간 PT 등록 내역"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT
                jgjm_member_name,
                jglesson_ticket_type,
                jglesson_origin_ticket_count,
                jglesson_ticket_started_dttm
            FROM lesson_tickets
            WHERE jglesson_ticket_started_dttm >= ? AND jglesson_ticket_started_dttm < ?
            ORDER BY jgjm_member_name, jglesson_ticket_started_dttm
        """, (start_date, end_date))

        result = defaultdict(list)
        for row in cursor.fetchall():
            result[row['jgjm_member_name']].append({
                'type': row['jglesson_ticket_type'],
                'count': row['jglesson_origin_ticket_count'],
                'start_date': row['jglesson_ticket_started_dttm']
            })
        return result

    def analyze_session_overflow(self, year, prev_month, curr_month):
        """잔여세션 초과 진행 분석 (lesson_tickets 연계)"""
        cursor = self.conn.cursor()

        # 이전월 → 현재월 데이터 조인
        cursor.execute("""
            SELECT
                p.트레이너, p.회원명,
                p.남은세션 as prev_remain,
                p.등록세션 as prev_reg,
                c.당월진행세션 as curr_session,
                c.남은세션 as curr_remain,
                c.등록세션 as curr_reg
            FROM salary_records p
            JOIN salary_records c ON c.년도 = ? AND c.월 = ?
                AND c.트레이너 = p.트레이너 AND c.회원명 = p.회원명
            WHERE p.년도 = ? AND p.월 = ?
        """, (year, curr_month, year, prev_month))

        rows = cursor.fetchall()

        # 현재월 기간 계산 (PT 등록 조회용)
        curr_month_num = self.get_month_order(curr_month)
        start_date = f'{year}-{curr_month_num:02d}-01'
        if curr_month_num == 12:
            end_date = f'{year + 1}-01-01'
        else:
            end_date = f'{year}-{curr_month_num + 1:02d}-01'

        # 해당 기간 PT 등록 내역
        pt_registrations = self.get_lesson_tickets_in_period(start_date, end_date)

        overflow_issues = []
        remain_mismatch = []

        for row in rows:
            trainer = row['트레이너']
            member = row['회원명']
            prev_remain = row['prev_remain'] or 0
            prev_reg = row['prev_reg'] or 0
            curr_session = row['curr_session'] or 0
            curr_remain = row['curr_remain'] or 0
            curr_reg = row['curr_reg'] or 0

            # PT 추가 등록 여부 확인
            pt_added = pt_registrations.get(member, [])
            pt_added_count = sum(p['count'] or 0 for p in pt_added)

            # 1. 초과 진행 탐지
            if curr_session > prev_remain:
                overflow = curr_session - prev_remain
                reg_increased = curr_reg > prev_reg

                # PT 등록으로 설명 가능한지 확인
                explained_by_pt = pt_added_count >= overflow

                overflow_issues.append({
                    'trainer': trainer,
                    'member': member,
                    'prev_remain': prev_remain,
                    'curr_session': curr_session,
                    'overflow': overflow,
                    'prev_reg': prev_reg,
                    'curr_reg': curr_reg,
                    'reg_increased': reg_increased,
                    'pt_added': pt_added,
                    'pt_added_count': pt_added_count,
                    'explained': explained_by_pt or reg_increased
                })

            # 2. 잔여세션 불일치 탐지
            expected_remain = prev_remain - curr_session + pt_added_count
            if curr_reg > prev_reg:
                expected_remain += (curr_reg - prev_reg)

            diff = curr_remain - expected_remain
            if abs(diff) > 0.5 and not (curr_reg > prev_reg):
                remain_mismatch.append({
                    'trainer': trainer,
                    'member': member,
                    'prev_remain': prev_remain,
                    'curr_session': curr_session,
                    'expected_remain': expected_remain,
                    'actual_remain': curr_remain,
                    'diff': diff,
                    'pt_added_count': pt_added_count
                })

        return {
            'overflow': overflow_issues,
            'remain_mismatch': remain_mismatch,
            'pt_registrations': pt_registrations
        }

    def analyze_missing_members(self, year, prev_month, curr_month):
        """이전월에 있었는데 현재월에 없는 회원"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT p.트레이너, p.회원명, p.당월진행세션, p.당월수업료
            FROM salary_records p
            WHERE p.년도 = ? AND p.월 = ? AND p.당월진행세션 > 0
            AND NOT EXISTS (
                SELECT 1 FROM salary_records c
                WHERE c.년도 = ? AND c.월 = ?
                AND c.트레이너 = p.트레이너 AND c.회원명 = p.회원명
            )
            ORDER BY p.트레이너, p.당월수업료 DESC
        """, (year, prev_month, year, curr_month))
        return cursor.fetchall()

    def analyze_session_drop(self, year, prev_month, curr_month, threshold=0.5):
        """세션 급감 회원 (threshold 비율 이상 감소)"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT
                c.트레이너, c.회원명,
                p.당월진행세션 as prev_session,
                c.당월진행세션 as curr_session
            FROM salary_records c
            JOIN salary_records p ON p.년도 = ? AND p.월 = ?
                AND p.트레이너 = c.트레이너 AND p.회원명 = c.회원명
            WHERE c.년도 = ? AND c.월 = ?
            AND p.당월진행세션 > 0
            AND c.당월진행세션 < p.당월진행세션 * ?
            ORDER BY (p.당월진행세션 - c.당월진행세션) DESC
        """, (year, prev_month, year, curr_month, threshold))
        return cursor.fetchall()

    def analyze_returned_members(self, year, prev_month, curr_month):
        """이전월 0세션 → 현재월 복귀 회원"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT c.트레이너, c.회원명, c.당월진행세션
            FROM salary_records c
            LEFT JOIN salary_records p ON p.년도 = ? AND p.월 = ?
                AND p.트레이너 = c.트레이너 AND p.회원명 = c.회원명
            WHERE c.년도 = ? AND c.월 = ? AND c.당월진행세션 > 0
            AND (p.당월진행세션 IS NULL OR p.당월진행세션 = 0)
            ORDER BY c.트레이너, c.당월진행세션 DESC
        """, (year, prev_month, year, curr_month))
        return cursor.fetchall()

    def generate_report(self, year, output_file=None, recent_months=None):
        """종합 분석 보고서 생성

        Args:
            year: 분석 연도
            output_file: 출력 파일 경로
            recent_months: 최근 N개월만 분석 (None이면 전체)
        """
        if output_file:
            f = open(output_file, 'w', encoding='utf-8')
        else:
            f = sys.stdout

        def write(text=''):
            f.write(text + '\n')

        months = self.get_available_months(year)

        # 최근 N개월만 필터링
        if recent_months and recent_months < len(months):
            months = months[-recent_months:]

        trainer_status = self.get_trainer_status()

        write('=' * 100)
        write(f'{year}년 월별 세션 정합성 분석 보고서')
        write('=' * 100)
        write(f'생성일시: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        write(f'분석 기간: {months[0]} ~ {months[-1]} ({len(months)}개월)')
        write()

        # 1. 트레이너 현황
        write('=' * 100)
        write('[1. 트레이너 현황]')
        write('=' * 100)
        for name, info in sorted(trainer_status.items(), key=lambda x: (x[1]['status'] != '근무', x[0])):
            emoji = '🟢' if info['status'] == '근무' else '🔴'
            write(f"  {emoji} {name}: {info['status']} (입사: {info['start_date']})")
        write()

        # 2. 월별 트레이너 실적
        write('=' * 100)
        write('[2. 월별 트레이너 실적]')
        write('=' * 100)

        for month in months:
            write(f'\n▶ {month}')
            write('-' * 100)
            write(f'{"트레이너":>10} {"상태":>6} {"회원수":>8} {"진행세션":>10} {"수업료":>14}')
            write('-' * 100)

            summary = self.get_monthly_summary(year, month)
            for row in summary:
                trainer = row['트레이너']
                status = trainer_status.get(trainer, {}).get('status', '?')
                status_mark = '퇴사' if status == '퇴사' else '근무'
                write(f'{trainer:>10} {status_mark:>6} {row["회원수"]:>8} '
                      f'{row["진행세션"] or 0:>10.0f} {row["수업료"] or 0:>14,.0f}')

        # 3. 월간 비교 분석
        write('\n\n' + '=' * 100)
        write('[3. 월간 세션 정합성 분석]')
        write('=' * 100)

        for i in range(1, len(months)):
            prev_month = months[i - 1]
            curr_month = months[i]

            write(f'\n{"=" * 100}')
            write(f'▶ {prev_month} → {curr_month} 비교')
            write('=' * 100)

            # 3-1. 잔여세션 초과 진행
            analysis = self.analyze_session_overflow(year, prev_month, curr_month)
            overflow = analysis['overflow']
            unexplained = [o for o in overflow if not o['explained']]

            if unexplained:
                write(f'\n⚠️  잔여세션 초과 진행 (PT 등록으로 설명 안됨) - {len(unexplained)}건')
                write('-' * 100)
                write(f'{"트레이너":>8} {"회원명":>10} {"전월잔여":>8} {"당월진행":>8} {"초과":>6} {"PT추가":>8} {"설명"}')
                write('-' * 100)
                for o in sorted(unexplained, key=lambda x: -x['overflow']):
                    pt_info = f"{o['pt_added_count']}회" if o['pt_added_count'] > 0 else '-'
                    write(f'{o["trainer"]:>8} {o["member"]:>10} {o["prev_remain"]:>8.0f} '
                          f'{o["curr_session"]:>8.0f} {o["overflow"]:>+6.0f} {pt_info:>8} 확인필요')

            explained = [o for o in overflow if o['explained']]
            if explained:
                write(f'\n✅ 잔여세션 초과 진행 (PT 등록으로 설명됨) - {len(explained)}건')
                write('-' * 100)
                for o in explained[:10]:
                    pt_details = ', '.join([f"{p['type']}({p['count']}회)" for p in o['pt_added']]) if o['pt_added'] else '등록세션 증가'
                    write(f'  {o["trainer"]} - {o["member"]}: {o["prev_remain"]:.0f} → {o["curr_session"]:.0f}세션 진행 ({pt_details})')
                if len(explained) > 10:
                    write(f'  ... 외 {len(explained) - 10}건')

            # 3-2. 잔여세션 불일치
            mismatch = analysis['remain_mismatch']
            if mismatch:
                write(f'\n⚠️  잔여세션 계산 불일치 - {len(mismatch)}건')
                write('-' * 100)
                write(f'{"트레이너":>8} {"회원명":>10} {"전월잔여":>8} {"당월진행":>8} {"예상잔여":>8} {"실제잔여":>8} {"차이":>6}')
                write('-' * 100)
                for m in sorted(mismatch, key=lambda x: abs(x['diff']), reverse=True)[:15]:
                    write(f'{m["trainer"]:>8} {m["member"]:>10} {m["prev_remain"]:>8.0f} '
                          f'{m["curr_session"]:>8.0f} {m["expected_remain"]:>8.0f} '
                          f'{m["actual_remain"]:>8.0f} {m["diff"]:>+6.0f}')
                if len(mismatch) > 15:
                    write(f'  ... 외 {len(mismatch) - 15}건')

            # 3-3. 누락 회원
            missing = self.analyze_missing_members(year, prev_month, curr_month)
            if missing:
                # 퇴직 트레이너 회원 제외
                active_missing = [m for m in missing
                                  if trainer_status.get(m['트레이너'], {}).get('status') == '근무']
                if active_missing:
                    write(f'\n⚠️  {prev_month}에 있었는데 {curr_month}에 없는 회원 (근무 트레이너) - {len(active_missing)}건')
                    write('-' * 100)
                    for m in active_missing[:10]:
                        write(f'  {m["트레이너"]} - {m["회원명"]}: {prev_month} {m["당월진행세션"]:.0f}세션, {m["당월수업료"]:,.0f}원')
                    if len(active_missing) > 10:
                        write(f'  ... 외 {len(active_missing) - 10}건')

            # 3-4. 세션 급감
            drops = self.analyze_session_drop(year, prev_month, curr_month)
            if drops:
                write(f'\n📉 세션 급감 회원 (50% 이상 감소) - {len(drops)}건')
                write('-' * 100)
                for d in drops[:10]:
                    diff = (d['prev_session'] or 0) - (d['curr_session'] or 0)
                    write(f'  {d["트레이너"]} - {d["회원명"]}: {d["prev_session"]:.0f} → {d["curr_session"]:.0f} (↓{diff:.0f})')
                if len(drops) > 10:
                    write(f'  ... 외 {len(drops) - 10}건')

            # 3-5. 복귀 회원
            returned = self.analyze_returned_members(year, prev_month, curr_month)
            if returned:
                write(f'\n📈 {prev_month} 0세션 → {curr_month} 복귀 - {len(returned)}건')
                write('-' * 100)
                for r in returned[:10]:
                    write(f'  {r["트레이너"]} - {r["회원명"]}: {r["당월진행세션"]:.0f}세션')
                if len(returned) > 10:
                    write(f'  ... 외 {len(returned) - 10}건')

        # 4. 요약
        write('\n\n' + '=' * 100)
        write('[4. 종합 요약]')
        write('=' * 100)

        # 전체 통계
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT
                COUNT(DISTINCT 트레이너) as trainers,
                COUNT(DISTINCT 회원명) as members,
                SUM(당월진행세션) as sessions,
                SUM(당월수업료) as tuition
            FROM salary_records
            WHERE 년도 = ?
        """, (year,))
        total = cursor.fetchone()

        write(f'\n총 트레이너: {total["trainers"]}명 (근무: {sum(1 for t in trainer_status.values() if t["status"] == "근무")}명)')
        write(f'총 회원: {total["members"]}명')
        write(f'총 진행세션: {total["sessions"] or 0:,.0f}회')
        write(f'총 수업료: {total["tuition"] or 0:,.0f}원')

        write('\n' + '=' * 100)
        write('보고서 생성 완료')
        write('=' * 100)

        if output_file:
            f.close()


def main():
    import argparse
    import shutil

    parser = argparse.ArgumentParser(description='월별 세션 정합성 분석')
    parser.add_argument('-m', '--months', type=int, default=None,
                        help='최근 N개월만 분석 (기본값: 전체)')
    parser.add_argument('-y', '--year', type=int, default=2025,
                        help='분석 연도 (기본값: 2025)')
    args = parser.parse_args()

    recent_months = args.months
    year = args.year

    print('=' * 80)
    if recent_months:
        print(f'월별 세션 정합성 분석 (최근 {recent_months}개월)')
    else:
        print('월별 세션 정합성 분석 (전체)')
    print('=' * 80)

    base_dir = Path(__file__).parent.parent
    db_path = base_dir / 'data' / 'doubless.db'

    if not db_path.exists():
        print(f'❌ DB 파일을 찾을 수 없습니다: {db_path}')
        sys.exit(1)

    analyzer = MonthlySessionAnalyzer(db_path)

    try:
        analyzer.connect()

        # 분석 실행 시간
        analysis_time = datetime.now()
        analysis_id = analysis_time.strftime('%Y%m%d_%H%M%S')

        # 보고서 기본 경로
        report_base_dir = base_dir / 'pay' / 'report' / 'session_analysis'

        # 분석 폴더 생성 (타임스탬프)
        if recent_months:
            analysis_dir = report_base_dir / f'{analysis_id}_{recent_months}m'
        else:
            analysis_dir = report_base_dir / analysis_id
        analysis_dir.mkdir(parents=True, exist_ok=True)

        # 분석 대상 월 조회
        all_months = analyzer.get_available_months(year)
        if recent_months and recent_months < len(all_months):
            target_months = all_months[-recent_months:]
        else:
            target_months = all_months

        print(f'\n📊 분석 대상: {len(target_months)}개월 ({target_months[0]} ~ {target_months[-1]})')
        print(f'📁 저장 폴더: {analysis_dir}')

        # 월별 개별 리포트 생성
        trainer_status = analyzer.get_trainer_status()
        monthly_summaries = []

        for i, month in enumerate(target_months):
            print(f'\n▶ {year}년 {month} 분석 중...')

            month_file = analysis_dir / f'{year}년_{month}_세션분석.txt'

            with open(month_file, 'w', encoding='utf-8') as f:
                f.write('=' * 100 + '\n')
                f.write(f'{year}년 {month} 세션 정합성 분석 보고서\n')
                f.write('=' * 100 + '\n')
                f.write(f'생성일시: {analysis_time.strftime("%Y-%m-%d %H:%M:%S")}\n\n')

                # 해당 월 트레이너 실적
                f.write('=' * 100 + '\n')
                f.write(f'[1. {month} 트레이너 실적]\n')
                f.write('=' * 100 + '\n\n')

                summary = analyzer.get_monthly_summary(year, month)
                f.write(f'{"트레이너":>8} {"상태":>6} {"회원수":>8} {"진행세션":>10} {"수업료":>14}\n')
                f.write('-' * 100 + '\n')

                month_sessions = 0
                month_tuition = 0
                for row in summary:
                    trainer = row['트레이너']
                    status = trainer_status.get(trainer, {}).get('status', '?')
                    sessions = row['진행세션'] or 0
                    tuition = row['수업료'] or 0
                    month_sessions += sessions
                    month_tuition += tuition
                    f.write(f'{trainer:>8} {status:>6} {row["회원수"]:>8} {sessions:>10.0f} {tuition:>14,.0f}\n')

                # 이전 월과 비교 (첫 월이 아닌 경우)
                if i > 0:
                    prev_month = target_months[i-1]
                    f.write(f'\n\n{"=" * 100}\n')
                    f.write(f'[2. {prev_month} → {month} 비교]\n')
                    f.write('=' * 100 + '\n')

                    analysis = analyzer.analyze_session_overflow(year, prev_month, month)

                    # 미설명 초과
                    unexplained = [o for o in analysis['overflow'] if not o['explained']]
                    if unexplained:
                        f.write(f'\n⚠️ 잔여세션 초과 진행 (PT 등록으로 설명 안됨) - {len(unexplained)}건\n')
                        f.write('-' * 100 + '\n')
                        for o in sorted(unexplained, key=lambda x: -x['overflow'])[:15]:
                            f.write(f'  {o["trainer"]} - {o["member"]}: 잔여 {o["prev_remain"]:.0f} → {o["curr_session"]:.0f}세션 진행 (+{o["overflow"]:.0f})\n')

                    # PT 설명됨
                    explained = [o for o in analysis['overflow'] if o['explained']]
                    if explained:
                        f.write(f'\n✅ 잔여세션 초과 진행 (PT 등록으로 설명됨) - {len(explained)}건\n')
                        f.write('-' * 100 + '\n')
                        for o in explained[:10]:
                            pt_details = ', '.join([f"{p['type']}({p['count']}회)" for p in o['pt_added']]) if o['pt_added'] else '등록세션 증가'
                            f.write(f'  {o["trainer"]} - {o["member"]}: {o["prev_remain"]:.0f} → {o["curr_session"]:.0f}세션 ({pt_details})\n')

                    # 잔여 불일치
                    if analysis['remain_mismatch']:
                        f.write(f'\n⚠️ 잔여세션 계산 불일치 - {len(analysis["remain_mismatch"])}건\n')
                        f.write('-' * 100 + '\n')
                        f.write(f'{"트레이너":>8} {"회원명":>10} {"전월잔여":>8} {"당월진행":>8} {"예상":>8} {"실제":>8} {"차이":>6}\n')
                        f.write('-' * 100 + '\n')
                        for m in sorted(analysis['remain_mismatch'], key=lambda x: abs(x['diff']), reverse=True)[:15]:
                            f.write(f'{m["trainer"]:>8} {m["member"]:>10} {m["prev_remain"]:>8.0f} {m["curr_session"]:>8.0f} {m["expected_remain"]:>8.0f} {m["actual_remain"]:>8.0f} {m["diff"]:>+6.0f}\n')

                    # 누락 회원
                    missing = analyzer.analyze_missing_members(year, prev_month, month)
                    active_missing = [m for m in missing if trainer_status.get(m['트레이너'], {}).get('status') == '근무']
                    if active_missing:
                        f.write(f'\n⚠️ {prev_month}에 있었는데 {month}에 없는 회원 - {len(active_missing)}건\n')
                        f.write('-' * 100 + '\n')
                        for m in active_missing[:10]:
                            f.write(f'  {m["트레이너"]} - {m["회원명"]}: {prev_month} {m["당월진행세션"]:.0f}세션, {m["당월수업료"]:,.0f}원\n')

                    # 세션 급감
                    drops = analyzer.analyze_session_drop(year, prev_month, month)
                    if drops:
                        f.write(f'\n📉 세션 급감 (50% 이상 감소) - {len(drops)}건\n')
                        f.write('-' * 100 + '\n')
                        for d in drops[:10]:
                            diff = (d['prev_session'] or 0) - (d['curr_session'] or 0)
                            f.write(f'  {d["트레이너"]} - {d["회원명"]}: {d["prev_session"]:.0f} → {d["curr_session"]:.0f} (↓{diff:.0f})\n')

                    # 복귀 회원
                    returned = analyzer.analyze_returned_members(year, prev_month, month)
                    if returned:
                        f.write(f'\n📈 {prev_month} 0세션 → {month} 복귀 - {len(returned)}건\n')
                        f.write('-' * 100 + '\n')
                        for r in returned[:10]:
                            f.write(f'  {r["트레이너"]} - {r["회원명"]}: {r["당월진행세션"]:.0f}세션\n')

                f.write('\n' + '=' * 100 + '\n')
                f.write('보고서 생성 완료\n')
                f.write('=' * 100 + '\n')

            monthly_summaries.append({
                'month': month,
                'sessions': month_sessions,
                'tuition': month_tuition
            })
            print(f'   ✅ {month_file.name} 생성 완료')

        # 종합 리포트 생성
        print(f'\n▶ 종합 보고서 생성 중...')
        if recent_months:
            summary_file = analysis_dir / f'종합분석_{recent_months}m_{analysis_id}.txt'
        else:
            summary_file = analysis_dir / f'종합분석_{analysis_id}.txt'

        analyzer.generate_report(year=year, output_file=summary_file, recent_months=recent_months)
        print(f'   ✅ {summary_file.name} 생성 완료')

        # 메타데이터 저장
        metadata = {
            'analysis_id': analysis_id,
            'analysis_time': analysis_time.isoformat(),
            'year': year,
            'recent_months': recent_months,
            'months_analyzed': len(target_months),
            'month_range': f'{target_months[0]} ~ {target_months[-1]}',
            'monthly_summaries': monthly_summaries
        }

        metadata_file = analysis_dir / 'analysis_info.json'
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        print(f'   ✅ analysis_info.json 생성 완료')

        # latest 폴더 업데이트
        latest_dir = report_base_dir / 'latest'
        if latest_dir.exists():
            shutil.rmtree(latest_dir)
        latest_dir.mkdir(parents=True, exist_ok=True)

        for file_path in analysis_dir.glob('*'):
            if file_path.is_file():
                shutil.copy2(file_path, latest_dir / file_path.name)
        print(f'\n✅ latest 폴더 업데이트 완료')

        # 최종 결과
        print('\n' + '=' * 80)
        print('분석 완료')
        print('=' * 80)
        print(f'\n생성된 파일:')
        print(f'  - 월별 리포트: {len(monthly_summaries)}개')
        print(f'  - 종합 리포트: 1개')
        print(f'  - 메타데이터: 1개')
        print(f'\n저장 위치:')
        print(f'  - 분석 폴더: {analysis_dir}')
        print(f'  - 최신 폴더: {latest_dir}')

    finally:
        analyzer.close()


if __name__ == '__main__':
    main()
