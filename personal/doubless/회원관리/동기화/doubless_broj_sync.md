# Doubless Broj CRM 동기화 관리

## 📌 개요

이 문서는 Doubless의 Broj CRM 시스템과의 데이터 동기화 작업을 관리하고 추적하기 위한 관리 문서입니다.

## 📂 디렉토리 구조

```
회원관리/
├── 동기화/
│   ├── doubless_broj_sync.md           # 이 파일 (동기화 관리 문서)
│   ├── latest/                         # 최신 동기화 데이터 (심볼릭 링크)
│   │   ├── members_sync_*.json
│   │   ├── tickets_sync_*.json
│   │   └── lesson_tickets_sync_*.json
│   ├── 20251226_010439/                # 동기화 회차별 폴더
│   │   ├── sync_info.json              # 동기화 메타정보
│   │   ├── members_sync_20251226_010439.json
│   │   ├── tickets_sync_20251226_010441.json
│   │   └── lesson_tickets_sync_20251226_010442.json
│   ├── 20251225_230000/
│   │   └── ...
│   └── sync_history.json               # 동기화 이력 로그
└── 회원데이터/                          # (기존) 원본 다운로드 위치
```

## 🎯 동기화 정책

### 1. 폴더 단위 관리
- 각 동기화 실행 시 `YYYYMMDD_HHMMSS` 형식의 폴더 생성
- 한 번의 동기화로 생성된 3개 파일을 하나의 폴더에 저장
- 동기화 ID는 최초 동기화 시작 시간 기준

### 2. Latest 링크 관리
- `latest/` 폴더는 가장 최근 동기화 데이터를 가리킴
- 심볼릭 링크 또는 복사본으로 관리
- 다른 프로그램은 `latest/` 폴더를 참조하면 항상 최신 데이터 사용

### 3. 동기화 이력 추적
- `sync_history.json`에 모든 동기화 이력 기록
- 성공/실패 여부, 레코드 수, 소요 시간 등 기록

## 📊 데이터 종류

### 1. 회원 정보 (members)
- **파일명**: `members_sync_YYYYMMDD_HHMMSS.json`
- **API**: `/api/jcustomer/jgroup/{jgroup_key}`
- **주요 필드**: customer_key, name, phone, email, classification
- **평균 레코드 수**: ~1,000명

### 2. 회원권 정보 (tickets)
- **파일명**: `tickets_sync_YYYYMMDD_HHMMSS.json`
- **API**: `/jgroup/ticketdetails/{jgroup_key}`
- **주요 필드**: jtd_key, jtd_name, jtd_started_dttm, jtd_closed_dttm
- **평균 레코드 수**: ~1,300건

### 3. 수강권 정보 (lesson_tickets)
- **파일명**: `lesson_tickets_sync_YYYYMMDD_HHMMSS.json`
- **API**: `/api/jgroup/lessonticket/{jgroup_key}`
- **주요 필드**: jglesson_ticket_key, jglesson_ticket_type, jglesson_ticket_count
- **평균 레코드 수**: ~300건

## 🚀 동기화 실행 방법

### 기본 실행
```bash
cd /Users/ijeongseob/IdeaProjects/jslee27/personal/doubless/programs
./venv/bin/python3 download_members.py
```

### 전체 경로 실행
```bash
/Users/ijeongseob/IdeaProjects/jslee27/personal/doubless/programs/venv/bin/python3 \
/Users/ijeongseob/IdeaProjects/jslee27/personal/doubless/programs/download_members.py
```

## 📋 동기화 체크리스트

### 실행 전
- [ ] 네트워크 연결 확인
- [ ] config.md 설정 확인 (ID, PWD, jgroup_key)
- [ ] Python 가상환경 활성화 확인
- [ ] requests 라이브러리 설치 확인

### 실행 중
- [ ] 로그인 성공 확인
- [ ] Access Token 획득 확인
- [ ] 회원 정보 다운로드 완료 (페이지 수 확인)
- [ ] 회원권 정보 다운로드 완료 (페이지 수 확인)
- [ ] 수강권 정보 다운로드 완료 (페이지 수 확인)

### 실행 후
- [ ] 3개 파일 모두 생성 확인
- [ ] sync_info 메타데이터 확인
- [ ] 레코드 수 정상 범위 확인
- [ ] latest 링크 업데이트 확인
- [ ] sync_history.json 업데이트 확인

## 📈 동기화 이력

| 동기화 ID | 실행 시간 | 회원 수 | 회원권 수 | 수강권 수 | 상태 | 비고 |
|-----------|-----------|---------|-----------|-----------|------|------|
| 20251226_011032 | 2025-12-26 01:10:32 | 1,042명 | 1,305건 | 305건 | ✅ 성공 | 폴더 구조 개선 (v2.0) |
| 20251226_010439 | 2025-12-26 01:04:39 | 1,042명 | 1,305건 | 305건 | ✅ 성공 | 초기 전체 동기화 (v1.0) |

