"""
认证模块 Schema
"""
from pydantic import BaseModel
from typing import Optional


class RegisterRequest(BaseModel):
    """注册请求"""
    username: str
    password: str
    email: Optional[str] = None


class LoginRequest(BaseModel):
    """登录请求"""
    username: str
    password: str


class UserInfo(BaseModel):
    """用户信息"""
    id: int
    username: str
    email: Optional[str] = None
    role: str = "user"


class AuthResponseData(BaseModel):
    """登录/注册响应"""
    token: str
    user: UserInfo
