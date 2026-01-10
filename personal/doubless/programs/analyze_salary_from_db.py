#!/usr/bin/env python3
"""
급여 DB 기반 이상건 분석 프로그램

급여 DB와 회원 DB를 조인하여 종합적인 이상건 분석을 수행합니다.
"""

import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import calendar
import json
import shutil
import re

def load_name_mapping_rules():
    """이름 매핑 규칙 로드"""
    rules_file = Path(__file__).parent / "name_mapping_rules.json"

    if not rules_file.exists():
        print("⚠️  이름 매핑 규칙 파일이 없습니다. 기본 규칙 사용")
        return {
            "normalization_rules": {
                "rules": [
                    {"pattern": "E$", "replacement": "", "enabled": True}
                ]
            },
            "known_mappings": {"mappings": {}}
        }

    with open(rules_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def normalize_name(name, rules):
    """이름 정규화 (규칙 적용)"""
    if pd.isna(name):
        return name

    normalized = str(name).strip()

    # 정규화 규칙 적용
    for rule in rules["normalization_rules"]["rules"]:
        if rule.get("enabled", True):
            pattern = rule["pattern"]
            replacement = rule["replacement"]
            normalized = re.sub(pattern, replacement, normalized)

    # 알려진 매핑 적용
    mappings = rules["known_mappings"]["mappings"]
    if normalized in mappings:
        original = normalized
        normalized = mappings[normalized]
        return normalized, True, original  # (정규화된 이름, 매핑 적용 여부, 원본 이름)

    return normalized, False, name

def load_salary_and_members(salary_db_path, members_db_path, name_rules=None):
    """급여 DB와 회원 DB를 조인하여 로드 (이름 정규화 적용)"""
    conn = sqlite3.connect(salary_db_path)

    # 회원 DB 연결
    conn.execute(f"ATTACH DATABASE '{members_db_path}' AS members_db")

    # 급여 데이터 먼저 로드
    salary_query = """
        SELECT
            년도, 월, 트레이너, 회원명, 성별,
            등록세션, 총진행세션, 남은세션,
            결제형태, 등록비용, 공급가, 회단가, 매출대비율,
            수업료_정산, 당월진행세션, 당월수업료, 이달의매출
        FROM salary_records
        ORDER BY 년도, 월, 트레이너, 회원명
    """
    salary_df = pd.read_sql(salary_query, conn)

    # 이름 정규화 적용
    if name_rules:
        salary_df['원본_회원명'] = salary_df['회원명']
        normalized_results = salary_df['회원명'].apply(lambda x: normalize_name(x, name_rules))

        # 정규화 결과 분리
        salary_df['회원명_정규화'] = normalized_results.apply(lambda x: x[0])
        salary_df['이름_매핑_적용'] = normalized_results.apply(lambda x: x[1])
        salary_df['매핑_전_이름'] = normalized_results.apply(lambda x: x[2])
    else:
        salary_df['회원명_정규화'] = salary_df['회원명']
        salary_df['이름_매핑_적용'] = False
        salary_df['원본_회원명'] = salary_df['회원명']

    # 회원 DB 로드
    members_query = """
        SELECT
            이름, 상태, 성별, 연락처, 보유이용권,
            최종만료일, 남은일수, 최근구매일, 최근출석일,
            상담담당자, 나이
        FROM members
    """
    members_df = pd.read_sql(members_query, conn)
    conn.close()

    # 정규화된 이름으로 조인
    result_df = salary_df.merge(
        members_df,
        left_on='회원명_정규화',
        right_on='이름',
        how='left',
        suffixes=('_급여', '_회원DB')
    )

    # 컬럼명 정리
    result_df.rename(columns={
        '성별_급여': '급여상_성별',
        '성별_회원DB': '회원DB_성별',
        '상태': '회원상태',
        '상담담당자': '회원DB_담당자'
    }, inplace=True)

    return result_df

def get_month_end_date(year, month_str):
    """월 문자열(예: '11월')을 받아 해당 월의 마지막 날짜를 반환"""
    month_num = int(month_str.replace('월', ''))
    last_day = calendar.monthrange(year, month_num)[1]
    return datetime(year, month_num, last_day)

def is_expired_at_session_time(row):
    """세션 진행 당시에 회원권이 만료되었는지 확인"""
    # 회원 DB에 없으면 판단 불가
    if pd.isna(row['최종만료일']):
        return False

    try:
        # 최종만료일 파싱
        expire_date = pd.to_datetime(row['최종만료일'])

        # 급여 월의 마지막 날 계산
        month_end = get_month_end_date(int(row['년도']), row['월'])

        # 급여 월 마지막 날 기준으로 만료되었으면 True
        return expire_date < month_end
    except:
        return False

def detect_anomalies(df):
    """이상건 탐지"""
    anomalies = []

    # 월별로 정렬
    months = df['월'].unique()

    # 이전 월 데이터 저장용
    prev_month_data = {}

    for month in sorted(months):
        month_df = df[df['월'] == month]

        for idx, row in month_df.iterrows():
            issues = []

            # 1. 당월 진행세션이 있는데 남은세션이 음수 (0은 정상 - 정확히 소진)
            if pd.notna(row['당월진행세션']) and row['당월진행세션'] > 0:
                if pd.notna(row['남은세션']) and row['남은세션'] < 0:
                    issues.append(f"당월 {row['당월진행세션']:.0f}회 진행했으나 남은세션 {row['남은세션']:.0f}회 (초과 사용)")

            # 2. 회원 DB에 없는 경우
            in_db = pd.notna(row['회원상태'])
            if not in_db:
                issues.append("회원 DB에 존재하지 않음 (탈퇴 또는 이름 오타)")

            # 3. 세션 진행 당시 만료된 회원인데 세션 진행
            if in_db:
                if pd.notna(row['당월진행세션']) and row['당월진행세션'] > 0:
                    if is_expired_at_session_time(row):
                        issues.append(f"세션 진행 당시({row['월']}) 이미 만료된 회원 (만료일: {row['최종만료일']})")

            # 4. 담당자 불일치
            if in_db and pd.notna(row['회원DB_담당자']) and row['회원DB_담당자'] != '-':
                if str(row['트레이너']) != str(row['회원DB_담당자']):
                    issues.append(f"담당자 불일치: 급여({row['트레이너']}) ≠ DB({row['회원DB_담당자']})")

            # 5. 전월 대비 체크 (이전 월 데이터가 있는 경우)
            member_key = f"{row['트레이너']}_{row['회원명']}"
            if member_key in prev_month_data:
                prev_row = prev_month_data[member_key]

                # 10월, 11월은 어뷰징 가능성으로 더 엄격하게 체크
                is_strict_month = row['월'] in ['10월', '11월']

                # 전월 잔여세션과 당월 진행세션, 당월 잔여세션이 모두 있는 경우
                if pd.notna(prev_row['남은세션']) and pd.notna(row['당월진행세션']) and pd.notna(row['남은세션']):
                    prev_remaining = prev_row['남은세션']
                    current_sessions = row['당월진행세션']
                    current_remaining = row['남은세션']

                    # 예상 잔여 = 전월 잔여 - 당월 진행
                    expected_remaining = prev_remaining - current_sessions

                    # 10월, 11월: 전월 잔여보다 많이 진행한 경우 모두 이상
                    if is_strict_month and current_sessions > 0:
                        if expected_remaining < 0:
                            # 전월 잔여세션 부족한데 진행
                            shortage = abs(expected_remaining)
                            issues.append(f"🚨 전월 잔여 {prev_remaining:.0f}회 부족한데 당월 {current_sessions:.0f}회 진행 (부족: {shortage:.0f}회) [어뷰징 의심]")

                    # 실제 잔여와 예상 잔여가 다른 경우
                    if abs(current_remaining - expected_remaining) > 0.5:  # 부동소수점 오차 고려
                        diff = current_remaining - expected_remaining

                        if diff > 0:
                            # 예상보다 많이 남음 = 세션이 증가했거나 차감이 안됨
                            if is_strict_month:
                                issues.append(f"🚨 세션 차감 이상: 전월 잔여 {prev_remaining:.0f}회 - 당월 진행 {current_sessions:.0f}회 = 예상 {expected_remaining:.0f}회, 실제 {current_remaining:.0f}회 (+{diff:.0f}회 증가) [어뷰징 의심]")
                            else:
                                issues.append(f"세션 차감 이상: 전월 잔여 {prev_remaining:.0f}회 - 당월 진행 {current_sessions:.0f}회 = 예상 {expected_remaining:.0f}회, 실제 {current_remaining:.0f}회 (+{diff:.0f}회 증가)")
                        else:
                            # 예상보다 적게 남음 = 추가 차감 발생
                            issues.append(f"세션 추가 차감: 전월 잔여 {prev_remaining:.0f}회 - 당월 진행 {current_sessions:.0f}회 = 예상 {expected_remaining:.0f}회, 실제 {current_remaining:.0f}회 ({diff:.0f}회 추가 차감)")

                # 전월 잔여세션보다 당월 진행세션이 많은 경우 (이용권 추가 구매 없이)
                elif pd.notna(prev_row['남은세션']) and pd.notna(row['당월진행세션']):
                    if row['당월진행세션'] > prev_row['남은세션']:
                        # 10월, 11월은 무조건 이상
                        if is_strict_month:
                            shortage = row['당월진행세션'] - prev_row['남은세션']
                            issues.append(f"🚨 전월 잔여 {prev_row['남은세션']:.0f}회인데 당월 {row['당월진행세션']:.0f}회 진행 (초과: {shortage:.0f}회) [어뷰징 의심]")
                        # 다른 달은 당월 잔여가 없으면 문제
                        elif pd.isna(row['남은세션']) or row['남은세션'] <= 0:
                            issues.append(f"전월 잔여 {prev_row['남은세션']:.0f}회 초과 진행: 당월 {row['당월진행세션']:.0f}회 진행")

            # 6. 당월수업료가 비정상적으로 높거나 낮은 경우
            if pd.notna(row['당월진행세션']) and pd.notna(row['당월수업료']) and pd.notna(row['회단가']):
                if row['당월진행세션'] > 0 and row['회단가'] > 0:
                    expected = row['당월진행세션'] * row['회단가'] * row['매출대비율']
                    actual = row['당월수업료']
                    # 10% 이상 차이나면 이상
                    if abs(expected - actual) / expected > 0.1:
                        issues.append(f"급여 계산 이상: 예상 {expected:,.0f}원 vs 실제 {actual:,.0f}원")

            if issues:
                anomaly = {
                    '년도': row['년도'],
                    '월': row['월'],
                    '트레이너': row['트레이너'],
                    '회원명': row['회원명'],
                    '당월진행세션': row['당월진행세션'],
                    '남은세션': row['남은세션'],
                    '당월수업료': row['당월수업료'],
                    '등록비용': row['등록비용'],
                    '공급가': row['공급가'],
                    '회단가': row['회단가'],
                    '회원상태': row['회원상태'],
                    '연락처': row['연락처'],
                    '최종만료일': row['최종만료일'],
                    '남은일수': row['남은일수'],
                    '최근출석일': row['최근출석일'],
                    '회원DB_담당자': row['회원DB_담당자'],
                    'in_db': in_db,
                    'issues': issues
                }
                anomalies.append(anomaly)

        # 현재 월 데이터를 다음 월을 위해 저장
        for idx, row in month_df.iterrows():
            member_key = f"{row['트레이너']}_{row['회원명']}"
            prev_month_data[member_key] = row

    return anomalies

def save_anomalies_csv(anomalies, output_path):
    """이상건을 CSV 파일로 저장 (엑셀에서 열기 편함)"""
    import csv

    with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)

        # 헤더
        writer.writerow([
            '년도', '월', '트레이너', '회원명', '당월진행세션', '남은세션',
            '당월수업료', '회원상태', '연락처', '최종만료일', '최근출석일',
            '회원DB_담당자', '문제점'
        ])

        # 데이터
        for a in anomalies:
            issues_str = ' | '.join(a['issues'])
            writer.writerow([
                a['년도'],
                a['월'],
                a['트레이너'],
                a['회원명'],
                f"{a['당월진행세션']:.0f}" if pd.notna(a['당월진행세션']) else '',
                f"{a['남은세션']:.0f}" if pd.notna(a['남은세션']) else '',
                f"{a['당월수업료']:,.0f}" if pd.notna(a['당월수업료']) else '',
                a['회원상태'] if a['in_db'] else 'DB없음',
                a['연락처'] if pd.notna(a['연락처']) else '',
                a['최종만료일'] if pd.notna(a['최종만료일']) else '',
                a['최근출석일'] if pd.notna(a['최근출석일']) else '',
                a['회원DB_담당자'] if pd.notna(a['회원DB_담당자']) else '',
                issues_str
            ])

