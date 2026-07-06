import os
from typing import Dict, Any, Optional
import httpx
from dotenv import load_dotenv

load_dotenv()

class KakaoDispatcher:
    """비즈엠(BIZM) API 기반으로 카카오 알림톡을 전송하는 발송기"""
    
    # 비즈엠 알림톡 전송 Endpoint 예시
    BIZM_URL = "https://api.bizmsg.co.kr/v2/sender/send"
    
    def __init__(self):
        self.api_key = os.getenv("BIZM_API_KEY")
        self.sender_profile_key = os.getenv("BIZM_SENDER_PROFILE_KEY")
        
        # 키가 설정되지 않았거나 예시 키인 경우 Mock 모드로 전환
        self.is_mock = (
            not self.api_key 
            or "your_" in self.api_key 
            or not self.sender_profile_key 
            or "your_" in self.sender_profile_key
        )
        
        if self.is_mock:
            print("[정보] 카카오 알림톡 발송기: API Key 미인증 상태이므로 [Mock 발송 모드]로 작동합니다.")

    async def send_talk(
        self, 
        to_phone: str, 
        message_text: str, 
        template_code: Optional[str] = None
    ) -> bool:
        """
        카카오 알림톡을 구독자 휴대폰으로 발송합니다.
        API Key가 없는 경우 가상으로 성공 처리 및 콘솔에 내용을 출력합니다.
        
        :param to_phone: 구독자 전화번호
        :param message_text: 발송할 알림톡 메시지 본문
        :param template_code: 등록된 알림톡 템플릿 코드
        :return: 발송 성공 여부
        """
        if self.is_mock:
            print(f"\n[Mock 알림톡 발송 완료] 수신번호: {to_phone}")
            print(f"--- 발송된 메시지 본문 ---\n{message_text}")
            print("---------------------------------\n")
            return True
            
        headers = {
            "userid": "hermion_msg",
            "ApiKey": self.api_key,
            "content-type": "application/json"
        }
        
        payload = {
            "senderKey": self.sender_profile_key,
            "templateCode": template_code or "morning_briefing_01",
            "recipientNum": to_phone.replace("-", ""),
            "message": message_text
        }
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(self.BIZM_URL, headers=headers, json=payload)
                
                if response.status_code != 200:
                    print(f"[오류] 비즈엠 API 서버 오류 (HTTP {response.status_code}): {response.text}")
                    return False
                    
                res_data = response.json()
                # 성공 응답 사양에 따른 판정 (예: resultCode == "success" 등)
                if res_data.get("code") == "200" or res_data.get("result") == "success":
                    print(f"[성공] 카카오 알림톡 실제 발송 완료! (수신번호: {to_phone})")
                    return True
                else:
                    print(f"[오류] 알림톡 전송 실패 응답: {res_data}")
                    return False
                    
        except Exception as e:
            print(f"[오류] 알림톡 발송 중 네트워크/서버 에러 발생: {e}")
            return False
