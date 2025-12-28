# 빠른 참조 가이드

Claude와 함께 문서를 관리할 때 자주 사용하는 명령어와 규칙 모음입니다.

## 자주 사용하는 명령어

### 문서 찾기
```
"[카테고리] 관련 문서 찾아줘"
"2024년 [주제] 문서 검색해줘"
"[날짜] 이후 추가된 문서 보여줘"
```

### 문서 요약
```
"[폴더명] 폴더 내용 요약해줘"
"[파일명] 요약해줘 (개인정보 제외)"
"최근 회의록 요약해줘"
```

### 문서 작성
```
"회의록 작성해줘"
"의사결정 기록 만들어줘"
"[주제] 보고서 템플릿 만들어줘"
```

### 문서 정리
```
"중복 파일 찾아줘"
"파일명 규칙에 맞지 않는 파일 찾아줘"
"archive로 이동할 문서 추천해줘"
```

## 폴더 구조 치트시트

```
personal/
├── family/         # 가족 문서
├── certificates/   # 증명서
├── financial/      # 금융 (세금, 주식, 은행)
│   ├── stock-tax/
│   ├── stock/
│   ├── stock-documents/
│   └── bank-interest/
├── real-estate/    # 부동산
│   ├── mokpo/
│   └── gwanggyo/
├── health/         # 건강/의료
├── vehicle/        # 차량
└── career/         # 경력

work/
├── notes/          # 메모
├── meetings/       # 회의록
├── reports/        # 보고서
├── archive/        # 아카이브
└── settings/       # 설정

policies/           # AI 참조 정책
templates/          # 템플릿
references/         # 참고자료
```

## 파일명 규칙

### 템플릿
```
YYYY-MM-DD_카테고리_설명.확장자
```

### 예시
```
✅ 2024-12-24_회의록_프로젝트킥오프.md
✅ 2024-12-24_건강검진.pdf
✅ stock-tax-2024.xlsx
❌ 회의록 (12-24).md          # 공백, 특수문자
❌ report.md                  # 설명 부족
❌ 2024/12/24_meeting.md      # 날짜 형식 오류
```

## 보안 체크리스트

### 커밋 전 확인
- [ ] 개인정보 (주민등록번호, 계좌번호 등) 제거
- [ ] 비밀번호, API 키 제거
- [ ] 파일명에 민감정보 없음
- [ ] .gitignore 규칙 확인

### 민감도 레벨
| 레벨 | 포함 내용 | 예시 폴더 |
|------|-----------|-----------|
| Level 1 | 주민번호, 계좌번호, 비밀번호 | financial/stock-tax |
| Level 2 | 급여, 세금신고, 의료기록 | real-estate/mokpo/급여 |
| Level 3 | 계약서, 자격증, 건강검진 | certificates/, health/ |
| Level 4 | 일반 업무 문서 | work/meetings |

## Git 커밋 메시지

### 형식
```
[카테고리] 간단한 설명

- 상세 내용
```

### 카테고리 목록
- `[personal]` - 개인 문서
- `[work]` - 업무 문서
- `[policy]` - 정책 문서
- `[template]` - 템플릿
- `[structure]` - 구조 변경
- `[docs]` - 문서 업데이트

### 예시
```
[personal] 2024년 건강검진 결과 추가

- personal/health/건강검진/20241224_건강검진.pdf 추가
- 연간 정기 건강검진 결과
```

## 템플릿 사용법

### 회의록
```bash
cp templates/meeting-notes.md work/meetings/2024-12-24-프로젝트회의.md
```

### 의사결정 기록
```bash
cp templates/decision-record.md work/notes/2024-12-24-기술스택선정.md
```

## AI 작업 예시

### 문서 검색
```
사용자: "목포 영업신고 관련 문서 찾아줘"
AI: personal/real-estate/mokpo/영업신고/ 폴더 검색
    → 관련 파일 리스트 제공
```

### 문서 분류
```
사용자: "이 PDF를 적절한 폴더에 저장해줘"
AI: 파일 내용 분석
    → 카테고리 제안
    → 파일명 규칙에 맞게 제안
```

### 중복 파일 찾기
```
사용자: "중복 파일 찾아줘"
AI: 파일명, 크기, 내용 비교
    → 중복 가능성 있는 파일 리스트
    → 정리 방안 제안
```

### 월간 정리
```
사용자: "이번 달 문서 정리 도와줘"
AI: 체크리스트 확인
    - 파일명 규칙 준수 여부
    - 잘못 분류된 문서
    - archive 이동 대상
    - 중복 파일
```

## 정기 관리 작업

### 매주
- [ ] 새 문서 올바른 폴더에 분류
- [ ] 파일명 규칙 확인
- [ ] work/meetings 회의록 작성 완료

### 매월
- [ ] 완료된 프로젝트를 archive/로 이동
- [ ] 중복 파일 검사
- [ ] 백업 상태 확인

### 분기별
- [ ] 문서 분류 체계 검토
- [ ] 정책 문서 업데이트
- [ ] 불필요한 파일 정리

## 문제 해결

### Q: 문서를 어느 폴더에 넣어야 할지 모르겠어요
A: Claude에게 물어보세요
```
"이 문서를 어디에 저장하면 좋을까요?"
```

### Q: 파일명을 어떻게 지어야 하나요?
A: 규칙을 따르거나 Claude에게 제안 요청
```
"이 파일에 적절한 파일명 제안해줘"
```

### Q: 중요한 문서를 실수로 삭제했어요
A: Git 히스토리에서 복구
```bash
git log -- 파일경로
git checkout 커밋해시 -- 파일경로
```

### Q: 민감한 정보를 커밋했어요
A: 즉시 커밋 되돌리기
```bash
git reset --soft HEAD~1  # 커밋 취소 (변경사항 유지)
# 또는
git revert HEAD          # 되돌림 커밋 생성
```

## 유용한 Git 명령어

### 최근 변경 내역 확인
```bash
git log --oneline -10
```

### 특정 폴더 변경사항 보기
```bash
git log -- personal/financial/
```

### 파일 변경 이력
```bash
git log -p 파일경로
```

### 특정 날짜 이후 변경사항
```bash
git log --since="2024-12-01"
```

## 참고 문서

- [README.md](README.md) - 프로젝트 개요
- [CLAUDE_RULES.md](CLAUDE_RULES.md) - Claude 사용 규칙
- [policies/document-management.md](policies/document-management.md) - 상세 정책
- [policies/README.md](policies/README.md) - 정책 가이드

## 도움말

더 자세한 내용은:
1. 각 문서의 상단 참조
2. Claude에게 질문
3. 정책 문서 검토

예시:
```
"CLAUDE_RULES.md 요약해줘"
"문서 관리 정책 중 보안 관련 부분만 보여줘"
```
