import sys
import os
from dotenv import load_dotenv

# 加载 .env 环境变量
load_dotenv()

# 将项目根目录添加到 sys.path，解决直接运行 main.py 时的 "No module named 'app'" 报错
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from app.teams.tuoguan_group1_router import tuoguan_group1_router
import uvicorn
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    force=True
)
logger = logging.getLogger(__name__)

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 强制设置应用的所有 logger 的最低响应级别为 INFO
    # 这样既能打印 INFO，也能正常打印 ERROR/WARNING
    for name in logging.root.manager.loggerDict:
        if name.startswith("app."):
            logging.getLogger(name).setLevel(logging.INFO)
    logger.setLevel(logging.INFO)
    logger.info("Application startup complete. Custom loggers are set to INFO level.")
    yield
    # shutdown events if any

app = FastAPI(title="TuoGuan Group 1 Tools", lifespan=lifespan)

# 注册路由
app.include_router(tuoguan_group1_router)

@app.get("/")
def read_root():
    return {"message": "Welcome to TestCasesGenerator API"}

if __name__ == "__main__":
    logger.info("Starting server...")
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
