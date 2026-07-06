import asyncio
import os
import json
from typing import Dict, Any, List, Optional
import anthropic
from dotenv import load_dotenv

from ..validator.double_check_validator import DoubleCheckValidator

load_dotenv()

class BriefingGenerator:
    """Claude 공식 SDK를 비동기 호출하여 모닝/마감 브리핑 본문을 생성하고 수치 검증을 수행하는 생성기"""
    
    CLAUDE_MODEL = "claude-sonnet-5"
    
    # LLM이 숫자를 창작하거나 반올림/왜곡하는 것을 강력 제어하는 아침 브리핑 시스템 프롬프트
    SYSTEM_PROMPT = (
        "너는 신뢰성 100%의 금융 모닝브리핑을 작성하는 전문 에디터이다.\n\n"
        "### 핵심 가이드라인 (반드시 준수할 것):\n"
        "1. 제공된 JSON 데이터에 존재하지 않는 임의의 숫자(지수, 가격, 등락률, 날짜 등)를 절대로 창작하거나 추정하여 쓰지 말라.\n"
        "2. 소수점이나 수치는 반올림하지 말고 원본 JSON에 있는 숫자 그대로 표기하라 (예: -8051.33은 -8051.33 그대로 기입, -8051로 축소 금지).\n"
        "3. 제공된 데이터가 없는 종목이나 지수에 대해서는 절대 추정해서 코멘트하지 말고 반드시 기재를 생략하거나 '데이터 없음'으로 처리하라.\n"
        "4. 브리핑 문구에 '매수하세요', '지금이 기회', '상승할 것입니다' 등 투자 권유나 특정 종목 매매를 추천하는 표현은 법적으로 엄격히 금지된다. 철저히 사실에 기반한 시황 정보 및 요약 정보만 건조하고 전문적인 어조로 서술하라.\n\n"
        "### 브리핑 템플릿 구조:\n"
        "## [오늘의 시장 요약]\n"
        "- 국내 시장(코스피/코스닥 지수 및 등락률) 요약\n"
        "- 해외 시장(다우, S&P 500, 나스닥, 필라델피아 반도체 지수 및 등락률) 요약\n\n"
        "## [수급 동향]\n"
        "- 코스피 당일 주요 주체별(외국인, 기관, 개인) 순매수 특징 요약\n\n"
        "## [관심 종목 및 공시 알림]\n"
        "- 관심 종목(사용자가 지정한 종목)들의 시세 상태와 관련 주요 공시 내역 요약\n"
        "- 공시가 있을 경우 해당 공시 제목과 함께 제공된 URL 링크(DART 링크)를 마크다운 링크 형식으로 반드시 포함할 것"
    )

    # 마감시황 전용 시스템 프롬프트 (정보가 더욱 풍부하고 네이버 증권 마감 시황 뉴스 스타일 분석 포함)
    SYSTEM_PROMPT_CLOSING = (
        "너는 신뢰성 100%의 풍부하고 깊이 있는 금융 마감시황을 작성하는 전문 경제 에디터이다.\n\n"
        "### 핵심 가이드라인 (반드시 준수할 것):\n"
        "1. 제공된 JSON 데이터에 존재하지 않는 임의의 숫자(지수, 가격, 등락률, 날짜 등)를 절대로 창작하거나 추정하여 쓰지 말라.\n"
        "2. 소수점이나 수치는 반올림하지 말고 원본 JSON에 있는 숫자 그대로 표기하라 (예: -8051.33은 -8051.33 그대로 기입, -8051로 축소 금지).\n"
        "3. 제공된 데이터가 없는 종목이나 지수에 대해서는 절대 추정해서 코멘트하지 말고 반드시 기재를 생략하거나 '데이터 없음'으로 처리하라.\n"
        "4. 브리핑 문구에 '매수하세요', '지금이 기회', '상승할 것입니다' 등 투자 권유나 특정 종목 매매를 추천하는 표현은 법적으로 엄격히 금지된다. 철저히 사실에 기반한 시황 정보 및 요약 정보만 건조하고 전문적인 어조로 서술하라.\n\n"
        "### 브리핑 템플릿 구조:\n"
        "# 📈 오늘의 증시 마감 요약\n"
        "- 국내 시장(코스피/코스닥 지수 및 등락률) 마감 현황 요약\n"
        "- 해외 시장(다우, S&P 500, 나스닥, 필라델피아 반도체 지수 및 등락률) 요약\n\n"
        "# 🏛️ 시장 특징 및 수급 동향\n"
        "- 제공된 코스피 수급 정보(외국인, 기관, 개인 순매수 금액)를 바탕으로 오늘 시장의 수급 주체별 매매 동향 상세 설명\n"
        "- 오늘 하루 동안의 전반적인 시장 특징 분석 (지수 등락 흐름에 대한 설명)\n\n"
        "# 📰 주요 헤드라인 뉴스\n"
        "- 제공된 'news' 데이터를 바탕으로 주요 뉴스 5건을 소개할 것\n"
        "- 각 뉴스 제목을 마크다운 링크 형식(제공된 URL 사용)으로 기재하고, 해당 뉴스가 오늘 주식 시장 또는 향후 증시에 미칠 영향을 금융 에디터의 시각에서 전문적이고 풍부하게 해설할 것\n\n"
        "# 🔔 관심 종목 및 공시 알림\n"
        "- 관심 종목들의 마감 시세 상태와 관련 주요 공시 내역 요약\n"
        "- 공시가 있을 경우 해당 공시 제목과 함께 제공된 URL 링크(DART 링크)를 마크다운 링크 형식으로 반드시 포함할 것"
    )


    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.validator = DoubleCheckValidator()
        
    async def call_claude_api(self, prompt: str, system_instruction: str) -> str:
        """Claude API를 비동기 호출하여 텍스트를 반환합니다."""
        if not self.api_key or "your_" in self.api_key:
            raise ValueError("ANTHROPIC_API_KEY가 설정되지 않았거나 올바르지 않습니다.")
            
        # AsyncAnthropic 클라이언트 초기화 (가이드라인 준수)
        client = anthropic.AsyncAnthropic(api_key=self.api_key)
        
        # 공식 SDK 메시지 생성 호출
        message = await client.messages.create(
            model=self.CLAUDE_MODEL,
            max_tokens=3000,
            system=system_instruction,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        # 생각 블록(thinking) 등 다중 블록 포맷 호환 추출
        text_blocks = [block.text for block in message.content if block.type == "text"]
        if text_blocks:
            return "\n".join(text_blocks)
            
        raise ValueError("Claude API 응답에 텍스트 본문이 존재하지 않습니다.")

    async def generate_and_validate_briefing(self, raw_data: Dict[str, Any], briefing_type: str = "morning") -> Dict[str, Any]:
        """
        수집된 원본 데이터를 기반으로 브리핑 본문을 생성하고, 2단계 수치 불일치 검증을 수행합니다.
        검증 실패 시 피드백 프롬프트를 포함하여 최대 1회 재생성을 시도합니다.
        
        :param raw_data: 키움, DART, Yahoo, 뉴스 등에서 모은 통합 딕셔너리
        :param briefing_type: 'morning' (아침 모닝브리핑) 또는 'closing' (장 마감시황)
        :return: {'briefing', 'is_valid', 'mismatched_numbers', 'attempts'}
        """
        system_instruction = self.SYSTEM_PROMPT_CLOSING if briefing_type == "closing" else self.SYSTEM_PROMPT
        
        # User 프롬프트 생성 (JSON 데이터를 텍스트로 전달)
        user_prompt = (
            f"아래의 통합 시장 데이터를 기반으로 {'하루를 마감하는 마감시황 브리핑' if briefing_type == 'closing' else '아침 모닝브리핑'}을 작성해줘.\n\n"
            f"=== 수집된 시장 데이터 (JSON) ===\n"
            f"{json.dumps(raw_data, ensure_ascii=False, indent=2)}"
        )
        
        print(f"[정보] Claude API 브리핑 생성 요청 중 (1차 시도, 타입={briefing_type})...")
        briefing = await self.call_claude_api(user_prompt, system_instruction)
        
        # 1차 검증 실행
        validation_result = self.validator.validate_briefing(briefing, raw_data)
        print(f"[정보] 1차 검증 완료: 일치율={validation_result['valid_percentage']}% | 패스 여부={validation_result['is_valid']}")
        
        attempts = 1
        
        # 수치 불일치가 발생할 경우 피드백 재생성 시도
        if not validation_result["is_valid"]:
            attempts += 1
            print(f"[경고] 1차 생성 브리핑에 불일치 숫자 발견: {validation_result['mismatched_numbers']}")
            print("[정보] 피드백 루프 작동: Claude API 재생성 요청 중 (2차 시도)...")
            
            # 피드백 프롬프트 구성
            feedback_prompt = (
                f"{user_prompt}\n\n"
                f"### [⚠️ 재생성 요청 피드백]\n"
                f"이전 생성본에서 아래의 숫자들이 원본 데이터와 일치하지 않거나 왜곡(반올림 등)되었습니다:\n"
                f"{validation_result['mismatched_numbers']}\n\n"
                f"이번에는 원본 데이터셋을 정확하게 다시 대조하여, 불일치한 수치를 반드시 올바르게 교정하고 "
                f"데이터에 없는 숫자는 절대 추가하지 않고 엄격하게 새로 작성해줘."
            )
            
            # 2차 재생성 호출
            briefing = await self.call_claude_api(feedback_prompt, system_instruction)
            
            # 2차 검증 실행
            validation_result = self.validator.validate_briefing(briefing, raw_data)
            print(f"[정보] 2차 검증 완료: 일치율={validation_result['valid_percentage']}% | 패스 여부={validation_result['is_valid']}")
            
        return {
            "briefing": briefing,
            "is_valid": validation_result["is_valid"],
            "mismatched_numbers": validation_result["mismatched_numbers"],
            "attempts": attempts,
            "checked_count": validation_result["checked_count"],
            "valid_percentage": validation_result["valid_percentage"]
        }

