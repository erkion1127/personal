# 데이터 디렉토리

이 디렉토리는 Doubless 프로젝트의 모든 데이터베이스 파일을 중앙 관리합니다.

## 📂 디렉토리 구조

```
data/
├── members.db          # 회원 관리 데이터베이스
├── salary.db           # 급여 관리 데이터베이스
├── backups/            # 백업 파일 디렉토리
│   ├── members_backup_YYYYMMDD_HHMMSS.db
│   └── salary_backup_YYYYMMDD_HHMMSS.db
└── README.md           # 이 파일
```

## 🗄️ 데이터베이스 파일

### members.db
회원 정보를 관리하는 데이터베이스

**테이블:**
- `members`: 회원 기본 정보 (이름, 연락처, 상태, 이용권, 만료일 등)
- `suganggwon`: 수강권(PT) 정보 (강사, 잔여횟수, 시작/종료일 등)
- `hoewongwon`: 회원권(헬스) 정보 (상태, 판매금액, 잔여횟수 등)

**생성 프로그램:**
- `programs/html_to_db.py` - 회원 리스트 HTML 파싱
- `programs/membership_to_db.py` - 수강권/회원권 데이터 파싱

### salary.db
급여 정보를 관리하는 데이터베이스

**테이블:**
- `salary_records`: 급여 상세 레코드 (트레이너별, 회원별 세션 및 급여 정보)
- `monthly_summary`: 월별 트레이너 요약 통계

**생성 프로그램:**
- `programs/salary_to_db.py` - 급여 엑셀 파일 파싱

## 🔄 백업 정책

- 백업 파일은 `backups/` 디렉토리에 타임스탬프와 함께 저장됩니다
- 백업 파일명 형식: `{dbname}_backup_YYYYMMDD_HHMMSS.db`
- DB 재생성 시 자동으로 백업이 생성됩니다

## 📊 데이터베이스 사용법

### SQLite로 직접 조회
```bash
sqlite3 data/members.db
sqlite3 data/salary.db
```

### Python 프로그램으로 분석
```bash
# 회원 분석
python programs/member_analysis.py

# 급여 분석
python programs/analyze_salary_from_db.py
```

## ⚠️ 주의사항

- DB 파일을 직접 수정하지 마세요. 항상 제공된 프로그램을 사용하세요.
- 중요한 작업 전에는 수동 백업을 권장합니다.
- 백업 파일은 정기적으로 정리하세요 (용량 관리).

## 🔗 관련 프로그램

| 프로그램 | 설명 |
|---------|------|
| `html_to_db.py` | 회원 HTML → members.db |
| `membership_to_db.py` | 수강권/회원권 HTML → members.db |
| `salary_to_db.py` | 급여 엑셀 → salary.db |
| `analyze_salary_from_db.py` | 급여 이상건 분석 |
| `member_analysis.py` | 회원 정보 조회/분석 |
| `cross_analysis.py` | 급여-회원 교차 분석 |
