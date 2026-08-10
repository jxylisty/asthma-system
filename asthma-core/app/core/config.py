"""
应用配置：数据库路径、CORS 域名、JWT 密钥等
"""
import os

# 项目根目录（asthma-core/）
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# SQLite 数据库路径（默认放在 data/ 目录，可通过环境变量覆盖）
DB_PATH = os.getenv(
    "DB_PATH",
    os.path.join(PROJECT_ROOT, "data", "asthma_v2.db")
)
DATABASE_URL = f"sqlite:///{DB_PATH}"

# CORS 允许的前端域名
# 开发环境默认值，生产环境通过 CORS_EXTRA_ORIGINS 环境变量追加
CORS_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
]

# Render / Vercel 生产域名（通过环境变量动态追加）
# 格式: "https://my-app.vercel.app,https://my-api.onrender.com"
# 设为 "*" 表示允许所有来源（含 credentials 限制）
EXTRA_ORIGINS = os.getenv("CORS_EXTRA_ORIGINS", "")
if EXTRA_ORIGINS == "*":
    CORS_ORIGINS = ["*"]
elif EXTRA_ORIGINS:
    CORS_ORIGINS.extend([o.strip() for o in EXTRA_ORIGINS.split(",") if o.strip()])

# ORM 模型目录路径（已内联到 app/models/tables.py，不再需要外部目录）
DATABASE_DIR = os.path.join(PROJECT_ROOT, "data")

# JWT 配置（生产环境必须通过环境变量设置）
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24小时
