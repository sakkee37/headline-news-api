from fastapi import FastAPI
from routers import new,users,favorite,history
from fastapi.middleware.cors import CORSMiddleware

from utils.exception_handler import register_exception_handlers

app = FastAPI()
app.include_router(new.router)

app.include_router(users.router)

app.include_router(favorite.router)

app.include_router(history.router)

# 注册异常处理器
register_exception_handlers(app)

# 允许的来源（可以是域名列表）
origins = [
    "http://localhost",
    "http://localhost:3000",
    "https://your-frontend-domain.com"  # 你的服务器IP/域名
]

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    # allow_origins=[origins],      # 生成环境
    allow_origins=["*"],      # 允许访问的源
    allow_credentials=True,   # 允许携带 Cookie
    allow_methods=["*"],      # 允许所有请求方法
    allow_headers=["*"],      # 允许所有请求头
)