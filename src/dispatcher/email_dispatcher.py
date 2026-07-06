import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any
import markdown
from dotenv import load_dotenv

load_dotenv()

class EmailDispatcher:
    """Daum SMTP 등 SSL 이메일 발송 기능을 담당하는 비동기/동기 발송기"""
    
    def __init__(self):
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.daum.net")
        self.smtp_port = int(os.getenv("SMTP_PORT", "465"))
        self.smtp_username = os.getenv("SMTP_USERNAME")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.from_email = os.getenv("SMTP_FROM_EMAIL")
        
        # 윈도우 린터 경고 방지를 위한 임포트 가이드 적용 (상대 경로 없음)

    def _render_html_template(self, title: str, markdown_content: str, is_closing: bool = False) -> str:
        """마크다운 브리핑 텍스트를 수려한 모던 디자인의 HTML 템플릿으로 변환합니다."""
        # 마크다운을 HTML로 파싱 (테이블 등 확장 모듈 활성화)
        html_body = markdown.markdown(markdown_content, extensions=['tables', 'nl2br'])
        
        subtitle = "Hermion Messenger Closing Briefing Service" if is_closing else "Hermion Messenger Daily Briefing Service"
        
        # 프리미엄 다크 네이비 & 포인트 블루 디자인 템플릿 적용 (Aesthetics)
        premium_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>{title}</title>
            <style>
                body {{
                    font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                    background-color: #f1f5f9;
                    margin: 0;
                    padding: 30px 20px;
                    color: #0f172a;
                }}
                .container {{
                    max-width: 680px;
                    margin: 0 auto;
                    background-color: #ffffff;
                    border-radius: 20px;
                    box-shadow: 0 10px 30px rgba(15, 23, 42, 0.08);
                    overflow: hidden;
                    border: 1px solid #e2e8f0;
                }}
                .header {{
                    background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%);
                    color: #ffffff;
                    padding: 40px 30px;
                    text-align: center;
                    border-bottom: 4px solid #2563eb;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 26px;
                    font-weight: 800;
                    letter-spacing: -0.75px;
                    line-height: 1.3;
                }}
                .header p {{
                    margin: 10px 0 0 0;
                    font-size: 13px;
                    color: #94a3b8;
                    font-weight: 500;
                    text-transform: uppercase;
                    letter-spacing: 1.5px;
                }}
                .content {{
                    padding: 40px 35px;
                    line-height: 1.8;
                    font-size: 15px;
                    color: #334155;
                }}
                /* 본문 헤더 H1 매거진 바 포인트 스타일 */
                .content h1 {{
                    color: #0f172a;
                    font-size: 20px;
                    font-weight: 700;
                    border-left: 5px solid #2563eb;
                    padding-left: 14px;
                    margin-top: 35px;
                    margin-bottom: 20px;
                }}
                .content h2 {{
                    color: #0f172a;
                    font-size: 17px;
                    font-weight: 700;
                    margin-top: 25px;
                    margin-bottom: 15px;
                    border-bottom: 1px solid #e2e8f0;
                    padding-bottom: 6px;
                }}
                .content ul {{
                    padding-left: 20px;
                    margin-bottom: 25px;
                }}
                .content li {{
                    margin-bottom: 10px;
                }}
                .content p {{
                    margin-bottom: 20px;
                }}
                .content a {{
                    color: #2563eb;
                    text-decoration: none;
                    font-weight: 600;
                    border-bottom: 1px dashed #2563eb;
                }}
                .content a:hover {{
                    color: #1d4ed8;
                    border-bottom: 1px solid #1d4ed8;
                }}
                /* 인용구 blockquote 스타일링 (뉴스 해설 및 주요 공시 포인트) */
                blockquote {{
                    margin: 20px 0;
                    padding: 15px 20px;
                    background-color: #f8fafc;
                    border-left: 4px solid #94a3b8;
                    border-radius: 0 8px 8px 0;
                    color: #475569;
                    font-style: italic;
                    font-size: 14.5px;
                }}
                /* DART 공시 / 시황 테이블 스타일링 */
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 25px 0;
                    font-size: 14px;
                    border-radius: 8px;
                    overflow: hidden;
                    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.02);
                }}
                th, td {{
                    padding: 12px 15px;
                    text-align: left;
                    border-bottom: 1px solid #f1f5f9;
                }}
                th {{
                    background-color: #0f172a;
                    color: #ffffff;
                    font-weight: 600;
                }}
                tr:nth-child(even) {{
                    background-color: #f8fafc;
                }}
                .footer {{
                    background-color: #f8fafc;
                    padding: 25px 20px;
                    text-align: center;
                    font-size: 12px;
                    color: #64748b;
                    border-top: 1px solid #e2e8f0;
                    line-height: 1.6;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{title}</h1>
                    <p>{subtitle}</p>
                </div>
                <div class="content">
                    {html_body}
                </div>
                <div class="footer">
                    본 메일은 구독자님께 실시간 금융 데이터 기반으로 발송되는 증시 시황 및 기업 정보 서비스입니다.<br>
                    © 2026 Hermion Messenger. All rights reserved.
                </div>
            </div>
        </body>
        </html>
        """
        return premium_template

    def send_briefing(self, to_email: str, date_str: str, briefing_markdown: str, is_closing: bool = False) -> bool:
        """
        Daum SMTP 보안 SSL 방식으로 메일 발송을 수행합니다.
        
        :param to_email: 수신할 구독자 이메일 주소
        :param date_str: 기준 일자 YYYY-MM-DD
        :param briefing_markdown: 마크다운 형태의 브리핑 본문
        :param is_closing: True 이면 장마감시황 제목, False 이면 모닝브리핑 제목 적용
        :return: 발송 성공 여부
        """
        if not self.smtp_username or "your_" in self.smtp_username:
            print("[경고] SMTP 설정이 누락되어 메일 발송이 스킵되었습니다.")
            return False
            
        if is_closing:
            title = f"[장마감시황] {date_str} 국내외 증시 요약 및 주요 경제 뉴스"
        else:
            title = f"[모닝브리핑] {date_str} 국내외 시장 시황 및 공시 요약"
            
        html_content = self._render_html_template(title, briefing_markdown, is_closing)
        
        # 메일 메시지 작성
        msg = MIMEMultipart("alternative")
        msg["Subject"] = title
        msg["From"] = self.from_email
        msg["To"] = to_email
        
        # 텍스트와 HTML 본문 첨부
        part1 = MIMEText(briefing_markdown, "plain", "utf-8")
        part2 = MIMEText(html_content, "html", "utf-8")
        msg.attach(part1)
        msg.attach(part2)
        
        try:
            print(f"[정보] Daum SMTP({self.smtp_host}:{self.smtp_port})에 SSL 보안 연결 시도 중...")
            
            # SMTP_SSL 보안 접속
            with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, timeout=10.0) as server:
                server.login(self.smtp_username, self.smtp_password)
                server.sendmail(self.from_email, to_email, msg.as_string())
                
            print(f"[성공] 이메일 발송 완료! (수신자: {to_email})")
            return True
        except Exception as e:
            print(f"[오류] SMTP 메일 발송 중 실패 발생: {e}")
            raise e
