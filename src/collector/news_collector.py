import httpx
import xml.etree.ElementTree as ET
from typing import List, Dict, Any

class NewsCollector:
    """네이버 경제 뉴스 RSS 피드를 조회하여 주요 헤드라인 뉴스를 수집하는 비동기 수집기"""
    
    # 구글 뉴스 주식 시황 검색 RSS 피드 URL (한국어)
    RSS_URL = "https://news.google.com/rss/search?q=%EC%A3%BC%EC%8B%9D+%EC%8B%9C%ED%99%A9+when:1d&hl=ko&gl=KR&ceid=KR:ko"
    
    def __init__(self):
        # 봇 탐지 회피를 위해 심플한 헤더 제공
        self.headers = {
            "Accept": "application/xml, text/xml, */*",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

    async def fetch_major_news(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        네이버 경제 뉴스 RSS를 파싱하여 상위 N개의 주요 뉴스 목록을 반환합니다.
        
        :param limit: 가져올 뉴스 개수 (기본 5개)
        :return: [{'title', 'link', 'pub_date'}]
        """
        print(f"[정보] 네이버 경제 뉴스 RSS 수집 중... ({self.RSS_URL})")
        
        async with httpx.AsyncClient(timeout=10.0, headers=self.headers, follow_redirects=True) as client:
            try:
                response = await client.get(self.RSS_URL)
                if response.status_code != 200:
                    print(f"[오류] 뉴스 RSS 조회 실패 (HTTP {response.status_code})")
                    return []
                
                # XML 파싱
                root = ET.fromstring(response.content)
                
                news_list = []
                # channel/item 요소 순회
                items = root.findall(".//item")
                
                for item in items[:limit]:
                    title = item.find("title").text if item.find("title") is not None else "제목 없음"
                    link = item.find("link").text if item.find("link") is not None else ""
                    pub_date = item.find("pubDate").text if item.find("pubDate") is not None else ""
                    
                    # CDATA 섹션 등으로 감싸져 있을 수 있으므로 정규화
                    title = title.strip()
                    link = link.strip()
                    
                    news_list.append({
                        "title": title,
                        "link": link,
                        "pub_date": pub_date
                    })
                    
                print(f"[성공] 주요 경제 뉴스 수집 완료 ({len(news_list)}건)")
                return news_list
                
            except Exception as e:
                print(f"[오류] 뉴스 RSS 수집 중 에러 발생: {e}")
                return []

# 로컬 단독 테스트용
if __name__ == "__main__":
    import asyncio
    
    async def test():
        collector = NewsCollector()
        news = await collector.fetch_major_news(limit=5)
        for i, item in enumerate(news, 1):
            print(f"{i}. {item['title']}")
            print(f"   URL: {item['link']}")
            
    asyncio.run(test())
