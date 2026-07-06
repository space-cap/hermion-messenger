import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from .models import Subscriber, MarketDataSnapshot, SentBriefing

# ==============================================================================
# 1. 구독자 (Subscriber) CRUD 함수
# ==============================================================================

def create_subscriber(
    db: Session,
    subscriber_id: str,
    name: str,
    phone: Optional[str] = None,
    email: Optional[str] = None,
    tier: str = "FREE",
    watchlist: Optional[List[str]] = None,
    channel_preference: str = "KAKAO"
) -> Subscriber:
    """신규 구독자를 생성합니다."""
    watchlist_json = json.dumps(watchlist or [])
    
    db_subscriber = Subscriber(
        id=subscriber_id,
        name=name,
        phone=phone,
        email=email,
        tier=tier,
        status="ACTIVE",
        watchlist=watchlist_json,
        channel_preference=channel_preference,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(db_subscriber)
    db.commit()
    db.refresh(db_subscriber)
    return db_subscriber

def get_subscriber(db: Session, subscriber_id: str) -> Optional[Subscriber]:
    """구독자 ID로 구독자를 조회합니다."""
    return db.query(Subscriber).filter(Subscriber.id == subscriber_id).first()

def get_active_subscribers(db: Session) -> List[Subscriber]:
    """모닝 브리핑 발송 대상인 활성(ACTIVE) 상태의 모든 구독자를 조회합니다."""
    return db.query(Subscriber).filter(Subscriber.status == "ACTIVE").all()

def update_watchlist(db: Session, subscriber_id: str, watchlist: List[str]) -> Optional[Subscriber]:
    """구독자의 관심 종목 목록을 업데이트합니다."""
    db_subscriber = get_subscriber(db, subscriber_id)
    if db_subscriber:
        db_subscriber.watchlist = json.dumps(watchlist)
        db_subscriber.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_subscriber)
    return db_subscriber

def update_subscription(db: Session, subscriber_id: str, tier: str, status: str) -> Optional[Subscriber]:
    """구독 등급(tier) 및 구독 상태(status)를 변경합니다."""
    db_subscriber = get_subscriber(db, subscriber_id)
    if db_subscriber:
        db_subscriber.tier = tier
        db_subscriber.status = status
        db_subscriber.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_subscriber)
    return db_subscriber

# ==============================================================================
# 2. 시장 데이터 스냅샷 (MarketDataSnapshot) CRUD 함수
# ==============================================================================

def save_market_data_snapshot(db: Session, date: str, raw_data_dict: Dict[str, Any]) -> MarketDataSnapshot:
    """수집된 금융 데이터셋 딕셔너리를 지정된 일자의 스냅샷으로 저장합니다."""
    raw_data_json = json.dumps(raw_data_dict)
    
    # 이미 해당 날짜의 스냅샷이 존재하는지 조회
    snapshot = db.query(MarketDataSnapshot).filter(MarketDataSnapshot.date == date).first()
    
    if snapshot:
        # 기존 스냅샷 업데이트
        snapshot.raw_data = raw_data_json
        snapshot.created_at = datetime.utcnow()
    else:
        # 신규 스냅샷 생성
        snapshot = MarketDataSnapshot(
            date=date,
            raw_data=raw_data_json,
            created_at=datetime.utcnow()
        )
        db.add(snapshot)
        
    db.commit()
    db.refresh(snapshot)
    return snapshot

def get_market_data_snapshot(db: Session, date: str) -> Optional[Dict[str, Any]]:
    """지정된 일자의 시장 데이터 스냅샷을 파이썬 dict 형식으로 조회합니다."""
    snapshot = db.query(MarketDataSnapshot).filter(MarketDataSnapshot.date == date).first()
    if snapshot:
        try:
            return json.loads(snapshot.raw_data)
        except json.JSONDecodeError:
            return {}
    return None

# ==============================================================================
# 3. 브리핑 발송 이력 (SentBriefing) CRUD 함수
# ==============================================================================

def create_sent_briefing(
    db: Session,
    subscriber_id: str,
    date: str,
    briefing_content: str,
    status: str = "PENDING",
    sent_at: Optional[datetime] = None,
    error_message: Optional[str] = None
) -> SentBriefing:
    """브리핑 발송 이력을 생성 및 기록합니다."""
    db_briefing = SentBriefing(
        subscriber_id=subscriber_id,
        date=date,
        briefing_content=briefing_content,
        status=status,
        sent_at=sent_at,
        error_message=error_message
    )
    db.add(db_briefing)
    db.commit()
    db.refresh(db_briefing)
    return db_briefing

def get_sent_briefings_by_subscriber(db: Session, subscriber_id: str) -> List[SentBriefing]:
    """구독자 고유 ID에 따른 전체 브리핑 발송 이력을 조회합니다."""
    return db.query(SentBriefing).filter(SentBriefing.subscriber_id == subscriber_id).all()
