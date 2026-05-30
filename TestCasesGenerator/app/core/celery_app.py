from celery import Celery
import os
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
load_dotenv()

# 使用 Redis 作为 Broker 和 Backend
# 你可以根据环境变量配置生产环境的 Redis，默认指向虚拟机中的 Redis
redis_url = os.environ.get("REDIS_URL", "redis://192.168.159.128:6379/0")

celery_app = Celery(
    "ai_testcase_generator_worker",
    broker=redis_url,
    backend=redis_url,
    include=['app.domain.ClearingService.ai_testcase_generator.tasks']
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Shanghai',
    enable_utc=True,
    worker_concurrency=4,  # 可以根据机器性能调整
    task_track_started=True,
    task_time_limit=3600,  # 单个任务最大执行时间（秒）
)