# 정책 문서 가이드

이 디렉토리는 MCP 서버에서 참조할 수 있는 정책 문서를 관리합니다.

## 정책 문서 작성 가이드

### 파일명 규칙

- 소문자와 하이픈 사용: `coding-standards.md`
- 명확하고 설명적인 이름 사용
- 버전 관리가 필요한 경우: `policy-name-v1.md`

### 문서 구조

각 정책 문서는 다음 구조를 따르는 것을 권장합니다:

```markdown
# [정책 제목]

## 개요
정책의 목적과 범위

## 원칙
핵심 원칙들

## 세부 규칙
구체적인 규칙과 가이드라인

## 예시
좋은 예시와 나쁜 예시

## 예외 사항
규칙의 예외 상황

## 관련 문서
연관된 다른 정책이나 참고 자료
```

## MCP 서버 통합

MCP 서버 설정에서 이 디렉토리를 참조하도록 설정하여, AI 어시스턴트가 정책 문서를 자동으로 참고하도록 할 수 있습니다.

### 설정 예시

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/Users/ijeongseob/Documents/doc/jslee27/policies"]
    }
  }
}
```

## 정책 문서 예시

- `coding-standards.md`: 코딩 표준 및 컨벤션
- `security-guidelines.md`: 보안 관련 가이드라인
- `review-process.md`: 코드 리뷰 프로세스
- `documentation-policy.md`: 문서화 정책
