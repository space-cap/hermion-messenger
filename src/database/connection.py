import os
from contextlib import contextmanager
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.database.models import Base

# .env 로드
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data.db")

# SQLite인 경우 멀티스레드 접근 에러 방지를 위해 check_same_thread 옵션을 켜줍니다.
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

# 1. SQLAlchemy Engine 생성 (개발 편의를 위해 SQL 로깅을 echo=True로 설정할 수 있음)
engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=False  # SQL 쿼리를 터미널에 로깅하고 싶다면 True로 변경
)

# 2. Session 팩토리 설정
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """데이터베이스 테이블을 생성하는 초기화 함수"""
    print(f"[정보] 데이터베이스 초기화 진행 중... (연결 주소: {DATABASE_URL})")
    Base.metadata.create_all(bind=engine)
    print("[성공] 모든 데이터베이스 테이블이 생성되었습니다.")

@contextmanager
def get_db():
    """Context Manager 기반으로 DB 세션을 안전하게 반환하고 회수하는 제너레이터"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 연동 테스트용 진입점
if __name__ == "__main__":
    init_db()
