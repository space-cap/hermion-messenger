import asyncio
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import httpx
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

class DARTCollector:
    """DART Open API를 통해 기업 공시 정보를 수집하는 비동기 수집기"""
    
    BASE_URL = "https://opendart.fss.or.kr/api/list.json"
    
    def __init__(self, api_key: Optional[str] = None):
        # 환경변수에서 DART_API_KEY 로드
        self.api_key = api_key or os.getenv("DART_API_KEY")
        
    async def fetch_disclosures(
        self, 
        start_date: str, 
        end_date: str, 
        page_no: int = 1, 
        page_count: int = 100
    ) -> List[Dict[str, Any]]:
        """
        지정된 기간 동안의 DART 공시 목록을 조회합니다.
        
        :param start_date: 시작일자 (YYYYMMDD)
        :param end_date: 종료일자 (YYYYMMDD)
        :param page_no: 페이지 번호
        :param page_count: 페이지당 데이터 수 (최대 100)
        :return: 공시 정보 딕셔너리 리스트
        """
        if not self.api_key or "your_" in self.api_key:
            raise ValueError("DART_API_KEY가 설정되지 않았거나 올바르지 않습니다.")
            
        params = {
            "crtfc_key": self.api_key,
            "bgn_de": start_date,
            "end_de": end_date,
            "page_no": page_no,
            "page_count": page_count
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(self.BASE_URL, params=params)
            
            if response.status_code != 200:
                raise httpx.HTTPStatusError(
                    f"DART API 호출 실패 (HTTP {response.status_code})",
                    request=response.request,
                    response=response
                )
                
            data = response.json()
            status = data.get("status")
            message = data.get("message", "메시지 없음")
            
            # DART API 상태 코드 검증: "000"은 정상
            if status == "000":
                return data.get("list", [])
            elif status == "013":
                # 013: 조회결과가 없음
                return []
            else:
                raise ValueError(f"DART API 오류: {status} ({message})")

    async def get_recent_disclosures(self, days: int = 2) -> List[Dict[str, Any]]:
        """
        최근 N일간의 공시 데이터를 조회합니다.
        
        :param days: 조회할 이전 일수 (전일 18시 이후 포함을 위해 기본 2일)
        :return: 전체 공시 목록
        """
        today = datetime.now()
        start_date_dt = today - timedelta(days=days)
        
        start_date = start_date_dt.strftime("%Y%m%d")
        end_date = today.strftime("%Y%m%d")
        
        print(f"[정보] DART 공시 조회 기간: {start_date} ~ {end_date}")
        
        # 첫 페이지 조회
        disclosures = await self.fetch_disclosures(start_date, end_date, page_no=1)
        
        # 건수가 많을 경우 페이징 처리도 처리 가능하지만, 모닝브리핑 범위에서는 100건으로 충분할 수 있음
        return disclosures

    async def filter_by_watchlist(
        self, 
        disclosures: List[Dict[str, Any]], 
        watchlist: List[str]
    ) -> List[Dict[str, Any]]:
        """
        수집된 공시 목록에서 관심 종목(stk_cd 리스트)에 해당하는 공시만 필터링합니다.
        
        :param disclosures: 전체 공시 리스트
        :param watchlist: 6자리 종목코드 리스트 (예: ['005930', '000660'])
        :return: 필터링된 공시 리스트
        """
        filtered = []
        for disc in disclosures:
            stock_code = disc.get("stock_code")
            # DART의 stock_code는 6자리 형태로 반환됨
            if stock_code and stock_code in watchlist:
                filtered.append(disc)
        return filtered


# 로컬 연동 테스트용 진입점
async def test_dart_connection():
    print("=== DART Open API 연동 테스트 시작 ===")
    
    api_key = os.getenv("DART_API_KEY")
    if not api_key or "your_" in api_key:
        print("[경고] .env 파일에 올바른 DART_API_KEY를 입력해 주세요.")
        print("=========================================")
        return

    collector = DARTCollector(api_key=api_key)
    
    try:
        # 최근 2일간의 전체 공시 정보 획득
        disclosures = await collector.get_recent_disclosures(days=1)
        print(f"[성공] 전체 수집된 공시 수: {len(disclosures)}건")
        
        # 관심 종목 리스트 예시: 삼성전자(005930), SK하이닉스(000660), 현대차(005380), 셀트리온(068270)
        watchlist = ["005930", "000660", "005380", "068270"]
        
        # 필터링
        filtered_disclosures = await collector.filter_by_watchlist(disclosures, watchlist)
        print(f"[성공] 관심 종목 필터링 결과: {len(filtered_disclosures)}건")
        
        # 필터링 결과 출력
        for i, disc in enumerate(filtered_disclosures[:10], start=1):
            print(f"   {i}. [{disc.get('corp_name')}] {disc.get('report_nm')} "
                  f"(접수일자: {disc.get('rcept_dt')}, 링크: https://dart.fss.or.kr/dsaf001/main.do?rcpNo={disc.get('rcept_no')})")
            
    except Exception as e:
        print(f"[오류] DART 수집 테스트 중 오류 발생: {e}")
    finally:
        print("=== 테스트 완료 ===")

if __name__ == "__main__":
    asyncio.run(test_dart_connection())
