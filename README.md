# AI 测试用例与附件生成系统 EVO (AI TestCase Generator EVO)

这是一个基于前后端分离架构的智能化测试辅助平台，专为托管业务等金融场景设计。系统对接 DeepSeek 大模型服务，提供测试数据的自动化泛化、对抗攻击生成、指令附件的动态排版与生成，以及结合 OCR 引擎的自动化结构比对评测能力。

## 🌟 核心业务场景

1. **测试集智能泛化与对抗生成**：支持基于原始 Excel 测试集，通过大模型进行数据泛化（扩充正常场景）和对抗攻击（注入异常场景）。
2. **指令附件动态生成**：支持生成排版精美的 PDF 附件，目前支持的业务场景包括：
   - 缴款通知书（需上传基础测试集 Excel 与 Word 模板）
   - **标的合同**（需上传基础测试集 Excel 与 Word 模板）
   - 各类他行定存/活期必备条款
3. **自动化评测与比对**：将生成的附件通过进程内 OCR 引擎（RapidOCR + PyMuPDF）解析，并在前端实时展示字段级解析准确率报告。
4. **全链路历史追溯**：提供强大的联合查询能力，支持通过多维度条件检索历史生成记录与比对明细，支持弹窗展示并导出 Excel 分析报表。
5. **高并发与稳定性保障**：彻底修复了全链路异步架构中的状态幽灵与雪崩问题，支持前台超大规模任务的可靠轮询与进度闭环。

## 🏗️ 项目架构

本项目采用前后端代码同仓管理：

```
TestCasesGeneratorEVO/
├── TestCasesGenerator/          # 后端 Python (FastAPI + Celery + Redis)
│   ├── app/
│   │   ├── main.py              # FastAPI 主入口
│   │   ├── common/              # 公共模块（DB、COS/MinIO 存储）
│   │   ├── core/                # Celery 异步任务配置
│   │   └── domain/ClearingService/
│   │       ├── ai_testcase_generator/  # AI 测试用例生成核心模块
│   │       │   ├── api.py             # API 路由
│   │       │   ├── llm_service.py     # DeepSeek LLM 调用层
│   │       │   ├── ocr_engine.py      # 进程内 OCR 引擎
│   │       │   ├── process_service.py # 核心业务编排
│   │       │   ├── tasks.py           # Celery 异步任务
│   │       │   └── agents/            # 各业务场景 Prompt 模板
│   │       └── in_flight_rules_automation_tools/  # 事中规则自动化
│   ├── Dockerfile
│   ├── requirements.txt
│   └── Templets/                # Word/Excel 模板文件
├── TestCasesGeneratorWeb/       # 前端 React SPA
│   ├── src/
│   │   ├── components/pages/    # 页面组件 (Ant Design)
│   │   ├── configs/             # API 配置
│   │   └── services/            # 接口服务层
│   ├── Dockerfile
│   └── nginx.conf               # Nginx 反向代理配置
├── docker/mysql/init/           # 数据库初始化 SQL
├── docker-compose.yml            # Docker Compose 编排
└── README.md
```

### 技术栈

| 层级 | 技术 |
|------|------|
| **后端框架** | FastAPI (Python 3.12) |
| **异步队列** | Celery + Redis |
| **大模型** | DeepSeek (deepseek-v4-flash)，OpenAI SDK 兼容模式 |
| **OCR 引擎** | RapidOCR + PyMuPDF（进程内，零网络依赖） |
| **PDF 渲染** | ReportLab（中英文混排、复杂表格） |
| **对象存储** | MinIO（本地）/ 腾讯云 COS（生产） |
| **数据库** | MariaDB 11.4 |
| **前端** | React + Ant Design + Axios |
| **部署** | Docker Compose（6 服务编排） |

## 🚀 快速开始（MacOS / Linux）