def save_metadata(report_dir, anomalies, total_records):
    """분석 메타데이터 저장"""
    metadata = {
        'timestamp': datetime.now().isoformat(),
        'total_salary_records': total_records,
        'total_anomalies': len(anomalies),
        'anomalies_in_db': sum(1 for a in anomalies if a['in_db']),
        'anomalies_not_in_db': sum(1 for a in anomalies if not a['in_db']),
        'anomaly_rate': f"{len(anomalies)*100/total_records:.1f}%",
        'issue_types': {}
    }

    # 이상 유형별 통계
    issue_types = defaultdict(int)
    for a in anomalies:
        for issue in a['issues']:
            if '회원 DB에 존재하지 않음' in issue:
                issue_types['회원 DB 없음'] += 1
            elif '세션 진행 당시' in issue and '이미 만료' in issue:
                issue_types['세션 진행 당시 만료된 회원'] += 1
            elif '담당자 불일치' in issue:
                issue_types['담당자 불일치'] += 1
            elif '어뷰징 의심' in issue:
                issue_types['🚨 어뷰징 의심 (10-11월)'] += 1
            elif '세션 차감 이상' in issue:
                issue_types['세션 차감 이상 (비정상 증가)'] += 1
            elif '세션 추가 차감' in issue:
                issue_types['세션 추가 차감'] += 1
            elif '전월 잔여' in issue and '초과 진행' in issue:
                issue_types['전월 잔여 초과 진행'] += 1
            elif '급여 계산 이상' in issue:
                issue_types['급여 계산 오류'] += 1
            elif '남은세션 0' in issue or '남은세션 -' in issue:
                issue_types['세션 종료 후 진행'] += 1

    metadata['issue_types'] = dict(issue_types)

    # JSON 저장
    meta_file = report_dir / "분석_메타데이터.json"
    with open(meta_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

def save_analysis_report(anomalies, output_path):
    """분석 보고서 저장"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("="*120 + "\n")
        f.write("Doubless 급여 이상건 종합 분석 보고서 (DB 기반)\n")
        f.write(f"생성일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*120 + "\n\n")

        # 전체 통계
        total = len(anomalies)
        in_db = sum(1 for a in anomalies if a['in_db'])
        not_in_db = total - in_db

        f.write("📊 전체 통계\n")
        f.write("="*120 + "\n")
        f.write(f"총 이상건: {total}건\n")
        f.write(f"  - 회원 DB 존재: {in_db}건 ({in_db*100/total:.1f}%)\n")
        f.write(f"  - 회원 DB 없음: {not_in_db}건 ({not_in_db*100/total:.1f}%)\n\n")

        # 이상 유형별 통계
        f.write("📋 이상 유형별 통계\n")
        f.write("="*120 + "\n")
        issue_types = defaultdict(int)
        for a in anomalies:
            for issue in a['issues']:
                # 이슈 유형 분류
                if '회원 DB에 존재하지 않음' in issue:
                    issue_types['회원 DB 없음'] += 1
                elif '세션 진행 당시' in issue and '이미 만료' in issue:
                    issue_types['세션 진행 당시 만료된 회원'] += 1
                elif '담당자 불일치' in issue:
                    issue_types['담당자 불일치'] += 1
                elif '어뷰징 의심' in issue:
                    issue_types['🚨 어뷰징 의심 (10-11월)'] += 1
                elif '세션 차감 이상' in issue:
                    issue_types['세션 차감 이상 (비정상 증가)'] += 1
                elif '세션 추가 차감' in issue:
                    issue_types['세션 추가 차감'] += 1
                elif '전월 잔여' in issue and '초과 진행' in issue:
                    issue_types['전월 잔여 초과 진행'] += 1
                elif '급여 계산 이상' in issue:
                    issue_types['급여 계산 오류'] += 1
                elif '남은세션 0' in issue or '남은세션 -' in issue:
                    issue_types['세션 종료 후 진행'] += 1

        for issue_type, count in sorted(issue_types.items(), key=lambda x: x[1], reverse=True):
            f.write(f"  {issue_type}: {count}건\n")

        # 회원 DB 없는 목록
        if not_in_db > 0:
            f.write(f"\n\n⚠️  회원 DB에 없는 회원 목록 ({not_in_db}건)\n")
            f.write("="*120 + "\n")
            f.write("급여 데이터에는 있지만 회원 DB에서 찾을 수 없습니다. (이름 오타 또는 탈퇴 회원)\n\n")

            not_in_db_list = [a for a in anomalies if not a['in_db']]
            for idx, a in enumerate(not_in_db_list, 1):
                f.write(f"{idx}. [{a['월']}] {a['트레이너']} - {a['회원명']}")
                f.write(f" (당월 {a['당월진행세션']:.0f}회, 급여 {a['당월수업료']:,.0f}원)\n")

        # 월별 상세 분석
        f.write(f"\n\n{'='*120}\n")
        f.write("📅 월별 상세 분석\n")
        f.write(f"{'='*120}\n\n")

        month_summary = defaultdict(list)
        for a in anomalies:
            if a['in_db']:  # DB에 있는 회원만
                month_summary[a['월']].append(a)

        for month in sorted(month_summary.keys()):
            month_anomalies = month_summary[month]
            f.write(f"\n{'='*120}\n")
            f.write(f"[{month}] - {len(month_anomalies)}건\n")
            f.write(f"{'='*120}\n\n")

            trainer_summary = defaultdict(list)
            for a in month_anomalies:
                trainer_summary[a['트레이너']].append(a)

            for trainer, trainer_anomalies in sorted(trainer_summary.items()):
                f.write(f"\n{trainer} 트레이너: {len(trainer_anomalies)}건\n")
                f.write("-" * 120 + "\n\n")

                for idx, a in enumerate(trainer_anomalies, 1):
                    f.write(f"{idx}. {a['회원명']}\n")
                    f.write(f"   {'─'*110}\n")

                    # 급여 데이터
                    f.write(f"   [급여 데이터]\n")
                    f.write(f"   • 당월 진행세션: {a['당월진행세션']:.0f}회\n")
                    f.write(f"   • 남은 세션: {a['남은세션']:.0f}회\n" if pd.notna(a['남은세션']) else "   • 남은 세션: N/A\n")
                    f.write(f"   • 당월 수업료: {a['당월수업료']:,.0f}원\n" if pd.notna(a['당월수업료']) else "   • 당월 수업료: N/A\n")
                    if pd.notna(a['회단가']):
                        f.write(f"   • 1회 단가: {a['회단가']:,.0f}원\n")
                    if pd.notna(a['등록비용']):
                        f.write(f"   • 등록비용: {a['등록비용']:,.0f}원\n")
                    if pd.notna(a['공급가']):
                        f.write(f"   • 공급가: {a['공급가']:,.0f}원\n")

                    # 회원 DB 정보
                    f.write(f"\n   [회원 DB 정보]\n")
                    f.write(f"   • 회원 상태: {a['회원상태']}\n")
                    if pd.notna(a['연락처']):
                        f.write(f"   • 연락처: {a['연락처']}\n")
                    if pd.notna(a['최종만료일']):
                        days_str = f" (D-{int(a['남은일수'])})" if pd.notna(a['남은일수']) else ""
                        f.write(f"   • 최종 만료일: {a['최종만료일']}{days_str}\n")
                    if pd.notna(a['최근출석일']):
                        f.write(f"   • 최근 출석일: {a['최근출석일']}\n")
                    if pd.notna(a['회원DB_담당자']) and a['회원DB_담당자'] != '-':
                        f.write(f"   • DB상 담당자: {a['회원DB_담당자']}\n")

                    # 문제점
                    f.write(f"\n   [문제점]\n")
                    for issue in a['issues']:
                        f.write(f"   ⚠️  {issue}\n")

                    f.write("\n")

        # 주요 발견사항
        f.write(f"\n\n{'='*120}\n")
        f.write("💡 주요 발견사항 요약\n")
        f.write(f"{'='*120}\n\n")

        # 0. 🚨 어뷰징 의심 (10-11월)
        abuse_suspected = [a for a in anomalies if a['in_db'] and a['월'] in ['10월', '11월'] and
                          any('어뷰징 의심' in issue for issue in a['issues'])]
        if abuse_suspected:
            total_amount = sum(a['당월수업료'] for a in abuse_suspected if pd.notna(a['당월수업료']))
            f.write(f"🚨 어뷰징 의심 (10-11월): {len(abuse_suspected)}건\n")
            f.write(f"   총 지급액: {total_amount:,.0f}원\n")
            f.write(f"   10-11월 전월 잔여세션이 부족한데도 세션이 진행되었습니다.\n")
            f.write(f"   이용권 추가 구매 없이 진행된 것으로 의심됩니다.\n\n")
            for a in abuse_suspected[:15]:
                for issue in a['issues']:
                    if '어뷰징 의심' in issue:
                        f.write(f"   • {a['회원명']} ({a['트레이너']}, {a['월']}): {issue}\n")
                        break
            if len(abuse_suspected) > 15:
                f.write(f"   ... 외 {len(abuse_suspected)-15}건\n")
            f.write("\n")

        # 1. 세션 진행 당시 만료된 회원 중 세션 진행
        expired_sessions = [a for a in anomalies if a['in_db'] and
                          any('세션 진행 당시' in issue and '이미 만료' in issue for issue in a['issues'])]
        if expired_sessions:
            total_amount = sum(a['당월수업료'] for a in expired_sessions if pd.notna(a['당월수업료']))
            f.write(f"1. 세션 진행 당시 만료된 회원: {len(expired_sessions)}건\n")
            f.write(f"   총 지급액: {total_amount:,.0f}원\n")
            f.write(f"   세션 진행 월 기준으로 이미 회원권이 만료되었는데도 세션이 진행되었습니다.\n\n")
            for a in expired_sessions[:10]:
                expire_info = f" (만료일: {a['최종만료일']})" if pd.notna(a['최종만료일']) else ""
                f.write(f"   • {a['회원명']} ({a['트레이너']}, {a['월']}): {a['당월진행세션']:.0f}회, {a['당월수업료']:,.0f}원{expire_info}\n")
            if len(expired_sessions) > 10:
                f.write(f"   ... 외 {len(expired_sessions)-10}건\n")
            f.write("\n")

        # 2. 담당자 불일치
        trainer_mismatch = [a for a in anomalies if a['in_db'] and
                           '담당자 불일치' in str(a['issues'])]
        if trainer_mismatch:
            f.write(f"2. 담당자 불일치: {len(trainer_mismatch)}건\n")
            f.write(f"   급여 시트의 트레이너와 회원 DB의 담당자가 다릅니다.\n\n")
            for a in trainer_mismatch[:10]:
                f.write(f"   • {a['회원명']}: 급여({a['트레이너']}) ≠ DB({a['회원DB_담당자']})\n")
            if len(trainer_mismatch) > 10:
                f.write(f"   ... 외 {len(trainer_mismatch)-10}건\n")
            f.write("\n")

        # 3. 세션 종료 후 진행
        zero_remaining = [a for a in anomalies if '남은세션 0' in str(a['issues']) or '남은세션 -' in str(a['issues'])]
        if zero_remaining:
            f.write(f"3. 세션 종료 후 진행: {len(zero_remaining)}건\n")
            f.write(f"   남은 세션이 0 이하인데 당월 세션이 진행되었습니다.\n\n")
            for a in zero_remaining[:10]:
                f.write(f"   • {a['회원명']} ({a['트레이너']}): 당월 {a['당월진행세션']:.0f}회 진행\n")
            if len(zero_remaining) > 10:
                f.write(f"   ... 외 {len(zero_remaining)-10}건\n")
            f.write("\n")

        # 4. 세션 차감 이상 (비정상 증가)
        session_deduction_issues = [a for a in anomalies if '세션 차감 이상' in str(a['issues'])]
        if session_deduction_issues:
            f.write(f"4. 세션 차감 이상 (비정상 증가): {len(session_deduction_issues)}건\n")
            f.write(f"   전월 잔여 - 당월 진행 = 예상값과 실제 잔여가 다릅니다 (세션 증가).\n\n")
            for a in session_deduction_issues[:10]:
                for issue in a['issues']:
                    if '세션 차감 이상' in issue:
                        f.write(f"   • {a['회원명']} ({a['트레이너']}): {issue}\n")
                        break
            if len(session_deduction_issues) > 10:
                f.write(f"   ... 외 {len(session_deduction_issues)-10}건\n")
            f.write("\n")

        # 5. 세션 추가 차감
        session_extra_deduction = [a for a in anomalies if '세션 추가 차감' in str(a['issues'])]
        if session_extra_deduction:
            f.write(f"5. 세션 추가 차감: {len(session_extra_deduction)}건\n")
            f.write(f"   전월 잔여 - 당월 진행보다 더 많이 차감되었습니다.\n\n")
            for a in session_extra_deduction[:10]:
                for issue in a['issues']:
                    if '세션 추가 차감' in issue:
                        f.write(f"   • {a['회원명']} ({a['트레이너']}): {issue}\n")
                        break
            if len(session_extra_deduction) > 10:
                f.write(f"   ... 외 {len(session_extra_deduction)-10}건\n")
            f.write("\n")

def create_versioned_report_dir(base_dir):
    """버저닝된 보고서 디렉토리 생성"""
    reports_dir = base_dir / "pay" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    # 타임스탬프 기반 디렉토리명
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_dir = reports_dir / timestamp
    report_dir.mkdir(parents=True, exist_ok=True)

    # latest 심볼릭 링크 업데이트 (Windows에서는 복사)
    latest_link = reports_dir / "latest"
    if latest_link.exists():
        if latest_link.is_symlink():
            latest_link.unlink()
        elif latest_link.is_dir():
            shutil.rmtree(latest_link)

    try:
        # Unix/Mac에서는 심볼릭 링크
        latest_link.symlink_to(timestamp, target_is_directory=True)
    except (OSError, NotImplementedError):
        # Windows에서는 그냥 복사하지 않고 패스
        pass

    return report_dir, timestamp

def copy_comprehensive_report(base_dir, report_dir):
    """종합분석보고서를 보고서 디렉토리로 복사"""
    source = base_dir / "pay" / "Doubless_종합분석보고서.md"
    if source.exists():
        dest = report_dir / "종합분석보고서.md"
        shutil.copy(source, dest)
        print(f"✅ 종합분석보고서 복사 완료")

def main():
    """메인 함수"""
    print("="*120)
    print("💰 급여 이상건 종합 분석 (DB 기반)")
    print("="*120)

    # 경로 설정
    base_dir = Path(__file__).parent.parent
    salary_db = base_dir / "data" / "doubless.db"
    members_db = base_dir / "data" / "doubless.db"

    # 버저닝된 보고서 디렉토리 생성
    report_dir, timestamp = create_versioned_report_dir(base_dir)
    print(f"\n📁 보고서 디렉토리: reports/{timestamp}/")

    # DB 확인
    if not salary_db.exists():
        print(f"❌ 급여 DB를 찾을 수 없습니다: {salary_db}")
        return

    if not members_db.exists():
        print(f"❌ 회원 DB를 찾을 수 없습니다: {members_db}")
        return

    # 이름 매핑 규칙 로드
    print("\n📋 이름 매핑 규칙 로드 중...")
    name_rules = load_name_mapping_rules()
    print(f"✅ 정규화 규칙: {len(name_rules['normalization_rules']['rules'])}개")
    print(f"✅ 알려진 매핑: {len(name_rules['known_mappings']['mappings'])}개")

    # 데이터 로드
    print("\n📊 데이터 로드 중...")
    df = load_salary_and_members(salary_db, members_db, name_rules)
    print(f"✅ {len(df)}건의 급여 레코드 로드 완료")

    # 이름 매핑 적용 통계
    mapped_count = df['이름_매핑_적용'].sum()
    if mapped_count > 0:
        print(f"✅ 이름 매핑 적용: {mapped_count}건")
        mapped_cases = df[df['이름_매핑_적용']][['원본_회원명', '회원명_정규화']].drop_duplicates()
        for _, row in mapped_cases.iterrows():
            print(f"   • {row['원본_회원명']} → {row['회원명_정규화']}")

    # 이상건 탐지
    print("\n🔍 이상건 탐지 중...")
    anomalies = detect_anomalies(df)
    print(f"✅ {len(anomalies)}건의 이상건 발견")

    # 보고서 저장
    print(f"\n📝 보고서 생성 중...")

    # 1. 상세 텍스트 보고서
    detail_report = report_dir / "급여이상건_상세.txt"
    save_analysis_report(anomalies, detail_report)
    print(f"✅ 상세 보고서: {detail_report.name}")

    # 2. 이상건 CSV (엑셀용)
    csv_file = report_dir / "이상건_목록.csv"
    save_anomalies_csv(anomalies, csv_file)
    print(f"✅ 이상건 CSV: {csv_file.name}")

    # 3. 메타데이터 JSON
    save_metadata(report_dir, anomalies, len(df))
    print(f"✅ 메타데이터: 분석_메타데이터.json")

    # 4. 종합분석보고서 복사
    copy_comprehensive_report(base_dir, report_dir)

    # 요약 출력
    in_db = sum(1 for a in anomalies if a['in_db'])
    not_in_db = len(anomalies) - in_db

    print(f"\n" + "="*120)
    print(f"📊 분석 완료")
    print(f"="*120)
    print(f"총 급여 레코드: {len(df)}건")
    print(f"총 이상건: {len(anomalies)}건 ({len(anomalies)*100/len(df):.1f}%)")
    print(f"  • 회원 DB 존재: {in_db}건")
    print(f"  • 회원 DB 없음: {not_in_db}건")
    print(f"\n보고서 위치: {report_dir}")
    print(f"  - 급여이상건_상세.txt")
    print(f"  - 이상건_목록.csv")
    print(f"  - 분석_메타데이터.json")
    print(f"  - 종합분석보고서.md")

if __name__ == "__main__":
    main()
