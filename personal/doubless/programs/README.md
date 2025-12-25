# Doubless 분석 프로그램

Doubless 관련 데이터를 분석하는 프로그램 모음

## 프로그램 목록

### 1. analyze_salary.py
6~11월 트레이너 급여 엑셀 파일을 분석하여 이상 징후를 탐지하는 프로그램

**기능:**
- 6개월간 급여 데이터 자동 분석
- 전월 대비 이상 징후 탐지
  - 세션 종료 후 진행
  - 전월 잔여보다 많은 진행
  - 비정상적 세션 증가
- 자동 보고서 생성 (TXT)

### 2. html_to_db.py
HTML 회원 리스트를 SQLite DB로 변환하는 프로그램

**기능:**
- HTML 테이블 파싱
- SQLite DB 자동 생성
- 1000명 회원 데이터 저장
- 검색 인덱스 자동 생성
- 통계 자동 출력

### 3. member_analysis.py
회원 데이터 분석 및 조회 프로그램

**기능:**
- 이름/연락처로 회원 검색
- 만료 임박 회원 조회 (D-7, D-30)
- 장기 미출석 회원 조회 (이탈 위험군)
- 락커 사용 현황
- 트레이너별 통계
- 상품(이용권) 통계
- 나이대별 분포
- 월별 신규 가입 추이

### 4. cross_analysis.py
급여 이상건과 회원 DB를 교차 분석하는 프로그램

**기능:**
- 급여 분석 보고서의 272건 이상건 전체 검토
- 회원 DB에서 해당 회원 상세 정보 조회
- 이상건별 회원 상태, 연락처, 이용권, 만료일 등 정보 통합
- DB 없는 회원 탐지 (이름 오타, 탈퇴 회원 등)
- 주요 발견사항 요약
  - 만료된 회원 중 세션 진행
  - 담당자 불일치
  - 장기 미출석 중 세션 진행
- 교차 분석 보고서 자동 생성

### 5. salary_to_db.py
트레이너 급여 엑셀 파일을 SQLite DB로 변환하는 프로그램

**기능:**
- 6~11월 급여 엑셀 파일 자동 파싱 (6개 파일)
- SQLite DB 자동 생성 (salary.db)
- 516건 급여 레코드 저장
- 월별/트레이너별 통계 자동 생성
- 월별 트레이너 급여 요약 뷰 제공
- 검색 인덱스 자동 생성

## 사용 방법

### 환경 설정

```bash
# programs 디렉토리로 이동
cd /Users/ijeongseob/IdeaProjects/jslee27/personal/doubless/programs

# 가상환경 활성화
source venv/bin/activate

# 필요한 라이브러리 (이미 설치되어 있음)
# pip install openpyxl pandas beautifulsoup4
```

### 1. 급여 분석 프로그램

```bash
# 가상환경 활성화
source venv/bin/activate

# 프로그램 실행
python analyze_salary.py

# 결과: ../pay/급여이상건_분석보고서.txt 생성
```

### 2. 회원 DB 구축

```bash
# 가상환경 활성화
source venv/bin/activate

# HTML → DB 변환
python html_to_db.py

# 결과: ../회원관리/members.db 생성
```

**처음 실행 시:**
- 1000명 회원 데이터 파싱
- SQLite DB 자동 생성
- 통계 자동 출력

**재실행 시:**
- 기존 DB 자동 백업 (members_backup_YYYYMMDD_HHMMSS.db)
- 새로운 DB 재생성

### 3. 회원 분석

```bash
# 가상환경 활성화
source venv/bin/activate

# 분석 프로그램 실행 (대화형)
python member_analysis.py
```

**메뉴:**
```
1. 이름으로 회원 검색
2. 연락처로 회원 검색
3. 만료 임박 회원 (D-7)
4. 만료 임박 회원 (D-30)
5. 장기 미출석 회원 (2주)
6. 락커 사용 현황
7. 트레이너별 통계
8. 상품(이용권) 통계
9. 나이대별 분포
10. 월별 신규 가입 추이
0. 종료
```

### 4. 급여-회원 교차 분석

```bash
# 가상환경 활성화
source venv/bin/activate

# 교차 분석 프로그램 실행
python cross_analysis.py

# 결과: ../pay/급여이상건_교차분석보고서.txt 생성
```

**분석 내용:**
- 급여 이상건 272건 전체에 대해 회원 DB 정보 조회
- 회원 DB 존재 여부 확인 (247건 존재, 25건 없음)
- 각 이상건별 회원 상세 정보 (상태, 연락처, 이용권, 만료일 등)
- 만료된 회원 중 세션 진행 (103건)
- 담당자 불일치 (12건)
- 장기 미출석 중 세션 진행

### 5. 급여 DB 구축

```bash
# 가상환경 활성화
source venv/bin/activate

# 엑셀 → DB 변환
python salary_to_db.py

# 결과: ../pay/salary.db 생성
```

**처음 실행 시:**
- 6~11월 급여 엑셀 파일 자동 파싱
- SQLite DB 자동 생성
- 516건 급여 레코드 저장
- 통계 자동 출력

