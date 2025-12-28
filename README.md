# jslee27

개인 업무 문서 및 정책 관리 저장소

## 목적

- 개인 업무 문서(회의록, 보고서 등) 체계적 관리
- MCP 서버에서 참조할 정책 문서 관리

## 폴더 구조

```
jslee27/
├── personal/          # 개인 문서
│   ├── family/        # 가족 관련
│   ├── certificates/  # 증명서/자격증
│   ├── financial/     # 세금/주식/은행
│   ├── real-estate/   # 부동산 (목포, 광교 등)
│   ├── health/        # 건강검진/의료
│   ├── vehicle/       # 차량
│   └── career/        # 이력서/면접
├── work/              # 업무 관련 문서
│   ├── notes/         # 일반 노트
│   ├── meetings/      # 회의록
│   ├── reports/       # 보고서
│   ├── archive/       # 아카이브된 문서
│   └── settings/      # 개발 환경 설정
├── policies/          # MCP 서버용 정책 문서
├── references/        # 참고 자료
└── templates/         # 문서 템플릿
```

## 사용 방법

### 회의록 작성

```bash
cp templates/meeting-notes.md work/meetings/YYYY-MM-DD-meeting-title.md
```

### 의사결정 기록

```bash
cp templates/decision-record.md work/notes/YYYY-MM-DD-decision-title.md
```

## 정책 문서

MCP 서버에서 참조할 수 있는 정책 문서는 `policies/` 디렉토리에 저장합니다.
자세한 내용은 [policies/README.md](policies/README.md)를 참조하세요.
