"""
数据库连接与 Session 依赖注入
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import DATABASE_URL

# 创建引擎（SQLite 需要check_same_thread=False）
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False  # 生产环境关闭 SQL 日志
)

# Session 工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """FastAPI 依赖注入：获取数据库 Session，请求结束后自动关闭"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
