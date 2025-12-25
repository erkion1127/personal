#!/usr/bin/env python3
"""
급여 분석 보고서와 회원 DB를 교차 분석하는 프로그램

급여 이상건에 포함된 회원들의 상세 정보를 회원 DB에서 조회하여
더 상세한 분석 보고서를 생성합니다.
"""

import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime
from collections import defaultdict

def load_member_db(db_path):
    """회원 데이터베이스 로드"""
    conn = sqlite3.connect(db_path)
    query = """
        SELECT 이름, 상태, 연락처, 보유이용권, 최종만료일, 남은일수,
               최근구매일, 최근출석일, 상담담당자, 성별, 나이
        FROM members
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def analyze_excel_file(file_path):
    """엑셀 파일 분석"""
    try:
        excel_file = pd.ExcelFile(file_path)
        all_data = {}

        for sheet_name in excel_file.sheet_names:
            df = pd.read_excel(file_path, sheet_name=sheet_name, header=2)
            df = df.dropna(how='all')

            if 'NO.' in df.columns:
                df = df[pd.to_numeric(df['NO.'], errors='coerce').notna()]

            all_data[sheet_name] = df

        return all_data
    except Exception as e:
        print(f"오류 발생: {e}")
        return None

def find_column_name(columns, keywords):
    """컬럼명 찾기"""
    for col in columns:
        col_str = str(col).lower()
        for keyword in keywords:
            if keyword in col_str:
                return col
    return None

def detect_anomalies_with_member_info(data, month, previous_month_data, members_df):
    """이상 징후 탐지 (회원 정보 포함)"""
    anomalies = []

    for trainer_name, df in data.items():
        # 컬럼명 찾기
        col_member = find_column_name(df.columns, ['회원명', '이름', '회원'])
        col_current_sessions = find_column_name(df.columns, ['당월', '진행', '수업'])
        col_remaining_sessions = find_column_name(df.columns, ['남은', '잔여'])

        if not all([col_member, col_current_sessions, col_remaining_sessions]):
            continue

        # 각 회원별로 검사
        for idx, row in df.iterrows():
            member_name = row[col_member]
            current = row[col_current_sessions]
            remaining = row[col_remaining_sessions]

            if pd.isna(member_name) or str(member_name).strip() == '':
                continue

            try:
                current = float(current) if not pd.isna(current) else 0
                remaining = float(remaining) if not pd.isna(remaining) else 0
            except:
                continue

            issues = []

            # 1. 당월 진행이 있는데 남은 세션이 0 또는 음수
            if current > 0 and remaining <= 0:
                issues.append(f"당월 {current}회 진행했으나 남은 세션 {remaining}회")

            # 2. 전월 데이터와 비교
            if previous_month_data and trainer_name in previous_month_data:
                prev_df = previous_month_data[trainer_name]
                prev_col_member = find_column_name(prev_df.columns, ['회원명', '이름', '회원'])
                prev_col_remaining = find_column_name(prev_df.columns, ['남은', '잔여'])

                if prev_col_member and prev_col_remaining:
                    prev_row = prev_df[prev_df[prev_col_member] == member_name]
                    if not prev_row.empty:
                        prev_remaining = prev_row.iloc[0][prev_col_remaining]
                        try:
                            prev_remaining = float(prev_remaining) if not pd.isna(prev_remaining) else 0

                            if current > prev_remaining and prev_remaining > 0:
                                issues.append(f"전월 잔여 {prev_remaining}회인데 당월 {current}회 진행")

                            if current > 0 and remaining > prev_remaining:
                                increase = remaining - prev_remaining
                                issues.append(f"당월 {current}회 진행했는데 잔여세션 {increase}회 증가 ({prev_remaining}→{remaining})")
                        except:
                            pass

            if issues:
                # 회원 DB에서 정보 조회
                member_info = members_df[members_df['이름'] == member_name]

                if not member_info.empty:
                    member_record = member_info.iloc[0]
                    anomaly = {
                        'month': month,
                        'trainer': trainer_name,
                        'member': member_name,
                        'current_sessions': current,
                        'remaining_sessions': remaining,
                        'issues': issues,
                        # 회원 DB 정보 추가
                        'member_status': member_record['상태'],
                        'phone': member_record['연락처'],
                        'product': member_record['보유이용권'],
                        'expire_date': member_record['최종만료일'],
                        'days_left': member_record['남은일수'],
                        'last_purchase': member_record['최근구매일'],
                        'last_visit': member_record['최근출석일'],
                        'db_trainer': member_record['상담담당자'],
                        'gender': member_record['성별'],
                        'age': member_record['나이'],
                        'in_db': True
                    }
                else:
                    # DB에 없는 회원
                    anomaly = {
                        'month': month,
                        'trainer': trainer_name,
                        'member': member_name,
                        'current_sessions': current,
                        'remaining_sessions': remaining,
                        'issues': issues,
                        'in_db': False
                    }

                anomalies.append(anomaly)

    return anomalies

def save_cross_analysis_report(anomalies, members_df, output_path):
    """교차 분석 보고서 저장"""
    from datetime import datetime as dt

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("="*100 + "\n")
        f.write("Doubless 급여 이상건 교차 분석 보고서 (급여 데이터 + 회원 DB)\n")
        f.write(f"생성일시: {dt.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*100 + "\n\n")

        # 전체 통계
        total_anomalies = len(anomalies)
        in_db = sum(1 for a in anomalies if a.get('in_db', False))
        not_in_db = total_anomalies - in_db

        f.write(f"📊 전체 통계\n")
        f.write(f"{'='*100}\n")
        f.write(f"총 이상건: {total_anomalies}건\n")
        f.write(f"  - 회원 DB에 존재: {in_db}건 ({in_db*100/total_anomalies:.1f}%)\n")
        f.write(f"  - 회원 DB에 없음: {not_in_db}건 ({not_in_db*100/total_anomalies:.1f}%)\n\n")

        # DB에 없는 회원 리스트
        if not_in_db > 0:
            f.write(f"\n⚠️  회원 DB에 없는 회원 ({not_in_db}건)\n")
            f.write(f"{'='*100}\n")
            f.write("급여 데이터에는 있지만 회원 DB에서 찾을 수 없는 회원들입니다.\n")
            f.write("이름 오타, 탈퇴 회원, 또는 데이터 동기화 문제일 수 있습니다.\n\n")

            not_in_db_list = [a for a in anomalies if not a.get('in_db', False)]
            for idx, a in enumerate(not_in_db_list, 1):
                f.write(f"{idx}. [{a['month']}월] {a['trainer']} 트레이너 - {a['member']}\n")
                f.write(f"   당월 진행: {a['current_sessions']}회, 남은 세션: {a['remaining_sessions']}회\n")

        # 월별 상세 분석
        f.write(f"\n\n{'='*100}\n")
        f.write("📅 월별 상세 분석\n")
        f.write(f"{'='*100}\n\n")

        month_summary = defaultdict(list)
        for anomaly in anomalies:
            if anomaly.get('in_db', False):
                month_summary[anomaly['month']].append(anomaly)

        for month in sorted(month_summary.keys()):
            month_anomalies = month_summary[month]
            f.write(f"\n{'='*100}\n")
            f.write(f"[{month}월] - {len(month_anomalies)}건\n")
            f.write(f"{'='*100}\n\n")

            trainer_summary = defaultdict(list)
            for a in month_anomalies:
                trainer_summary[a['trainer']].append(a)

            for trainer, trainer_anomalies in trainer_summary.items():
                f.write(f"\n{trainer} 트레이너: {len(trainer_anomalies)}건\n")
                f.write("-" * 100 + "\n\n")

                for idx, a in enumerate(trainer_anomalies, 1):
                    f.write(f"{idx}. {a['member']}\n")
                    f.write(f"   {'─'*90}\n")

                    # 급여 데이터
                    f.write(f"   [급여 데이터]\n")
                    f.write(f"   • 당월 진행 세션: {a['current_sessions']}회\n")
                    f.write(f"   • 남은 세션: {a['remaining_sessions']}회\n")
                    f.write(f"   • 문제점:\n")
                    for issue in a['issues']:
                        f.write(f"     - {issue}\n")

                    # 회원 DB 정보
                    f.write(f"\n   [회원 DB 정보]\n")
                    f.write(f"   • 회원 상태: {a['member_status']}\n")
                    f.write(f"   • 연락처: {a['phone']}\n")
                    f.write(f"   • 성별/나이: {a['gender']}/{a['age']}세\n")
                    f.write(f"   • 보유 이용권: {a['product']}\n")
                    f.write(f"   • 최종 만료일: {a['expire_date']} (D-{a['days_left']})\n")
                    f.write(f"   • 최근 구매일: {a['last_purchase']}\n")
                    f.write(f"   • 최근 출석일: {a['last_visit']}\n")
                    f.write(f"   • DB상 담당자: {a['db_trainer']}\n")

                    # 담당자 불일치 체크
                    if str(a['db_trainer']) != str(trainer) and a['db_trainer'] not in ['-', None, '']:
                        f.write(f"\n   ⚠️  담당자 불일치: 급여({trainer}) ≠ DB({a['db_trainer']})\n")

                    f.write("\n")

        # 주요 발견사항 요약
        f.write(f"\n\n{'='*100}\n")
        f.write("💡 주요 발견사항\n")
        f.write(f"{'='*100}\n\n")

        # 1. 만료된 회원 중 세션 진행
        expired_with_sessions = [a for a in anomalies if a.get('in_db') and a.get('member_status') == '만료']
        if expired_with_sessions:
            f.write(f"1. 만료된 회원 중 세션 진행: {len(expired_with_sessions)}건\n")
            f.write("   만료 상태임에도 세션이 진행되고 있는 회원들입니다.\n\n")
            for a in expired_with_sessions[:10]:  # 상위 10건만
                f.write(f"   • {a['member']} ({a['trainer']}) - 당월 {a['current_sessions']}회 진행\n")
            if len(expired_with_sessions) > 10:
                f.write(f"   ... 외 {len(expired_with_sessions)-10}건\n")
            f.write("\n")

        # 2. 담당자 불일치
        trainer_mismatch = [a for a in anomalies if a.get('in_db') and
                           str(a.get('db_trainer')) != str(a['trainer']) and
                           a.get('db_trainer') not in ['-', None, '']]
        if trainer_mismatch:
            f.write(f"2. 담당자 불일치: {len(trainer_mismatch)}건\n")
            f.write("   급여 시트의 트레이너와 회원 DB의 상담담당자가 다릅니다.\n\n")
            for a in trainer_mismatch[:10]:
                f.write(f"   • {a['member']}: 급여({a['trainer']}) ≠ DB({a['db_trainer']})\n")
            if len(trainer_mismatch) > 10:
                f.write(f"   ... 외 {len(trainer_mismatch)-10}건\n")
            f.write("\n")

        # 3. 장기 미출석 중 세션 진행
        from datetime import datetime, timedelta
        no_recent_visit = []
        for a in anomalies:
            if a.get('in_db') and a.get('last_visit'):
                try:
                    last_visit = datetime.strptime(str(a['last_visit']), '%Y-%m-%d')
                    days_since_visit = (datetime.now() - last_visit).days
                    if days_since_visit > 30:
                        no_recent_visit.append((a, days_since_visit))
                except:
                    pass

        if no_recent_visit:
            no_recent_visit.sort(key=lambda x: x[1], reverse=True)
            f.write(f"3. 장기 미출석 중 세션 진행: {len(no_recent_visit)}건\n")
            f.write("   최근 출석이 30일 이상 없는데 세션이 진행되고 있습니다.\n\n")
            for a, days in no_recent_visit[:10]:
                f.write(f"   • {a['member']} ({a['trainer']}) - 마지막 출석: {days}일 전\n")
            if len(no_recent_visit) > 10:
                f.write(f"   ... 외 {len(no_recent_visit)-10}건\n")
            f.write("\n")

def main():
    """메인 함수"""
    print("="*100)
    print("🔄 급여 데이터 + 회원 DB 교차 분석 시작")
    print("="*100)

    # 경로 설정
    base_dir = Path(__file__).parent.parent
    db_file = base_dir / "data" / "members.db"
    pay_dir = base_dir / "pay" / "2025"

    # 회원 DB 로드
    print(f"\n📊 회원 DB 로드 중: {db_file}")
    if not db_file.exists():
        print(f"❌ 회원 DB를 찾을 수 없습니다: {db_file}")
        return

    members_df = load_member_db(db_file)
    print(f"✅ {len(members_df)}명의 회원 정보 로드 완료")

    # 급여 파일 찾기
    excel_files = sorted(pay_dir.glob("*.xlsx"))
    if not excel_files:
        print(f"❌ 급여 파일을 찾을 수 없습니다: {pay_dir}")
        return

    print(f"\n📁 {len(excel_files)}개 급여 파일 발견")

    # 각 파일 분석
    all_anomalies = []
    previous_month_data = None

    for file_path in excel_files:
        month = file_path.stem.split()[0]  # "6월", "7월" 등
        print(f"\n분석 중: {month}...")

        data = analyze_excel_file(file_path)
        if data:
            anomalies = detect_anomalies_with_member_info(data, month, previous_month_data, members_df)
            all_anomalies.extend(anomalies)
            previous_month_data = data

    print(f"\n✅ 분석 완료: 총 {len(all_anomalies)}건의 이상 징후 발견")

    # 교차 분석 보고서 저장
    output_path = base_dir / "pay" / "급여이상건_교차분석보고서.txt"
    save_cross_analysis_report(all_anomalies, members_df, output_path)

    print(f"\n✅ 교차 분석 보고서 저장 완료: {output_path}")

    # 요약 출력
    in_db = sum(1 for a in all_anomalies if a.get('in_db', False))
    not_in_db = len(all_anomalies) - in_db

    print(f"\n📊 요약:")
    print(f"  • 총 이상건: {len(all_anomalies)}건")
    print(f"  • 회원 DB 존재: {in_db}건")
    print(f"  • 회원 DB 없음: {not_in_db}건")

if __name__ == "__main__":
    main()
