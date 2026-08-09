"""
统一响应封装
"""
from pydantic import BaseModel
from typing import Any


class ResponseModel(BaseModel):
    """统一响应格式"""
    code: int = 200
    message: str = "success"
    data: Any = None