> **참고**: sync_history.json 파일에서 전체 이력을 확인할 수 있습니다.

## 🔄 동기화 주기 권장사항

### 실시간 동기화가 필요한 경우
- 매일 1회: 오전 9시 (영업 시작 전)
- 매일 1회: 오후 11시 (영업 종료 후)

### 주간 동기화
- 주 1회: 월요일 오전 9시

### 월간 동기화
- 월 1회: 매월 1일 오전 9시

## 🛠️ 동기화 데이터 활용

### 1. 급여 분석
- `salary_analysis.py`에서 수강권 데이터 참조
- 트레이너별 진행 세션 수 계산
- 이상 케이스 탐지

### 2. 회원 관리
- 회원 상태 변화 추적
- 신규 회원 vs 재등록 회원 분석
- 회원권 만료 예정자 알림

### 3. 수강권 관리
- 수강권 잔여 세션 추적
- 트레이너별 담당 회원 관리
- 수강권 만료 예정 알림

## ⚠️ 주의사항

### 데이터 무결성
- 동기화 중 중단되지 않도록 주의
- 3개 파일이 모두 생성되어야 완료
- sync_id가 동일한 파일들만 함께 사용

### 보안
- 다운로드된 JSON 파일은 개인정보 포함
- Git 커밋 시 제외 (.gitignore에 추가)
- 파일 권한 관리 주의

### 스토리지
- 월 30회 동기화 시 약 300MB 예상
- 6개월 이상 경과 데이터는 아카이브 고려
- latest 폴더는 용량에 포함되지 않음

## 🔧 문제 해결

### 1. 동기화 실패
- 로그 파일 확인
- 네트워크 상태 확인
- Token 만료 여부 확인
- 재실행 후에도 실패 시 수동 확인

### 2. 레코드 수 급감
- 회원 수가 전날 대비 50% 이상 감소 시 확인 필요
- API 변경 가능성 확인
- 페이징 로직 확인

### 3. Latest 링크 오류
- 심볼릭 링크 재생성
- 복사본 방식으로 변경 고려

## 📞 담당자

- **시스템 관리**: 이정섭
- **데이터 활용**: Doubless 트레이너 팀
- **문의**: 시스템 이슈 발생 시 이정섭에게 연락

## 📚 관련 문서

- `회원정보다운로드_사용법.md`: 다운로드 프로그램 상세 사용법
- `회원정보다운로드_절차.md`: API 호출 절차 및 기술 문서
- `급여내역테이블설명.md`: 급여 분석 정책
- `config.md`: CRM 로그인 설정

## 🔄 버전 이력

- **v2.0** (2025-12-26 01:10): 폴더 구조 개선 완료
  - ✅ 동기화 ID별 폴더 자동 생성 (`YYYYMMDD_HHMMSS/`)
  - ✅ Latest 폴더 자동 업데이트 (최신 데이터 복사)
  - ✅ sync_info.json 자동 생성 (폴더별 메타정보)
  - ✅ sync_history.json 자동 업데이트 (전체 이력 추적)
  - ✅ 레코드 수 자동 집계 및 기록

- **v1.0** (2025-12-26 01:04): 초기 동기화 관리 체계 구축
  - 폴더 단위 관리 개념 설계
  - Latest 링크 개념 도입
  - 동기화 이력 추적 계획

## 💡 사용 팁

### Latest 폴더 활용
다른 프로그램에서 항상 최신 데이터를 참조하려면:
```python
# Python 예시
from pathlib import Path
import json

latest_dir = Path("/Users/ijeongseob/IdeaProjects/jslee27/personal/doubless/회원관리/동기화/latest")

# 최신 회원 정보 읽기
with open(latest_dir / "members_sync_*.json") as f:  # 실제로는 glob 사용
    members = json.load(f)

# 또는 sync_info로 파일명 확인
with open(latest_dir / "sync_info.json") as f:
    info = json.load(f)
    member_file = latest_dir / info['files']['members']
```

### 동기화 이력 조회
```bash
# 전체 이력 보기
cat /Users/ijeongseob/IdeaProjects/jslee27/personal/doubless/회원관리/동기화/sync_history.json | python3 -m json.tool

# 최근 5회 동기화 이력
cat sync_history.json | python3 -m json.tool | tail -50
```

### 이전 동기화 데이터 복원
```bash
# 특정 시점 데이터를 latest로 복원
cd /Users/ijeongseob/IdeaProjects/jslee27/personal/doubless/회원관리/동기화
rm -rf latest
cp -r 20251226_010439 latest
```
