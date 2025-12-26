"""
이메일 발송 모듈 사용 예제
"""

from email_sender import EmailSender


def example_basic():
    """기본 텍스트 이메일 발송 예제"""
    print("=== 기본 텍스트 이메일 발송 ===")

    sender = EmailSender()
    sender.send_email(
        to_email="recipient@example.com",
        subject="안녕하세요",
        body="이것은 테스트 이메일입니다."
    )


def example_html():
    """HTML 이메일 발송 예제"""
    print("\n=== HTML 이메일 발송 ===")

    html_content = """
    <html>
      <body>
        <h1 style="color: #2e6c80;">급여 분석 보고서</h1>
        <p>안녕하세요,</p>
        <p>이번 달 급여 분석 결과를 알려드립니다.</p>
        <ul>
          <li>총 세션 수: 398회</li>
          <li>총 급여: 6,517,200원</li>
          <li>이상 케이스: 0건</li>
        </ul>
        <p>자세한 내용은 첨부 파일을 참고해주세요.</p>
        <hr>
        <p style="color: #888; font-size: 12px;">
          이 메일은 자동으로 발송되었습니다.
        </p>
      </body>
    </html>
    """

    sender = EmailSender()
    sender.send_email(
        to_email="recipient@example.com",
        subject="[Doubless] 월간 급여 분석 보고서",
        body=html_content,
        is_html=True
    )


def example_with_attachments():
    """파일 첨부 예제"""
    print("\n=== 파일 첨부 이메일 발송 ===")

    sender = EmailSender()
    sender.send_email(
        to_email="recipient@example.com",
        subject="급여 분석 보고서 (첨부파일 포함)",
        body="첨부 파일을 확인해주세요.",
        attachments=[
            "/Users/ijeongseob/IdeaProjects/jslee27/personal/doubless/pay/report/latest/종합분석_20251226_014231.txt",
            "/Users/ijeongseob/IdeaProjects/jslee27/personal/doubless/pay/report/latest/2025년_11월_급여분석.txt"
        ]
    )


def example_multiple_recipients():
    """여러 수신자에게 발송 예제"""
    print("\n=== 여러 수신자 이메일 발송 ===")

    recipients = [
        "manager@example.com",
        "trainer1@example.com",
        "trainer2@example.com"
    ]

    sender = EmailSender()
    sender.send_email(
        to_email=recipients,
        subject="[공지] 급여 지급 일정 안내",
        body="이번 달 급여는 25일에 지급될 예정입니다."
    )


def example_salary_report():
    """급여 분석 보고서 발송 예제 (실전 활용)"""
    print("\n=== 급여 분석 보고서 자동 발송 ===")

    # 분석 정보 읽기 (실제로는 JSON 파일에서 읽어옴)
    analysis_date = "2025년 12월 26일"
    total_sessions = 2358.0
    total_salary = "44,653,619원"
    total_anomalies = 114

    # HTML 보고서 생성
    html_report = f"""
    <html>
      <head>
        <style>
          body {{ font-family: 'Malgun Gothic', sans-serif; }}
          .header {{ background-color: #2e6c80; color: white; padding: 20px; }}
          .content {{ padding: 20px; }}
          .summary {{ background-color: #f0f0f0; padding: 15px; margin: 10px 0; }}
          .warning {{ color: #d9534f; font-weight: bold; }}
          table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
          th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
          th {{ background-color: #2e6c80; color: white; }}
        </style>
      </head>
      <body>
        <div class="header">
          <h1>Doubless 급여 분석 보고서</h1>
          <p>분석 일시: {analysis_date}</p>
        </div>
        <div class="content">
          <div class="summary">
            <h2>📊 종합 요약</h2>
            <table>
              <tr><th>항목</th><th>내용</th></tr>
              <tr><td>총 세션 수</td><td>{total_sessions}회</td></tr>
              <tr><td>총 급여</td><td>{total_salary}</td></tr>
              <tr><td>이상 케이스</td><td class="warning">{total_anomalies}건</td></tr>
            </table>
          </div>

          <h2>⚠️ 조치 필요 사항</h2>
          <p>이상 케이스가 발견되었습니다. 자세한 내용은 첨부 파일을 확인해주세요.</p>

          <hr>
          <p style="color: #888; font-size: 12px;">
            이 메일은 자동으로 발송되었습니다.<br>
            문의사항: k942363h@gmail.com
          </p>
        </div>
      </body>
    </html>
    """

    sender = EmailSender()
    sender.send_email(
        to_email="k942363h@gmail.com",
        subject=f"[Doubless] 급여 분석 보고서 - {analysis_date}",
        body=html_report,
        is_html=True,
        attachments=[
            "/Users/ijeongseob/IdeaProjects/jslee27/personal/doubless/pay/report/latest/종합분석_20251226_014231.txt"
        ]
    )


if __name__ == "__main__":
    print("이메일 발송 모듈 사용 예제\n")
    print("주의: 실제 이메일을 발송하려면 email_config.json 파일에 앱 비밀번호를 설정해야 합니다.")
    print("\n사용 가능한 예제:")
    print("1. example_basic() - 기본 텍스트 이메일")
    print("2. example_html() - HTML 이메일")
    print("3. example_with_attachments() - 파일 첨부")
    print("4. example_multiple_recipients() - 여러 수신자")
    print("5. example_salary_report() - 급여 보고서 발송 (실전)")
    print("\n원하는 예제 함수를 직접 호출하세요.")

    # 테스트를 원하면 아래 주석을 해제하세요
    # example_basic()
    # example_html()
    # example_with_attachments()
    # example_multiple_recipients()
    # example_salary_report()
