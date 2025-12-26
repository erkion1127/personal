# Email 발송 모듈

Gmail을 사용한 이메일 발송 모듈입니다.

## 설정 방법

### 1. Gmail 앱 비밀번호 생성

Gmail에서 2단계 인증을 활성화하고 앱 비밀번호를 생성해야 합니다.

1. Google 계정 설정 페이지 접속: https://myaccount.google.com/
2. 보안 → 2단계 인증 활성화
3. 보안 → 앱 비밀번호 생성
   - 앱 선택: 메일
   - 기기 선택: 기타 (사용자 지정 이름 입력 가능)
4. 생성된 16자리 비밀번호 복사

### 2. 설정 파일 생성

`email_config.json` 파일을 생성하고 아래 내용을 입력하세요:

```json
{
  "sender_email": "k942363h@gmail.com",
  "sender_password": "tvsh yhnj rjpn isqs",
  "smtp_server": "smtp.gmail.com",
  "smtp_port": 587
}
```

**⚠️ 보안 주의사항**:
- `email_config.json` 파일은 절대 Git에 커밋하지 마세요
- 이 파일은 `.gitignore`에 추가되어야 합니다
- 앱 비밀번호는 안전하게 관리하세요

### 3. 필요한 패키지 설치

이메일 발송에는 Python 표준 라이브러리만 사용하므로 추가 패키지 설치가 필요 없습니다.

## 사용 방법

### 기본 사용 예제

```python
from email_sender import EmailSender

# 이메일 발송 객체 생성
sender = EmailSender()

# 텍스트 이메일 발송
sender.send_email(
    to_email="recipient@example.com",
    subject="제목",
    body="이메일 본문 내용"
)
```

### HTML 이메일 발송

```python
html_content = """
<html>
  <body>
    <h1>안녕하세요</h1>
    <p>이것은 <b>HTML</b> 이메일입니다.</p>
  </body>
</html>
"""

sender.send_email(
    to_email="recipient@example.com",
    subject="HTML 이메일",
    body=html_content,
    is_html=True
)
```

### 파일 첨부

```python
sender.send_email(
    to_email="recipient@example.com",
    subject="첨부파일 포함",
    body="파일을 첨부합니다.",
    attachments=[
        "/path/to/file1.pdf",
        "/path/to/file2.xlsx"
    ]
)
```

### 여러 수신자에게 발송

```python
recipients = [
    "user1@example.com",
    "user2@example.com",
    "user3@example.com"
]

sender.send_email(
    to_email=recipients,
    subject="공지사항",
    body="여러분께 공지드립니다."
)
```

## 파일 구조

```
email/
├── README.md                 # 이 파일
├── email_sender.py          # 이메일 발송 모듈
├── email_config.json        # 설정 파일 (gitignore)
├── email_config.template.json  # 설정 템플릿
└── example_usage.py         # 사용 예제
```

## 주요 기능

- ✉️ 텍스트/HTML 이메일 발송
- 📎 파일 첨부 지원
- 👥 다중 수신자 지원
- 🔒 Gmail 앱 비밀번호 사용 (안전)
- 📝 상세한 오류 메시지

## 문제 해결

### "Authentication failed" 오류

- Gmail 2단계 인증이 활성화되어 있는지 확인
- 앱 비밀번호를 정확히 입력했는지 확인
- 일반 비밀번호가 아닌 앱 비밀번호를 사용해야 함

### "SMTP connection failed" 오류

- 인터넷 연결 확인
- 방화벽에서 587 포트가 차단되어 있지 않은지 확인

### 파일 첨부 실패

- 첨부할 파일 경로가 올바른지 확인
- 파일이 존재하는지 확인
- 파일 크기가 Gmail 제한(25MB)을 초과하지 않는지 확인
