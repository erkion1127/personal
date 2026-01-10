#!/usr/bin/env python3
"""
급여 엑셀 파일을 DB에 업로드하는 프로그램

엑셀 파일 구조:
- 각 시트 = 트레이너 이름
- header=2 (3번째 행이 헤더)
"""

import pandas as pd
import sqlite3
from pathlib import Path
from datetime import datetime
import sys


def find_column_name(columns, keywords):
    """컬럼명 찾기 - 다양한 표현을 지원 (줄바꿈 제거)"""
    for col in columns:
        # 줄바꿈 제거하고 소문자로 변환
        col_str = str(col).replace('\n', '').replace(' ', '').lower()
        for keyword in keywords:
            keyword_clean = keyword.replace(' ', '').lower()
            if keyword_clean in col_str:
                return col
    return None


def read_excel_file(file_path):
    """엑셀 파일 읽기"""
    print(f"\n{'='*80}")
    print(f"📄 파일 읽기: {file_path.name}")
    print(f"{'='*80}")

    try:
        excel_file = pd.ExcelFile(file_path)
        print(f"✅ 총 {len(excel_file.sheet_names)}개 시트 발견: {', '.join(excel_file.sheet_names)}")

        all_data = {}
        for sheet_name in excel_file.sheet_names:
            # header=2를 사용하여 3번째 행을 헤더로 인식
            df = pd.read_excel(file_path, sheet_name=sheet_name, header=2)

            # 빈 행 제거
            df = df.dropna(how='all')

            # NO. 컬럼이 숫자인 행만 필터링 (실제 데이터 행)
            if 'NO.' in df.columns:
                df = df[pd.to_numeric(df['NO.'], errors='coerce').notna()]

            all_data[sheet_name] = df
            print(f"   - [{sheet_name}] {len(df)}건")

        return all_data

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return None


def read_sales_data(file_path):
    """엑셀 파일에서 O, P, Q열(14, 15, 16)의 매출 데이터 읽기

    엑셀 구조:
    - 0행: 총 수업수, 잔여세션, 개인매출 (헤더)
    - 1행: 요약값 (80, 230, 8860000)
    - 2행: 이달의매출 (섹션 헤더)
    - 3행~: 실제 회원별 매출 데이터 (회원명, 결제형태, 금액)
    """
    print(f"\n{'='*80}")
    print(f"📊 매출 데이터 읽기: {file_path.name}")
    print(f"{'='*80}")

    try:
        excel_file = pd.ExcelFile(file_path)

        all_sales = {}
        for sheet_name in excel_file.sheet_names:
            # 헤더 없이 전체 읽기
            df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)

            # O, P, Q열 (14, 15, 16) 추출
            # 4행(인덱스 3)부터 매출 데이터 시작
            sales_list = []
            total_sales = 0

            for idx in range(3, len(df)):
                member_name = df.iloc[idx, 14]  # O열: 회원명
                payment_type = df.iloc[idx, 15]  # P열: 결제형태
                sales_amount = df.iloc[idx, 16]  # Q열: 매출금액

                # 유효한 매출 데이터만 처리 (회원명이 있고 금액이 숫자인 경우)
                if pd.notna(member_name) and pd.notna(sales_amount):
                    # 회원명이 특수 헤더가 아닌 경우만 처리
                    member_str = str(member_name).strip()
                    # 제외할 키워드 목록
                    exclude_keywords = ['이달의매출', '인계 매출', '총 매출', '합계', '달성', '기본급', '수업료', '급여']
                    is_valid = member_str and not any(kw in member_str for kw in exclude_keywords)
                    if is_valid:
                        try:
                            amount = float(sales_amount)
                            sales_list.append({
                                'member_name': member_str,
                                'payment_type': str(payment_type) if pd.notna(payment_type) else None,
                                'amount': amount
                            })
                            total_sales += amount
                        except (ValueError, TypeError):
                            pass

            all_sales[sheet_name] = {
                'sales_list': sales_list,
                'total_sales': total_sales
            }
            print(f"   - [{sheet_name}] 매출 {len(sales_list)}건, 총액: {total_sales:,.0f}원")

        return all_sales

    except Exception as e:
        print(f"❌ 매출 데이터 읽기 오류: {e}")
        import traceback
        traceback.print_exc()
        return None


