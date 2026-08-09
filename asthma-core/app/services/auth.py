"""
认证服务：密码哈希、JWT 令牌生成与校验、注册/登录逻辑
"""
from datetime import datetime, timedelta
from typing import Optional

from passlib.context import CryptContext
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from app.core.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from app.models.tables import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """密码哈希"""
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """校验密码"""
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """生成 JWT 令牌"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    """解码 JWT 令牌，失败返回 None"""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None


def register_user(db: Session, username: str, password: str, email: str = None) -> User:
    """
    注册新用户
    raises: ValueError 用户名已存在
    """
    existing = db.query(User).filter(User.username == username).first()
    if existing:
        raise ValueError("用户名已存在")

    user = User(
        username=username,
        password_hash=hash_password(password),
        email=email,
        role="user"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """验证用户名密码，成功返回 User，失败返回 None"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user
