"""
Gmail을 사용한 이메일 발송 모듈

사용 예제:
    sender = EmailSender()
    sender.send_email(
        to_email="recipient@example.com",
        subject="제목",
        body="본문"
    )
"""

import smtplib
import json
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Union
from pathlib import Path


class EmailSender:
    """Gmail SMTP를 사용한 이메일 발송 클래스"""

    def __init__(self, config_path: str = None):
        """
        EmailSender 초기화

        Args:
            config_path: 설정 파일 경로. None이면 현재 디렉토리의 email_config.json 사용
        """
        if config_path is None:
            # 현재 스크립트 위치 기준으로 설정 파일 찾기
            current_dir = Path(__file__).parent
            config_path = current_dir / "email_config.json"

        self.config = self._load_config(config_path)
        self.sender_email = self.config['sender_email']
        self.sender_password = self.config['sender_password']
        self.smtp_server = self.config.get('smtp_server', 'smtp.gmail.com')
        self.smtp_port = self.config.get('smtp_port', 587)

    def _load_config(self, config_path: Union[str, Path]) -> dict:
        """
        설정 파일 로드

        Args:
            config_path: 설정 파일 경로

        Returns:
            설정 딕셔너리

        Raises:
            FileNotFoundError: 설정 파일이 없을 때
            ValueError: 설정 파일 형식이 잘못되었을 때
        """
        config_path = Path(config_path)

        if not config_path.exists():
            raise FileNotFoundError(
                f"설정 파일을 찾을 수 없습니다: {config_path}\n"
                f"email_config.template.json을 참고하여 email_config.json을 생성하세요."
            )

        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        # 필수 필드 검증
        required_fields = ['sender_email', 'sender_password']
        missing_fields = [field for field in required_fields if field not in config]

        if missing_fields:
            raise ValueError(
                f"설정 파일에 필수 필드가 없습니다: {', '.join(missing_fields)}"
            )

        return config

    def send_email(
        self,
        to_email: Union[str, List[str]],
        subject: str,
        body: str,
        is_html: bool = False,
        attachments: List[str] = None
    ) -> bool:
        """
        이메일 발송

        Args:
            to_email: 수신자 이메일 주소 (문자열 또는 리스트)
            subject: 이메일 제목
            body: 이메일 본문
            is_html: HTML 형식 여부 (기본값: False)
            attachments: 첨부 파일 경로 리스트 (선택 사항)

        Returns:
            성공 여부 (True/False)
        """
        try:
            # 수신자 리스트 정규화
            if isinstance(to_email, str):
                recipients = [to_email]
            else:
                recipients = to_email

            # 이메일 메시지 생성
            message = MIMEMultipart()
            message['From'] = self.sender_email
            message['To'] = ', '.join(recipients)
            message['Subject'] = subject

            # 본문 추가
            mime_type = 'html' if is_html else 'plain'
            message.attach(MIMEText(body, mime_type, 'utf-8'))

            # 첨부 파일 추가
            if attachments:
                for file_path in attachments:
                    self._attach_file(message, file_path)

            # SMTP 연결 및 발송
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()  # TLS 암호화 시작
                server.login(self.sender_email, self.sender_password)
                server.send_message(message)

            print(f"✅ 이메일 발송 성공: {', '.join(recipients)}")
            return True

        except smtplib.SMTPAuthenticationError:
            print("❌ Gmail 인증 실패: 앱 비밀번호를 확인하세요.")
            return False

        except smtplib.SMTPException as e:
            print(f"❌ SMTP 오류: {e}")
            return False

        except Exception as e:
            print(f"❌ 이메일 발송 실패: {e}")
            return False

    def _attach_file(self, message: MIMEMultipart, file_path: str):
        """
        파일 첨부

        Args:
            message: MIMEMultipart 메시지 객체
            file_path: 첨부할 파일 경로
        """
        file_path = Path(file_path)

        if not file_path.exists():
            print(f"⚠️ 첨부 파일을 찾을 수 없습니다: {file_path}")
            return

        with open(file_path, 'rb') as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())

        encoders.encode_base64(part)
        part.add_header(
            'Content-Disposition',
            f'attachment; filename={file_path.name}'
        )

        message.attach(part)
        print(f"📎 첨부 파일 추가: {file_path.name}")


def main():
    """테스트용 메인 함수"""
    sender = EmailSender()

    # 테스트 이메일 발송
    result = sender.send_email(
        to_email="k942363h@gmail.com",
        subject="테스트 이메일",
        body="이메일 발송 모듈 테스트입니다."
    )

    if result:
        print("테스트 성공!")
    else:
        print("테스트 실패!")


if __name__ == "__main__":
    main()
