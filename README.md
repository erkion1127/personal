# jslee27

개인 업무 문서 및 정책 관리 저장소

## 목적

- 개인 문서(경력, 금융, 부동산, 건강 등) 체계적 관리
- 업무 문서(회의록, 노트 등) 정리
- MCP 서버에서 참조할 정책 문서 관리
- IDE 설정 및 개발 환경 백업

## 폴더 구조

```
jslee27/
├── personal/                    # 개인 관련 문서
│   ├── career/                  # 경력 관련 (rocketon, musinsa)
│   ├── certificates/            # 자격증
│   ├── doubless/                # 다블레스 관련 (급여, 규정)
│   ├── family/                  # 가족 관련
│   ├── financial/               # 금융 (은행이자, 주식, 세금)
│   ├── health/                  # 건강 (건강검진, 의료비)
│   ├── real-estate/             # 부동산 (목포, 광교)
│   └── vehicle/                 # 차량 관련
├── work/                        # 업무 관련 문서
│   ├── notes/                   # 일반 노트
│   └── settings/                # 설정 파일 (코드스타일, 키맵)
├── policies/                    # MCP 서버용 정책 문서
└── templates/                   # 문서 템플릿
```

## 사용 방법

### 업무 노트 작성

```bash
cp templates/meeting-notes.md work/notes/YYYY-MM-DD-meeting-title.md
```

### 의사결정 기록

```bash
cp templates/decision-record.md work/notes/YYYY-MM-DD-decision-title.md
```

### 개인 문서 관리

- `personal/career/`: 경력 관련 문서 (이력서, 평가 등)
- `personal/financial/`: 금융 관련 문서 (주식, 세금, 은행)
- `personal/real-estate/`: 부동산 관련 문서 (목포, 광교)
- `personal/health/`: 건강검진 및 의료비 관련 문서
- `personal/vehicle/`: 차량 관련 문서

### Doubless 피트니스 관리 시스템

`personal/doubless/` 디렉토리에는 다블레스 피트니스 센터의 회원 및 급여 관리 시스템이 포함되어 있습니다.

자세한 시스템 구조, 사용 방법, 데이터베이스 스키마, 급여 분석 규칙 등은 [personal/doubless/프로젝트구조.md](personal/doubless/프로젝트구조.md)를 참조하세요.

주요 기능:
- Broj CRM 데이터 자동 다운로드 및 동기화
- SQLite 기반 회원/회원권/수강권 통합 관리
- 트레이너 급여 분석 및 이상 케이스 탐지
- 월별 실적 리포트 자동 생성

## 정책 문서

MCP 서버에서 참조할 수 있는 정책 문서는 `policies/` 디렉토리에 저장합니다.
자세한 내용은 [policies/README.md](policies/README.md)를 참조하세요.