def extract_month_from_filename(filename):
    """파일명에서 월 추출"""
    # 예: "12월 트레이너 급여 목포.xlsx" -> "12월"
    # "6월트레이너 급여 목포.xlsx" -> "6월"
    import re
    match = re.search(r'(\d+월)', filename)
    if match:
        return match.group(1)
    return None


def save_to_db(data, year, month, db_path):
    """데이터를 DB에 저장 (중복 회원은 합산)"""
    print(f"\n{'='*80}")
    print(f"💾 DB 저장: {year}년 {month}")
    print(f"{'='*80}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 기존 데이터 삭제 (중복 방지)
    cursor.execute("DELETE FROM salary_records WHERE 년도 = ? AND 월 = ?", (year, month))
    deleted_count = cursor.rowcount
    if deleted_count > 0:
        print(f"⚠️  기존 데이터 {deleted_count}건 삭제")

    total_inserted = 0

    for trainer_name, df in data.items():
        print(f"\n   📋 트레이너: {trainer_name}")

        # 컬럼명 찾기
        col_no = find_column_name(df.columns, ['no.', 'no', '번호'])
        col_member = find_column_name(df.columns, ['회원명', '이름', '회원'])
        col_gender = find_column_name(df.columns, ['성별'])
        col_total_sessions = find_column_name(df.columns, ['등록세션', '등록 세션'])
        col_completed_sessions = find_column_name(df.columns, ['총진행세션', '총 진행 세션', '총진행'])
        col_remaining_sessions = find_column_name(df.columns, ['남은세션', '남은 세션', '남은'])
        col_payment_type = find_column_name(df.columns, ['결제형태', '결제'])
        col_registration_fee = find_column_name(df.columns, ['등록비용', '등록 비용'])
        col_supply_price = find_column_name(df.columns, ['공급가'])
        col_unit_price = find_column_name(df.columns, ['회단가', '회 단가', '단가'])
        col_revenue_rate = find_column_name(df.columns, ['매출대비율', '매출 대비율'])
        col_tuition_settlement = find_column_name(df.columns, ['수업료_정산', '정산'])
        # '수업료'는 tuition_settlement이고, '수업료.1'이 당월수업료임
        if col_tuition_settlement is None:
            for col in df.columns:
                if str(col).replace('\n', '').replace(' ', '') == '수업료' and not '.1' in str(col):
                    col_tuition_settlement = col
                    break

        col_current_sessions = find_column_name(df.columns, ['당월진행세션', '당월 진행 세션', '당월진행', '당월 진행'])
        col_current_tuition = find_column_name(df.columns, ['당월수업료', '당월 수업료'])
        # '수업료.1'이 당월수업료
        if col_current_tuition is None:
            for col in df.columns:
                if '수업료.1' in str(col):
                    col_current_tuition = col
                    break
        col_monthly_revenue = find_column_name(df.columns, ['이달의매출', '이달의 매출', '매출'])

        # 필수 컬럼 확인
        if not col_member:
            print(f"      ⚠️  회원명 컬럼을 찾을 수 없습니다. 스킵합니다.")
            continue

        # 중복 회원 그룹화 및 합산
        member_data = {}
        duplicate_count = 0

        for idx, row in df.iterrows():
            member_name = row[col_member]

            # NaN이나 빈 값 처리
            if pd.isna(member_name) or str(member_name).strip() == '':
                continue

            member_name = str(member_name).strip()

            # 데이터 추출 (안전하게)
            def safe_get(col_name):
                if col_name and col_name in row.index:
                    value = row[col_name]
                    if pd.isna(value):
                        return 0.0 if col_name in [col_total_sessions, col_completed_sessions, col_remaining_sessions,
                                                     col_registration_fee, col_supply_price, col_unit_price,
                                                     col_revenue_rate, col_tuition_settlement, col_current_sessions,
                                                     col_current_tuition, col_monthly_revenue] else None
                    return value
                return 0.0 if col_name in [col_total_sessions, col_completed_sessions, col_remaining_sessions,
                                             col_registration_fee, col_supply_price, col_unit_price,
                                             col_revenue_rate, col_tuition_settlement, col_current_sessions,
                                             col_current_tuition, col_monthly_revenue] else None

            # 회원별로 데이터 누적
            if member_name not in member_data:
                member_data[member_name] = {
                    'gender': safe_get(col_gender),
                    'payment_type': safe_get(col_payment_type),
                    'total_sessions': 0.0,
                    'completed_sessions': 0.0,
                    'remaining_sessions': 0.0,
                    'registration_fee': 0.0,
                    'supply_price': 0.0,
                    'unit_price': 0.0,
                    'revenue_rate': 0.0,
                    'tuition_settlement': 0.0,
                    'current_sessions': 0.0,
                    'current_tuition': 0.0,
                    'monthly_revenue': 0.0,
                    'count': 0
                }
            else:
                duplicate_count += 1

            # 수치 값들 누적 (안전하게 변환)
            def safe_float(value):
                try:
                    return float(value) if value else 0.0
                except (ValueError, TypeError):
                    return 0.0

            member_data[member_name]['total_sessions'] += safe_float(safe_get(col_total_sessions))
            member_data[member_name]['completed_sessions'] += safe_float(safe_get(col_completed_sessions))
            member_data[member_name]['remaining_sessions'] += safe_float(safe_get(col_remaining_sessions))
            member_data[member_name]['registration_fee'] += safe_float(safe_get(col_registration_fee))
            member_data[member_name]['supply_price'] += safe_float(safe_get(col_supply_price))
            member_data[member_name]['tuition_settlement'] += safe_float(safe_get(col_tuition_settlement))
            member_data[member_name]['current_sessions'] += safe_float(safe_get(col_current_sessions))
            member_data[member_name]['current_tuition'] += safe_float(safe_get(col_current_tuition))
            member_data[member_name]['monthly_revenue'] += safe_float(safe_get(col_monthly_revenue))
            member_data[member_name]['count'] += 1

            # 회단가, 매출대비율은 평균 (또는 마지막 값 사용)
            unit_price = safe_get(col_unit_price)
            revenue_rate = safe_get(col_revenue_rate)
            if unit_price:
                member_data[member_name]['unit_price'] = safe_float(unit_price)
            if revenue_rate:
                member_data[member_name]['revenue_rate'] = safe_float(revenue_rate)

        if duplicate_count > 0:
            print(f"      📊 중복 회원 {duplicate_count}건 합산")

        # DB에 저장
        insert_count = 0
        for member_name, data_dict in member_data.items():
            try:
                cursor.execute("""
                    INSERT INTO salary_records (
                        년도, 월, 트레이너, NO, 회원명, 성별,
                        등록세션, 총진행세션, 남은세션,
                        결제형태, 등록비용, 공급가, 회단가, 매출대비율,
                        수업료_정산, 당월진행세션, 당월수업료, 이달의매출
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    year,
                    month,
                    trainer_name,
                    None,  # NO는 합산 시 의미 없음
                    member_name,
                    data_dict['gender'],
                    data_dict['total_sessions'],
                    data_dict['completed_sessions'],
                    data_dict['remaining_sessions'],
                    data_dict['payment_type'],
                    data_dict['registration_fee'],
                    data_dict['supply_price'],
                    data_dict['unit_price'],
                    data_dict['revenue_rate'],
                    data_dict['tuition_settlement'],
                    data_dict['current_sessions'],
                    data_dict['current_tuition'],
                    data_dict['monthly_revenue']
                ))
                insert_count += 1
                total_inserted += 1

            except sqlite3.Error as e:
                print(f"      ❌ 삽입 실패 ({member_name}): {e}")

        print(f"      ✅ {insert_count}건 저장 (원본 {len(df)}건 → 합산 {insert_count}건)")

    conn.commit()
    conn.close()

    print(f"\n✅ 총 {total_inserted}건 저장 완료")
    return total_inserted


def save_sales_to_db(sales_data, year, month, db_path):
    """매출 데이터를 trainer_monthly_salary 테이블에 저장"""
    print(f"\n{'='*80}")
    print(f"💰 매출 데이터 DB 저장: {year}년 {month}")
    print(f"{'='*80}")

    # 월 문자열에서 숫자 추출 (예: "12월" -> 12)
    import re
    month_num = int(re.search(r'(\d+)', month).group(1))

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # employees 테이블에서 트레이너 목록 가져오기
    cursor.execute("SELECT id, name FROM employees WHERE job_type = '트레이너'")
    trainer_map = {row[1]: row[0] for row in cursor.fetchall()}

    updated_count = 0

    for trainer_name, sales_info in sales_data.items():
        total_sales = sales_info['total_sales']
        sales_count = len(sales_info['sales_list'])

        if total_sales > 0:
            # employee_id 찾기
            employee_id = trainer_map.get(trainer_name)

            # trainer_monthly_salary 테이블에 월별 매출 업데이트 또는 삽입
            cursor.execute("""
                INSERT INTO trainer_monthly_salary (employee_id, trainer_name, year, month, monthly_revenue)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(trainer_name, year, month)
                DO UPDATE SET monthly_revenue = excluded.monthly_revenue,
                              employee_id = excluded.employee_id
            """, (employee_id, trainer_name, year, month_num, total_sales))
            updated_count += 1
            print(f"   ✅ [{trainer_name}] (id={employee_id}) 매출 {sales_count}건, {total_sales:,.0f}원 저장")

    conn.commit()
    conn.close()

    print(f"\n✅ 총 {updated_count}명 트레이너 매출 저장 완료")
    return updated_count


def main():
    """메인 함수"""
    print("="*80)
    print("급여 데이터 DB 업로드")
    print("="*80)

    # 파일 경로 확인
    if len(sys.argv) < 2:
        print("\n사용법: python upload_salary_to_db.py <엑셀파일경로> [년도]")
        print("\n예시:")
        print("  python upload_salary_to_db.py '../pay/2025/12월 트레이너 급여 목포.xlsx'")
        print("  python upload_salary_to_db.py '../pay/2025/12월 트레이너 급여 목포.xlsx' 2025")
        sys.exit(1)

    file_path = Path(sys.argv[1])
    year = int(sys.argv[2]) if len(sys.argv) > 2 else 2025

    # 파일 존재 확인
    if not file_path.exists():
        print(f"❌ 파일을 찾을 수 없습니다: {file_path}")
        sys.exit(1)

    # 월 추출
    month = extract_month_from_filename(file_path.name)
    if not month:
        print(f"❌ 파일명에서 월을 추출할 수 없습니다: {file_path.name}")
        sys.exit(1)

    print(f"\n📅 업로드 대상: {year}년 {month}")
    print(f"📁 파일: {file_path}")

    # DB 경로
    base_dir = Path(__file__).parent.parent
    db_path = base_dir / "data" / "doubless.db"

    if not db_path.exists():
        print(f"❌ DB 파일을 찾을 수 없습니다: {db_path}")
        sys.exit(1)

    print(f"💾 DB: {db_path}")

    # 확인 메시지
    response = input(f"\n⚠️  {year}년 {month} 데이터를 DB에 저장하시겠습니까? (yes/no): ")
    if response.lower() != 'yes':
        print("\n❌ 취소되었습니다.")
        sys.exit(0)

    # 엑셀 파일 읽기
    data = read_excel_file(file_path)
    if not data:
        print("\n❌ 데이터 읽기 실패")
        sys.exit(1)

    # 매출 데이터 읽기
    sales_data = read_sales_data(file_path)

    # DB에 저장
    total_count = save_to_db(data, year, month, db_path)

    # 매출 데이터 저장
    sales_count = 0
    if sales_data:
        sales_count = save_sales_to_db(sales_data, year, month, db_path)

    print("\n" + "="*80)
    print(f"✅ 업로드 완료: 수업내역 {total_count}건, 매출 {sales_count}명")
    print("="*80)


if __name__ == "__main__":
    main()