**재실행 시:**
- 기존 DB 자동 백업 (salary_backup_YYYYMMDD_HHMMSS.db)
- 새로운 DB 재생성

**DB 조회 예시:**
```bash
# SQLite CLI로 조회
sqlite3 ../pay/salary.db

# 트레이너별 월별 급여 조회
SELECT * FROM monthly_trainer_summary;

# 특정 회원 급여 이력 조회
SELECT * FROM salary_records WHERE 회원명 = '김희성';

# 특정 월 트레이너별 총액
SELECT 트레이너, SUM(총급여_지급액) as 총액
FROM salary_records
WHERE 년도 = 2025 AND 월 = '11월'
GROUP BY 트레이너;
```

### 6. DB 기반 급여 분석 (최신) ⭐

```bash
# 가상환경 활성화
source venv/bin/activate

# DB 기반 분석 실행
python analyze_salary_from_db.py

# 결과: ../pay/reports/YYYYMMDD_HHMMSS/ 폴더에 보고서 생성
```

**생성되는 파일:**
1. **급여이상건_상세.txt** - 상세 텍스트 보고서
2. **이상건_목록.csv** - 엑셀에서 열어볼 수 있는 이상건 목록
3. **분석_메타데이터.json** - 분석 통계 및 메타데이터
4. **종합분석보고서.md** - 종합 분석 보고서 (복사본)

**특징:**
- ✅ 버저닝: 실행할 때마다 타임스탬프 기반 폴더 생성
- ✅ 세션 진행 월 기준 만료 판단 (정확도 향상)
- ✅ 회원 DB 1042명 완전 통합
- ✅ **이름 자동 정규화**: E 접미사 제거, 알려진 오타 자동 수정
- ✅ CSV 파일로 이상건 엑셀 분석 가능
- ✅ latest 심볼릭 링크로 최신 보고서 바로 접근

**이름 매핑 규칙:**
- 규칙 파일: `name_mapping_rules.json`
- E 접미사 자동 제거 (예: 김주홍E → 김주홍)
- 알려진 오타 자동 수정 (예: 유혜나 → 오혜나)
- 새로운 매핑 추가 시 JSON 파일 수정

**보고서 위치:**
```bash
# 최신 보고서
cd ../pay/reports/latest/

# 특정 시점 보고서
cd ../pay/reports/20251225_174059/
```

**이름 매핑 규칙 수정:**
```bash
# 규칙 파일 편집
nano name_mapping_rules.json

# 새로운 매핑 추가 예시:
{
  "known_mappings": {
    "mappings": {
      "유혜나": "오혜나",
      "박찬묵": "박강묵",
      "손헤림": "손혜림",
      "유현은": "유현우",
      "새로운오타": "정확한이름"  # 여기에 추가
    }
  }
}
```

## Python 스크립트로 활용

```python
# 회원 분석 클래스 사용 예시
from member_analysis import MemberAnalyzer

# DB 연결
analyzer = MemberAnalyzer('../회원관리/members.db')

# 만료 임박 회원 조회
expiring = analyzer.get_expiring_members(7)
print(expiring)

# 트레이너별 통계
trainer_stats = analyzer.get_trainer_stats()
print(trainer_stats)

# 특정 회원 정보
member_info = analyzer.get_member_info('김희성')
print(member_info)
```

## 급여 분석 + 회원 DB 연동

```python
import pandas as pd
import sqlite3

# 급여 엑셀 읽기
salary_df = pd.read_excel('../pay/2025/11월 트레이너 급여 목포.xlsx',
                          sheet_name='이준수')

# 회원 DB 연결
conn = sqlite3.connect('../회원관리/members.db')
members_df = pd.read_sql('SELECT * FROM members', conn)

# 교차 분석: 급여에는 있는데 회원DB에 없는 경우
for member in salary_df['회원명']:
    if member not in members_df['이름'].values:
        print(f"⚠️ {member}: 급여에는 있지만 회원DB에 없음")
```

## 디렉토리 구조

```
doubless/
├── programs/                          # 분석 프로그램 모음
│   ├── venv/                          # Python 가상환경
│   ├── analyze_salary.py              # 급여 분석 프로그램
│   ├── html_to_db.py                  # HTML → DB 변환
│   ├── member_analysis.py             # 회원 분석 프로그램
│   ├── cross_analysis.py              # 급여-회원 교차 분석 프로그램
│   ├── salary_to_db.py                # 급여 엑셀 → DB 변환
│   ├── analyze_salary_from_db.py      # DB 기반 급여 분석 (최신)
│   └── README.md                      # 이 파일
├── pay/                               # 급여 관련 데이터
│   ├── 2025/                          # 2025년 급여 엑셀 파일들
│   ├── salary.db                      # 급여 SQLite DB (자동 생성)
│   ├── reports/                       # 분석 보고서 폴더 (버저닝)
│   │   ├── 20251225_174059/          # 타임스탬프별 보고서
│   │   │   ├── 급여이상건_상세.txt
│   │   │   ├── 이상건_목록.csv       # 엑셀에서 열기
│   │   │   ├── 분석_메타데이터.json
│   │   │   └── 종합분석보고서.md
│   │   └── latest -> 20251225_174059/ # 최신 보고서 링크
│   ├── 급여이상건_분석보고서.txt        # 급여 이상건 보고서 (구버전)
│   ├── 급여이상건_교차분석보고서.txt    # 급여+회원 교차 분석 보고서 (구버전)
│   └── Doubless_종합분석보고서.md      # 종합 분석 보고서
├── 회원관리/                           # 회원 관련 데이터
│   ├── 회원리스트.html                 # 원본 HTML (1000명)
│   ├── 회원리스트_2.html               # 원본 HTML (42명)
│   └── members.db                     # 회원 SQLite DB (1042명, 자동 생성)
└── rule/                              # 규정 관련 문서
```

