"""
认证路由
- POST /register  用户注册
- POST /login     用户登录（返回 JWT）
- GET  /me        获取当前登录用户信息
"""
from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas import ResponseModel, RegisterRequest, LoginRequest, AuthResponseData, UserInfo
from app.services.auth import register_user, authenticate_user, create_access_token, decode_token
from app.models.tables import User

router = APIRouter()


def get_current_user(
    authorization: str = Header(..., description="Bearer <token>"),
    db: Session = Depends(get_db)
) -> User:
    """
    从 Authorization 头解析 JWT，返回当前用户。
    用于需要登录的接口依赖注入。
    """
    if not authorization.startswith("Bearer "):
        return None

    token = authorization[7:]
    payload = decode_token(token)
    if not payload:
        return None

    user_id = payload.get("sub")
    if not user_id:
        return None

    user = db.query(User).filter(User.id == int(user_id)).first()
    return user


@router.post("/register")
async def register(req: RegisterRequest, db: Session = Depends(get_db)):
    """用户注册"""
    try:
        user = register_user(db, req.username, req.password, req.email)
    except ValueError as e:
        return ResponseModel(code=400, message=str(e), data=None)

    token = create_access_token({"sub": str(user.id)})
    data = AuthResponseData(
        token=token,
        user=UserInfo(id=user.id, username=user.username, email=user.email, role=user.role)
    )
    return ResponseModel(data=data)


@router.post("/login")
async def login(req: LoginRequest, db: Session = Depends(get_db)):
    """用户登录"""
    user = authenticate_user(db, req.username, req.password)
    if not user:
        return ResponseModel(code=401, message="用户名或密码错误", data=None)

    token = create_access_token({"sub": str(user.id)})
    data = AuthResponseData(
        token=token,
        user=UserInfo(id=user.id, username=user.username, email=user.email, role=user.role)
    )
    return ResponseModel(data=data)


@router.get("/me")
async def get_me(
    authorization: str = Header(..., description="Bearer <token>"),
    db: Session = Depends(get_db)
):
    """获取当前登录用户信息"""
    user = get_current_user(authorization, db)
    if not user:
        return ResponseModel(code=401, message="未登录或登录已过期", data=None)

    return ResponseModel(data=UserInfo(
        id=user.id, username=user.username, email=user.email, role=user.role
    ))
