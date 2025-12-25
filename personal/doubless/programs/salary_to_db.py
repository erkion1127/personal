#!/usr/bin/env python3
"""
트레이너 급여 엑셀 파일을 SQLite DB로 변환하는 프로그램 (전체 컬럼 버전)

6~11월 트레이너 급여 엑셀 파일들을 읽어서
모든 컬럼을 포함한 통합 DB로 저장합니다.
"""

import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime
import re

def create_salary_database(db_path):
    """급여 데이터베이스 생성 - 전체 컬럼 포함"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 급여 상세 테이블 생성 (모든 컬럼 포함)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS salary_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            년도 INTEGER NOT NULL,
            월 TEXT NOT NULL,
            트레이너 TEXT NOT NULL,
            NO INTEGER,
            회원명 TEXT NOT NULL,
            성별 TEXT,
            등록세션 REAL,
            총진행세션 REAL,
            남은세션 REAL,
            결제형태 TEXT,
            등록비용 REAL,
            공급가 REAL,
            회단가 REAL,
            매출대비율 REAL,
            수업료_정산 REAL,
            당월진행세션 REAL,
            당월수업료 REAL,
            이달의매출 REAL,
            등록일시 TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(년도, 월, 트레이너, 회원명)
        )
    ''')

    # 월별 트레이너 요약 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS monthly_summary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            년도 INTEGER NOT NULL,
            월 TEXT NOT NULL,
            트레이너 TEXT NOT NULL,
            총인원 INTEGER,
            남 INTEGER,
            여 INTEGER,
            단가평균 REAL,
            총수업수 INTEGER,
            잔여세션 INTEGER,
            개인매출 REAL,
            개인매출_VAT REAL,
            UNIQUE(년도, 월, 트레이너)
        )
    ''')

    # 인덱스 생성
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_salary_trainer ON salary_records(트레이너)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_salary_member ON salary_records(회원명)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_salary_month ON salary_records(년도, 월)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_salary_trainer_month ON salary_records(트레이너, 년도, 월)')

    # 유용한 뷰 생성
    cursor.execute('''
        CREATE VIEW IF NOT EXISTS trainer_monthly_detail AS
        SELECT
            년도, 월, 트레이너,
            COUNT(*) as 회원수,
            SUM(등록세션) as 총등록세션,
            SUM(총진행세션) as 총진행세션,
            SUM(남은세션) as 총남은세션,
            SUM(당월진행세션) as 당월총진행세션,
            SUM(당월수업료) as 당월총수업료,
            AVG(회단가) as 평균단가,
            SUM(등록비용) as 총등록비용
        FROM salary_records
        GROUP BY 년도, 월, 트레이너
        ORDER BY 년도, 월, 트레이너
    ''')

    # 회원별 6개월 진행 상황 뷰
    cursor.execute('''
        CREATE VIEW IF NOT EXISTS member_6month_progress AS
        SELECT
            회원명,
            트레이너,
            COUNT(DISTINCT 월) as 활동월수,
            SUM(당월진행세션) as 총진행세션_6개월,
            SUM(당월수업료) as 총수업료_6개월,
            MAX(남은세션) as 최종남은세션,
            GROUP_CONCAT(DISTINCT 월) as 활동월
        FROM salary_records
        GROUP BY 회원명, 트레이너
        ORDER BY 총진행세션_6개월 DESC
    ''')

    conn.commit()
    return conn

def clean_numeric(value):
    """숫자 값 정리"""
    if pd.isna(value):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).replace(',', '').strip())
    except:
        return None

def clean_text(value):
    """텍스트 값 정리"""
    if pd.isna(value):
        return None
    return str(value).strip()

def extract_summary_from_excel(file_path, sheet_name):
    """엑셀 상단 요약 정보 추출"""
    df_raw = pd.read_excel(file_path, sheet_name=sheet_name, header=None, nrows=2)

    summary = {}

    # 1행에 요약 정보가 있음
    if len(df_raw) >= 2:
        row = df_raw.iloc[1]
        # 작성자(트레이너), 총인원, 남, 여, 단가평균, 총수업수, 잔여세션, 개인매출, 개인매출/VAT
        try:
            summary['총인원'] = clean_numeric(row[10])
            summary['남'] = clean_numeric(row[11])
            summary['여'] = clean_numeric(row[12])
            summary['단가평균'] = clean_numeric(row[13])
            summary['총수업수'] = clean_numeric(row[14])
            summary['잔여세션'] = clean_numeric(row[15])
            summary['개인매출'] = clean_numeric(row[16])
            summary['개인매출_VAT'] = clean_numeric(row[17])
        except:
            pass

    return summary

def parse_excel_to_db(file_path, year, month, conn):
    """엑셀 파일을 파싱하여 DB에 저장 - 전체 컬럼 포함"""
    print(f"\n📄 파일 처리 중: {file_path.name}")

    try:
        excel_file = pd.ExcelFile(file_path)
        print(f"   시트: {', '.join(excel_file.sheet_names)}")

        cursor = conn.cursor()
        total_inserted = 0

        for trainer_name in excel_file.sheet_names:
            # 요약 정보 추출
            summary = extract_summary_from_excel(file_path, trainer_name)

            # 요약 정보 저장
            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO monthly_summary (
                        년도, 월, 트레이너, 총인원, 남, 여, 단가평균,
                        총수업수, 잔여세션, 개인매출, 개인매출_VAT
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    year, month, trainer_name,
                    summary.get('총인원'), summary.get('남'), summary.get('여'),
                    summary.get('단가평균'), summary.get('총수업수'), summary.get('잔여세션'),
                    summary.get('개인매출'), summary.get('개인매출_VAT')
                ))
            except Exception as e:
                print(f"   ⚠️  요약 저장 오류 [{trainer_name}]: {e}")

            # header=2를 사용하여 3번째 행을 헤더로 인식
            df = pd.read_excel(file_path, sheet_name=trainer_name, header=2)

            # 빈 행 제거
            df = df.dropna(how='all')

            # NO. 컬럼이 숫자인 행만 필터링
            if 'NO.' in df.columns:
                df = df[pd.to_numeric(df['NO.'], errors='coerce').notna()]

            inserted = 0

            for idx, row in df.iterrows():
                # 회원명이 없으면 스킵
                if '회원명' not in df.columns or pd.isna(row['회원명']) or str(row['회원명']).strip() == '':
                    continue

                # 컬럼명 매핑 (개행 문자 포함된 컬럼명 처리)
                회원명 = clean_text(row.get('회원명'))
                성별 = clean_text(row.get('성별'))
                NO = clean_numeric(row.get('NO.'))
                등록세션 = clean_numeric(row.get('등록세션'))

                # '총 진행\n세션' 같은 개행 포함 컬럼명 찾기
                총진행세션_col = None
                남은세션_col = None
                결제형태_col = None
                당월진행세션_col = None

                for col in df.columns:
                    col_clean = str(col).replace('\n', '').replace(' ', '')
                    if '총진행세션' in col_clean or '총진행' in col_clean:
                        총진행세션_col = col
                    elif '남은세션' in col_clean or '남은' in col_clean:
                        남은세션_col = col
                    elif '결제형태' in col_clean or '결제' in col_clean:
                        결제형태_col = col
                    elif '당월진행세션' in col_clean or '당월진행' in col_clean:
                        당월진행세션_col = col

                총진행세션 = clean_numeric(row.get(총진행세션_col)) if 총진행세션_col else None
                남은세션 = clean_numeric(row.get(남은세션_col)) if 남은세션_col else None
                결제형태 = clean_text(row.get(결제형태_col)) if 결제형태_col else None
                당월진행세션 = clean_numeric(row.get(당월진행세션_col)) if 당월진행세션_col else None

                등록비용 = clean_numeric(row.get('등록비용'))
                공급가 = clean_numeric(row.get('(공급가)'))
                회단가 = clean_numeric(row.get('1회단가'))
                매출대비율 = clean_numeric(row.get('매출대비%'))
                수업료_정산 = clean_numeric(row.get('수업료'))

                # '수업료.1' 컬럼이 당월 수업료
                당월수업료 = clean_numeric(row.get('수업료.1'))
                이달의매출 = clean_numeric(row.get('이달의매출'))

                try:
                    cursor.execute('''
                        INSERT OR REPLACE INTO salary_records (
                            년도, 월, 트레이너, NO, 회원명, 성별,
                            등록세션, 총진행세션, 남은세션, 결제형태,
                            등록비용, 공급가, 회단가, 매출대비율, 수업료_정산,
                            당월진행세션, 당월수업료, 이달의매출
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        year, month, trainer_name, NO, 회원명, 성별,
                        등록세션, 총진행세션, 남은세션, 결제형태,
                        등록비용, 공급가, 회단가, 매출대비율, 수업료_정산,
                        당월진행세션, 당월수업료, 이달의매출
                    ))
                    inserted += 1
                except Exception as e:
                    print(f"   ⚠️  오류 [{trainer_name}] {회원명}: {e}")
                    continue

            print(f"   ✅ [{trainer_name}] {inserted}건 저장")
            total_inserted += inserted

        conn.commit()
        print(f"   📊 총 {total_inserted}건 저장 완료")
        return total_inserted

    except Exception as e:
        print(f"   ❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return 0

def print_statistics(conn):
    """데이터베이스 통계 출력"""
    cursor = conn.cursor()

    print("\n" + "="*100)
    print("📊 급여 데이터베이스 통계")
    print("="*100)

    # 전체 레코드 수
    total = cursor.execute("SELECT COUNT(*) FROM salary_records").fetchone()[0]
    print(f"\n총 급여 레코드 수: {total}건")

    # 월별 통계
    print("\n[월별 레코드 수]")
    monthly_stats = cursor.execute("""
        SELECT 년도, 월, COUNT(*) as cnt
        FROM salary_records
        GROUP BY 년도, 월
        ORDER BY 년도, 월
    """).fetchall()
    for year, month, count in monthly_stats:
        print(f"  {year}년 {month}: {count}건")

    # 월별 트레이너 상세 요약
    print("\n[월별 트레이너 상세 요약]")
    summary = cursor.execute("""
        SELECT * FROM trainer_monthly_detail
        ORDER BY 년도, 월, 트레이너
    """).fetchall()

    current_month = None
    for row in summary:
        년도, 월, 트레이너, 회원수, 총등록세션, 총진행세션, 총남은세션, 당월총진행세션, 당월총수업료, 평균단가, 총등록비용 = row
        month_key = f"{년도}년 {월}"

        if month_key != current_month:
            print(f"\n  [{month_key}]")
            current_month = month_key

        당월총진행세션_str = f"{당월총진행세션:.0f}회" if 당월총진행세션 else "N/A"
        당월총수업료_str = f"{당월총수업료:,.0f}원" if 당월총수업료 else "N/A"
        평균단가_str = f"{평균단가:,.0f}원" if 평균단가 else "N/A"
        총등록비용_str = f"{총등록비용:,.0f}원" if 총등록비용 else "N/A"

        print(f"    {트레이너}: 회원 {회원수}명, 당월 {당월총진행세션_str}, 당월급여 {당월총수업료_str}, 평균단가 {평균단가_str}")

    # 월별 요약 정보
    print("\n[월별 트레이너 요약 (엑셀 상단 데이터)]")
    monthly_summary = cursor.execute("""
        SELECT 년도, 월, 트레이너, 총인원, 남, 여, 단가평균, 총수업수, 잔여세션, 개인매출, 개인매출_VAT
        FROM monthly_summary
        ORDER BY 년도, 월, 트레이너
    """).fetchall()

    current_month = None
    for row in monthly_summary:
        년도, 월, 트레이너, 총인원, 남, 여, 단가평균, 총수업수, 잔여세션, 개인매출, 개인매출_VAT = row
        month_key = f"{년도}년 {월}"

        if month_key != current_month:
            print(f"\n  [{month_key}]")
            current_month = month_key

        매출_str = f"{개인매출:,.0f}원" if 개인매출 else "N/A"
        매출VAT_str = f"{개인매출_VAT:,.0f}원" if 개인매출_VAT else "N/A"

        print(f"    {트레이너}: 총{총인원}명(남{남}/여{여}), 총수업{총수업수}회, 잔여{잔여세션}회, 매출 {매출_str}")

    print("="*100)

def main():
    """메인 함수"""
    print("="*100)
    print("💰 트레이너 급여 데이터 DB 구축 프로그램 (전체 컬럼 버전)")
    print("="*100)

    # 경로 설정
    base_dir = Path(__file__).parent.parent
    pay_dir = base_dir / "pay" / "2025"
    db_file = base_dir / "data" / "salary.db"

    # 기존 DB 백업
    if db_file.exists():
        backup_dir = base_dir / "data" / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup_file = backup_dir / f"salary_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        import shutil
        shutil.copy(db_file, backup_file)
        print(f"📦 기존 DB 백업: {backup_file.name}")
        db_file.unlink()

    # 데이터베이스 생성
    print(f"\n🔧 데이터베이스 생성: {db_file}")
    conn = create_salary_database(db_file)

    # 엑셀 파일 찾기
    excel_files = sorted(pay_dir.glob("*.xlsx"))

    if not excel_files:
        print(f"❌ 엑셀 파일을 찾을 수 없습니다: {pay_dir}")
        return

    print(f"\n📁 {len(excel_files)}개 엑셀 파일 발견")

    # 각 파일 처리
    total_records = 0

    for file_path in excel_files:
        # 파일명에서 월 추출
        filename = file_path.stem
        month_match = re.search(r'(\d+)월', filename)
        if month_match:
            month = month_match.group(1) + "월"
        else:
            print(f"⚠️  월 정보를 추출할 수 없습니다: {filename}")
            continue

        year = 2025

        records = parse_excel_to_db(file_path, year, month, conn)
        total_records += records

    print(f"\n✅ 전체 {total_records}건 DB 저장 완료!")

    # 통계 출력
    print_statistics(conn)

    conn.close()

    print(f"\n✅ 데이터베이스 저장 완료: {db_file}")
    print(f"\n💡 사용 방법:")
    print(f"   sqlite3 {db_file}")
    print(f"   또는 Python으로 조회 가능")

if __name__ == "__main__":
    main()
