#!/usr/bin/env python3
"""
Doubless 급여 엑셀 파일 분석 스크립트
6월~11월 트레이너 급여 데이터를 분석하여 이상 징후를 탐지합니다.

엑셀 파일 구조:
- 각 시트 = 트레이너 이름 (예: 이준수, 한길수, 신지훈, 이현수)
- 주요 컬럼:
  * 회원명: 담당 회원 이름
  * 당월 진행 세션: 해당 월에 실제 진행한 수업 횟수
  * 남은 세션: 정산 후 남은 총 수업 횟수
  * 수업료/단가: 1회 수업당 금액
  * 총 급여/지급액: 최종 지급 금액
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
import sys
from collections import defaultdict

def analyze_excel_file(file_path):
    """엑셀 파일 분석"""
    print(f"\n{'='*80}")
    print(f"📄 파일: {file_path.name}")
    print(f"{'='*80}")

    try:
        # 엑셀 파일 읽기 (모든 시트)
        excel_file = pd.ExcelFile(file_path)
        print(f"✅ 총 {len(excel_file.sheet_names)}개 시트 발견: {', '.join(excel_file.sheet_names)}")

        all_data = {}
        for sheet_name in excel_file.sheet_names:
            # header=2를 사용하여 3번째 행을 헤더로 인식 (NO., 회원명, 성별... 있는 행)
            df = pd.read_excel(file_path, sheet_name=sheet_name, header=2)

            # 빈 행 제거
            df = df.dropna(how='all')

            # NO. 컬럼이 숫자인 행만 필터링 (실제 데이터 행)
            if 'NO.' in df.columns:
                df = df[pd.to_numeric(df['NO.'], errors='coerce').notna()]

            all_data[sheet_name] = df

            print(f"\n📊 [{sheet_name}] 시트 정보:")
            print(f"   - 데이터 행 수: {len(df)}")
            print(f"   - 컬럼: {list(df.columns)}")

        return all_data

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return None

def find_column_name(columns, keywords):
    """컬럼명 찾기 - 다양한 표현을 지원"""
    for col in columns:
        col_str = str(col).lower()
        for keyword in keywords:
            if keyword in col_str:
                return col
    return None

def detect_anomalies(data, month, previous_month_data=None):
    """이상 징후 탐지

    탐지 항목:
    1. 당월 진행 세션이 있는데 남은 세션이 줄지 않은 경우
    2. 남은 세션이 0인데 당월 진행 세션이 있는 경우
    3. 전월 대비 남은 세션이 비정상적으로 증가한 경우
    4. 당월 진행 세션 > 전월 남은 세션인 경우
    """
    print(f"\n🔍 [{month}월] 이상 징후 탐지 중...")
    anomalies = []

    # 각 시트(트레이너)별로 분석
    for trainer_name, df in data.items():
        print(f"\n   📋 트레이너: {trainer_name}")

        # 컬럼명 찾기
        col_member = find_column_name(df.columns, ['회원명', '이름', '회원'])
        col_current_sessions = find_column_name(df.columns, ['당월', '진행', '수업'])
        col_remaining_sessions = find_column_name(df.columns, ['남은', '잔여'])

        if not all([col_member, col_current_sessions, col_remaining_sessions]):
            print(f"      ⚠️  필수 컬럼을 찾을 수 없습니다.")
            print(f"         - 회원명: {col_member}")
            print(f"         - 당월 진행: {col_current_sessions}")
            print(f"         - 남은 세션: {col_remaining_sessions}")
            continue

        print(f"      ✅ 컬럼 매핑:")
        print(f"         - 회원명: {col_member}")
        print(f"         - 당월 진행: {col_current_sessions}")
        print(f"         - 남은 세션: {col_remaining_sessions}")

        # 각 회원별로 검사
        issue_count = 0
        for idx, row in df.iterrows():
            member_name = row[col_member]
            current = row[col_current_sessions]
            remaining = row[col_remaining_sessions]

            # NaN이나 빈 값 처리
            if pd.isna(member_name) or str(member_name).strip() == '':
                continue

            try:
                current = float(current) if not pd.isna(current) else 0
                remaining = float(remaining) if not pd.isna(remaining) else 0
            except:
                continue

            # 이상 징후 체크
            issues = []

            # 1. 당월 진행이 있는데 남은 세션이 0 또는 음수
            if current > 0 and remaining <= 0:
                issues.append(f"당월 {current}회 진행했으나 남은 세션 {remaining}회")

            # 2. 전월 데이터와 비교 (있는 경우)
            if previous_month_data and trainer_name in previous_month_data:
                prev_df = previous_month_data[trainer_name]
                prev_col_member = find_column_name(prev_df.columns, ['회원명', '이름', '회원'])
                prev_col_remaining = find_column_name(prev_df.columns, ['남은', '잔여'])

                if prev_col_member and prev_col_remaining:
                    # 동일 회원 찾기
                    prev_row = prev_df[prev_df[prev_col_member] == member_name]
                    if not prev_row.empty:
                        prev_remaining = prev_row.iloc[0][prev_col_remaining]
                        try:
                            prev_remaining = float(prev_remaining) if not pd.isna(prev_remaining) else 0

                            # 전월 남은 세션보다 당월 진행 세션이 많은 경우
                            if current > prev_remaining and prev_remaining > 0:
                                issues.append(f"전월 잔여 {prev_remaining}회인데 당월 {current}회 진행")

                            # 당월 진행했는데 남은 세션이 비정상적으로 증가
                            if current > 0 and remaining > prev_remaining:
                                increase = remaining - prev_remaining
                                issues.append(f"당월 {current}회 진행했는데 잔여세션 {increase}회 증가 ({prev_remaining}→{remaining})")

                        except:
                            pass

            if issues:
                issue_count += 1
                anomaly = {
                    'month': month,
                    'trainer': trainer_name,
                    'member': member_name,
                    'current_sessions': current,
                    'remaining_sessions': remaining,
                    'issues': issues
                }
                anomalies.append(anomaly)

                print(f"      ⚠️  {member_name}:")
                for issue in issues:
                    print(f"         - {issue}")

        if issue_count == 0:
            print(f"      ✅ 이상 징후 없음")
        else:
            print(f"      📊 총 {issue_count}건의 이상 징후 발견")

    return anomalies

def main():
    """메인 함수"""
    print("="*80)
    print("🏋️  Doubless 급여 데이터 분석 시작")
    print("="*80)

    # 2025년 급여 파일 디렉토리
    base_dir = Path(__file__).parent.parent / "pay" / "2025"

    if not base_dir.exists():
        print(f"❌ 디렉토리를 찾을 수 없습니다: {base_dir}")
        sys.exit(1)

    # 엑셀 파일 목록 찾기
    excel_files = sorted(base_dir.glob("*.xlsx"))

    if not excel_files:
        print(f"❌ 엑셀 파일을 찾을 수 없습니다: {base_dir}")
        sys.exit(1)

    print(f"\n📁 총 {len(excel_files)}개 파일 발견:")
    for f in excel_files:
        print(f"   - {f.name}")

    # 각 파일 분석 (월 순서대로)
    all_results = {}
    all_anomalies = []
    previous_month_data = None

    for file_path in excel_files:
        # 파일명에서 월 추출
        month = file_path.stem.split()[0]  # 예: "6월트레이너 급여 목포" -> "6월"

        data = analyze_excel_file(file_path)
        if data:
            all_results[month] = data
            # 이상 징후 탐지 (전월 데이터와 비교)
            anomalies = detect_anomalies(data, month, previous_month_data)
            all_anomalies.extend(anomalies)

            # 다음 반복을 위해 현재 데이터 저장
            previous_month_data = data

    print("\n" + "="*80)
    print("✅ 분석 완료!")
    print("="*80)

    # 결과 요약
    print(f"\n📊 분석 완료된 파일: {len(all_results)}개")
    for month in all_results.keys():
        print(f"   - {month}")

    print(f"\n⚠️  총 {len(all_anomalies)}건의 이상 징후 발견")

    # 월별 이상 징후 요약
    if all_anomalies:
        print("\n" + "="*80)
        print("📋 월별 이상 징후 요약")
        print("="*80)

        month_summary = defaultdict(list)
        for anomaly in all_anomalies:
            month_summary[anomaly['month']].append(anomaly)

        for month, anomalies in month_summary.items():
            print(f"\n[{month}월] - {len(anomalies)}건")
            trainer_summary = defaultdict(list)
            for a in anomalies:
                trainer_summary[a['trainer']].append(a)

            for trainer, trainer_anomalies in trainer_summary.items():
                print(f"\n  {trainer} 트레이너: {len(trainer_anomalies)}건")
                for a in trainer_anomalies:
                    print(f"    - {a['member']}")
                    for issue in a['issues']:
                        print(f"      · {issue}")

    # 보고서 파일 저장
    save_report(all_anomalies, base_dir.parent / "급여이상건_분석보고서.txt")

def save_report(anomalies, output_path):
    """분석 결과를 텍스트 파일로 저장"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("Doubless 급여 이상건 분석 보고서\n")
        f.write(f"생성일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*80 + "\n\n")

        f.write(f"총 {len(anomalies)}건의 이상 징후 발견\n\n")

        if anomalies:
            month_summary = defaultdict(list)
            for anomaly in anomalies:
                month_summary[anomaly['month']].append(anomaly)

            for month, month_anomalies in month_summary.items():
                f.write(f"\n{'='*80}\n")
                f.write(f"[{month}월] - {len(month_anomalies)}건\n")
                f.write(f"{'='*80}\n\n")

                trainer_summary = defaultdict(list)
                for a in month_anomalies:
                    trainer_summary[a['trainer']].append(a)

                for trainer, trainer_anomalies in trainer_summary.items():
                    f.write(f"\n{trainer} 트레이너: {len(trainer_anomalies)}건\n")
                    f.write("-" * 60 + "\n")

                    for idx, a in enumerate(trainer_anomalies, 1):
                        f.write(f"\n{idx}. {a['member']}\n")
                        f.write(f"   당월 진행: {a['current_sessions']}회\n")
                        f.write(f"   남은 세션: {a['remaining_sessions']}회\n")
                        f.write(f"   문제점:\n")
                        for issue in a['issues']:
                            f.write(f"     - {issue}\n")

    print(f"\n✅ 보고서 저장 완료: {output_path}")

if __name__ == "__main__":
    main()