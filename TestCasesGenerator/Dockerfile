FROM python:3.12-slim

WORKDIR /app

# 安装 Playwright、RapidOCR (OpenCV) 及其他系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    libffi-dev \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 安装 Playwright 浏览器依赖 (由于依赖较大，只安装 chromium)
RUN playwright install --with-deps chromium

# 复制项目所有文件
COPY . .

# 暴露 FastAPI 端口
EXPOSE 8000

# 启动 FastAPI
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]