## 데이터베이스 스키마

### 회원 DB (members.db)
```sql
CREATE TABLE members (
    id INTEGER PRIMARY KEY,
    상태 TEXT,                  -- 활성/만료/예정 등
    이름 TEXT NOT NULL,
    성별 TEXT,
    생년월일 TEXT,
    나이 INTEGER,
    연락처 TEXT,
    보유이용권 TEXT,            -- 헬스 3개월 등
    보유대여권 TEXT,            -- 락커 대여권 등
    구독플랜 TEXT,
    락커룸 TEXT,
    락커번호 TEXT,
    구분 TEXT,                  -- 신규/재등록
    최초등록일 TEXT,
    최종만료일 TEXT,
    남은일수 INTEGER,
    최근구매일 TEXT,
    최근출석일 TEXT,
    상담담당자 TEXT,
    주소 TEXT,
    -- ... 기타 필드
);

-- 검색 성능을 위한 인덱스
CREATE INDEX idx_name ON members(이름);
CREATE INDEX idx_status ON members(상태);
CREATE INDEX idx_phone ON members(연락처);
CREATE INDEX idx_expire ON members(최종만료일);
CREATE INDEX idx_counselor ON members(상담담당자);
```

### 급여 DB (salary.db)
```sql
CREATE TABLE salary_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    년도 INTEGER NOT NULL,
    월 TEXT NOT NULL,
    트레이너 TEXT NOT NULL,
    회원명 TEXT NOT NULL,
    성별 TEXT,
    당월진행세션 REAL,
    남은세션 REAL,
    수업료_단가 REAL,
    총급여_지급액 REAL,
    비고 TEXT,
    등록일시 TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(년도, 월, 트레이너, 회원명)
);

-- 검색 성능을 위한 인덱스
CREATE INDEX idx_salary_trainer ON salary_records(트레이너);
CREATE INDEX idx_salary_member ON salary_records(회원명);
CREATE INDEX idx_salary_month ON salary_records(년도, 월);

-- 월별 트레이너 요약 뷰
CREATE VIEW monthly_trainer_summary AS
SELECT
    년도, 월, 트레이너,
    COUNT(*) as 회원수,
    SUM(당월진행세션) as 총진행세션,
    SUM(총급여_지급액) as 월급여총액,
    AVG(수업료_단가) as 평균단가
FROM salary_records
GROUP BY 년도, 월, 트레이너;
```

## 분석 예시

### 1. 급여 이상건 분석 결과
- **총 272건** 이상 징후 발견
- 월별: 6월(47건), 7월(58건), 8월(56건), 9월(43건), 10월(15건), 11월(53건)

### 2. 회원 DB 통계
- **총 1000명** 회원
- 활성: 456명, 만료: 458명, 임박: 69명
- 남성: 654명, 여성: 346명
- 20대: 462명 (최다)
- 락커 사용: 139명

### 3. 교차 분석 주요 발견사항
- **총 272건** 이상건 중:
  - 회원 DB 존재: 247건 (90.8%)
  - 회원 DB 없음: 25건 (9.2%) - 이름 오타 또는 탈퇴 회원
- **만료된 회원 중 세션 진행**: 103건
  - 만료 상태임에도 PT 세션이 계속 진행되는 케이스
- **담당자 불일치**: 12건
  - 급여 시트의 트레이너 ≠ 회원 DB의 상담담당자
- **장기 미출석 중 세션 진행**
  - 최근 출석 30일 이상 없는데 세션 진행 기록

### 4. 급여 DB 통계
- **총 516건** 급여 레코드 (6개월)
- **트레이너별 담당 회원**:
  - 이준수: 189건 (고유 회원 56명)
  - 한길수: 179건 (고유 회원 47명)
  - 전민진: 56건 (고유 회원 26명)
  - 신지훈: 47건 (고유 회원 17명)
  - 이현수: 29건 (고유 회원 18명)
  - 김동하: 16건 (고유 회원 8명)
- **월별 레코드**: 6월(93건), 7월(85건), 8월(90건), 9월(76건), 10월(83건), 11월(89건)

## 요구사항

- Python 3.x
- openpyxl
- pandas
- beautifulsoup4
- SQLite (Python 내장)