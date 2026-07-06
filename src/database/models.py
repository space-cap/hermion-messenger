from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Integer, ForeignKey
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Subscriber(Base):
    """구독자 정보를 보관하는 테이블 모델"""
    __tablename__ = "subscribers"
    
    id = Column(String(50), primary_key=True)
    name = Column(String(50), nullable=False)
    phone = Column(String(255), nullable=True)  # 암호화된 상태로 저장
    email = Column(String(255), nullable=True)  # 암호화된 상태로 저장
    tier = Column(String(20), default="FREE", nullable=False)  # FREE, PREMIUM
    status = Column(String(20), default="ACTIVE", nullable=False)  # ACTIVE, CANCELLED, EXPIRED
    watchlist = Column(Text, default="[]", nullable=False)  # JSON 배열 형태의 String (예: ["005930", "000660"])
    channel_preference = Column(String(20), default="KAKAO", nullable=False)  # KAKAO, EMAIL
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Subscriber(id='{self.id}', name='{self.name}', tier='{self.tier}', status='{self.status}')>"

class MarketDataSnapshot(Base):
    """매일 아침 수집된 국내외 금융 및 공시 통합 데이터셋 스냅샷 테이블 모델"""
    __tablename__ = "market_data_snapshots"
    
    date = Column(String(10), primary_key=True)  # YYYY-MM-DD
    raw_data = Column(Text, nullable=False)  # 통합 수집된 JSON 형태의 String
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<MarketDataSnapshot(date='{self.date}', created_at='{self.created_at}')>"

class SentBriefing(Base):
    """구독자별 최종 생성 및 발송 완료된 브리핑 내역 테이블 모델"""
    __tablename__ = "sent_briefings"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    subscriber_id = Column(String(50), ForeignKey("subscribers.id"), nullable=False)
    date = Column(String(10), nullable=False)  # YYYY-MM-DD
    briefing_content = Column(Text, nullable=False)
    status = Column(String(20), default="PENDING", nullable=False)  # PENDING, SUCCESS, FAILED
    sent_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)

    def __repr__(self):
        return f"<SentBriefing(id={self.id}, subscriber_id='{self.subscriber_id}', date='{self.date}', status='{self.status}')>"
