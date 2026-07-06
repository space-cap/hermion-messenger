import asyncio
from typing import Dict, Any, Optional
import httpx

class YahooFinanceCollector:
    """Yahoo Finance 공개 HTTP API를 사용하여 해외 지수 시세를 수집하는 비동기 수집기"""
    
    BASE_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
    
    # 주요 미국 지수 티커 맵
    INDEX_TICKERS = {
        "DOW": "^DJI",          # 다우존스 산업평균지수
        "SP500": "^GSPC",       # S&P 500 지수
        "NASDAQ": "^IXIC",      # 나스닥 종합지수
        "SOX": "^SOX"           # 필라델피아 반도체지수
    }
    
    def __init__(self):
        # 야후 파이낸스는 User-Agent가 없으면 401/403 에러를 낼 수 있으므로 표준 브라우저 헤더를 정의합니다.
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }

    async def fetch_index_data(self, index_name: str) -> Dict[str, Any]:
        """
        특정 해외 지수 데이터를 조회하여 전일 종가 및 등락률을 계산해 반환합니다.
        
        :param index_name: INDEX_TICKERS에 정의된 지수명 (예: 'DOW', 'SP500')
        :return: {'name', 'price', 'prev_close', 'change_val', 'change_pct'}
        """
        ticker = self.INDEX_TICKERS.get(index_name.upper())
        if not ticker:
            raise ValueError(f"지원되지 않는 지수 이름입니다: {index_name}")
            
        url = self.BASE_URL.format(ticker=ticker)
        # 최근 1일 범위, 1일 간격의 시세 요청
        params = {
            "interval": "1d",
            "range": "1d"
        }
        
        async with httpx.AsyncClient(timeout=10.0, headers=self.headers) as client:
            response = await client.get(url, params=params)
            
            if response.status_code != 200:
                raise httpx.HTTPStatusError(
                    f"Yahoo API 호출 실패 (HTTP {response.status_code})",
                    request=response.request,
                    response=response
                )
                
            data = response.json()
            
            # JSON 트리 구조 진입
            chart_res = data.get("chart", {}).get("result", [])
            if not chart_res:
                raise ValueError(f"시세 데이터가 비어 있습니다: {ticker}")
                
            meta = chart_res[0].get("meta", {})
            
            # 현재가(혹은 마지막 종가) 및 전일 종가 추출
            price = meta.get("regularMarketPrice")
            prev_close = meta.get("previousClose")
            
            if price is None or prev_close is None:
                # meta 데이터에 없을 시 indicators.quote 에서 추정 시도
                indicators = chart_res[0].get("indicators", {}).get("quote", [{}])[0]
                close_list = [c for c in indicators.get("close", []) if c is not None]
                open_list = [o for o in indicators.get("open", []) if o is not None]
                
                if close_list and open_list:
                    price = close_list[-1]
                    prev_close = open_list[0]
                else:
                    raise ValueError(f"시세 데이터를 파싱할 수 없습니다: {ticker}")
            
            # 수치 정보 계산
            change_val = price - prev_close
            change_pct = (change_val / prev_close) * 100
            
            return {
                "name": index_name.upper(),
                "ticker": ticker,
                "price": round(price, 2),
                "prev_close": round(prev_close, 2),
                "change_val": round(change_val, 2),
                "change_pct": round(change_pct, 2)
            }

    async def collect_all_indices(self) -> Dict[str, Dict[str, Any]]:
        """
        정의된 모든 해외 지수 데이터를 비동기 병렬로 수집하여 결과를 반환합니다.
        
        :return: 지수별 결과 맵
        """
        print("[정보] 해외 지수 수집 시작...")
        tasks = {name: self.fetch_index_data(name) for name in self.INDEX_TICKERS.keys()}
        
        # 병렬 비동기 처리
        results = await asyncio.gather(*tasks.values(), return_exceptions=True)
        
        output = {}
        for (name, task), result in zip(tasks.items(), results):
            if isinstance(result, Exception):
                print(f"[오류] {name} 지수 수집 실패: {result}")
                output[name] = {"name": name, "error": str(result)}
            else:
                output[name] = result
                
        return output


# 로컬 연동 테스트용 진입점
async def test_yahoo_connection():
    print("=== Yahoo Finance API 연동 테스트 시작 ===")
    
    collector = YahooFinanceCollector()
    
    try:
        results = await collector.collect_all_indices()
        print(f"[성공] 해외 지수 수집 완료 (총 {len(results)}개 지수)")
        
        for name, data in results.items():
            if "error" in data:
                print(f"   - [{name}] 오류 발생: {data.get('error')}")
            else:
                sign = "+" if data['change_val'] >= 0 else ""
                print(f"   - [{name} ({data['ticker']})] 종가: {data['price']} | "
                      f"대비: {sign}{data['change_val']} | 등락률: {sign}{data['change_pct']}%")
                
    except Exception as e:
        print(f"[오류] 야후 파이낸스 테스트 중 오류 발생: {e}")
    finally:
        print("=== 테스트 완료 ===")

if __name__ == "__main__":
    asyncio.run(test_yahoo_connection())
