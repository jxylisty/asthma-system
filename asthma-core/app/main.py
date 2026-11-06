"""
东方智喘 - 基于AI入血预测的中医治疗儿童哮喘机制分析系统
FastAPI 后端主入口
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.routers import system, prescriptions, herbs, compounds, prediction, expert, auth, custom_prescription, ai
from app.schemas import ResponseModel
from app.core.config import CORS_ORIGINS

app = FastAPI(
    title="东方智喘 - 哮喘方剂智能分析系统",
    description="基于入血预测的中医治疗儿童哮喘作用机制分析 API",
    version="1.0.0"
)


# ==================== 全局异常捕获 ====================

@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    """拦截 422 参数校验错误，转为统一响应格式"""
    errors = exc.errors()
    # 取第一个错误的提示信息
    msg = errors[0]["msg"] if errors else "请求参数校验失败"
    return JSONResponse(
        status_code=200,  # HTTP 层仍返回 200，业务层 code 标识错误
        content={"code": 422, "message": f"参数错误: {msg}", "data": None}
    )


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_error_handler(request: Request, exc: SQLAlchemyError):
    """拦截数据库异常，转为统一响应格式"""
    return JSONResponse(
        status_code=200,
        content={"code": 500, "message": f"数据库错误: {str(exc)}", "data": None}
    )


@app.exception_handler(Exception)
async def generic_error_handler(request: Request, exc: Exception):
    """兜底：拦截所有未处理异常"""
    return JSONResponse(
        status_code=200,
        content={"code": 500, "message": f"服务器内部错误: {str(exc)}", "data": None}
    )

# 配置 CORS 跨域，允许前端访问
# 若 CORS_ORIGINS 为通配符 ["*"]，则关闭 allow_credentials
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=("*" not in CORS_ORIGINS),
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由模块
app.include_router(auth.router, prefix="/api/v1/auth", tags=["用户认证"])
app.include_router(system.router, prefix="/api/v1/system", tags=["系统大屏"])
app.include_router(prescriptions.router, prefix="/api/v1/prescriptions", tags=["方剂分析"])
app.include_router(herbs.router, prefix="/api/v1/herbs", tags=["中药材详情"])
app.include_router(compounds.router, prefix="/api/v1/compounds", tags=["化合物与算法"])
app.include_router(prediction.router, prefix="/api/v1/prediction", tags=["入血预测"])
app.include_router(expert.router, prefix="/api/v1/expert", tags=["专家模式"])
app.include_router(custom_prescription.router, prefix="/api/v1/prescriptions", tags=["自定义处方分析"])
app.include_router(ai.router, prefix="/api/v1/ai", tags=["AI 智能问答"])


@app.get("/")
async def root():
    return {"message": "东方智喘 API 服务运行中"}