> **前置条件**：已安装 [Docker Desktop](https://www.docker.com/)，Python 3.12 环境为可选（仅本地开发需要）。

### 一键容器化部署

```bash
# 1. 克隆仓库
git clone https://github.com/vstesla/ai_testcase_generator_evo.git
cd ai_testcase_generator_evo

# 2. 配置环境变量（首次运行必需）
cp TestCasesGenerator/.env.example TestCasesGenerator/.env
# 编辑 .env 文件，填入你的 DEEPSEEK_API_KEY

# 3. 启动全部服务
docker compose up -d --build
```

启动后访问：
| 服务 | 地址 |
|------|------|
| 前端页面 | `http://localhost:3000` |
| 后端 API 文档 (Swagger) | `http://localhost:8000/docs` |
| MinIO 管理控制台 | `http://localhost:9001` (minioadmin/minioadmin) |

### 容器服务说明

| 服务 | 端口 | 说明 |
|------|------|------|
| `frontend` | 3000→80 | React SPA，Nginx 反向代理 |
| `backend` | 8000 | FastAPI 核心服务 |
| `celery` | - | 异步任务 Worker |
| `mysql` | 3307→3306 | MariaDB 11.4，启动时自动建表 |
| `redis` | 6379 | Celery 消息队列 Broker |
| `minio` | 9000, 9001 | 本地 S3 兼容对象存储 |

### 关键环境变量（`.env` 文件）

```bash
# 必填：DeepSeek API Key
DEEPSEEK_API_KEY=sk-your-key-here

# 数据库（容器内自动配置）
DB_HOST=mysql
DB_PORT=3306
DB_USER=root
DB_PASSWORD=localroot
DB_NAME=test_cases_db

# 对象存储（容器内使用 MinIO）
COS_SECRET_ID=minioadmin
COS_SECRET_KEY=minioadmin
COS_ENDPOINT=http://minio:9000
COS_BUCKET_NAME=ai-testcases
COS_ADDRESSING_STYLE=path

# Redis
REDIS_URL=redis://redis:6379/0

# OCR（进程内模式，默认）
USE_IN_PROCESS_OCR=true
```

### 本地开发模式

```bash
# 后端
cd TestCasesGenerator
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# Celery Worker（macOS/Linux 使用 prefork 模式）
cd TestCasesGenerator
celery -A app.core.celery_app worker --loglevel=info -c 10

# 前端
cd TestCasesGeneratorWeb
npm install
npm start
```

## 🔧 近期重要修复与改进

### 2026-06 工作环境迁移至 MacOS

1. **Docker 容器化适配**
   - 新增完整 `docker-compose.yml`，支持 MinIO 本地对象存储替代云端 COS
   - 后端 Dockerfile 新增 `libgl1`/`libglib2.0-0` 支持 RapidOCR OpenCV 依赖
   - 移除独立 OCR 微服务，统一使用进程内 OCR（`USE_IN_PROCESS_OCR=true`）

2. **连接池泄漏修复** (`db_utils.py`)
   - `connect()` 改为"验证即归还"模式：获取连接 → SELECT 1 校验 → 立即归还连接池
   - 解决每次 COS 操作泄漏一个数据库连接，最终耗尽连接池导致 MariaDB `Aborted connection` 告警

3. **Nginx DNS 动态解析** (`nginx.conf`)
   - 使用 `resolver 127.0.0.11` + 变量 `proxy_pass` 实现容器重建后 IP 自动更新
   - 修复 `--force-recreate` 后端容器后 nginx 缓存旧 IP 导致 502

4. **比对评测健壮性增强** (`process_service.py`)
   - 远程解析 DB 连接失败时设置 `is_comparison_done=1`，避免前端永久轮询卡死
   - `process_ckxy` 比对任务改为 Celery `compare_attachments_task.delay()` 分发，避免 `asyncio.create_task` 进程重启丢失

5. **COS 异常处理修复** (`cos.py`)
   - `download_file`/`generate_download_url`/`get_object` 中 `storage_path` 未初始化导致 `NameError` 覆盖原始异常

6. **重复连接池创建修复** (`api.py`)
   - `_record_generation_result` 改为复用模块级 `DBUtils` 单例，避免每次调用创建新的连接池

## 📝 团队开发规范

- **Commit 规范**: 严格使用 `类型: 描述` 格式（中文），如 `feat: 新增标的合同生成支持`、`fix: 修复连接池泄漏`、`docs: 更新文档`。
- **文档维护**: 每次功能变更必须同步更新对应目录下的 `README.md`。
- **代码质量**: 函数圈复杂度 ≤ 15，嵌套层数 ≤ 5。避免硬编码，保证系统健壮性。
- **测试与清理**: 充分测试正常/异常输入，每次测试完成后主动清理临时文件与脏数据。

---
*© Clearing Service Automation Tools · [GitHub](https://github.com/vstesla/ai_testcase_generator_evo)*
