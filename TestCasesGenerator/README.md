# Clearing Service Automation Tools

本项目是一个基于 FastAPI 构建的自动化工具集合，旨在为托管业务提供 AI 测试用例生成和清算领域事中规则的自动化校验能力。

本仓库采用了模块化的目录结构，各个工具集在 `app/domain/ClearingService` 目录下独立维护，并通过统一的入口对外提供 API 接口。

---

## 1. 模块结构概览

目前系统集成了以下两大核心工具模块，您可以点击对应链接查看各个模块的详细设计与接口文档：

### 1.1 智能测试用例生成模块 (`ai_testcase_generator`)
- **路径**: [`app/domain/ClearingService/ai_testcase_generator`](./app/domain/ClearingService/ai_testcase_generator/)
- **功能简介**:
  该模块对接内部 AI Agent 服务，提供测试数据集的自动泛化、对抗样本生成能力。同时支持基于大模型的指令附件（如存款协议、缴款通知书、标的合同）的动态生成与排版渲染，并内置了与“解析小助”对接的比对评测能力。
- **最新架构与特性**:
  - **并发性能与稳定性飞跃**: 彻底修复了 FastAPI 同步数据库查询导致的线程池死锁，以及高并发请求下的 504 Gateway Timeout 报错，优化了 MySQL 默认事务隔离与连接泄漏的问题，保证了系统在前台多轮询环境下的绝对稳定。
  - **异步架构升级**: 引入 `Celery` + `Redis` 异步任务队列，彻底解决大批量（如 300 份）协议生成导致的 HTTP 接口超时问题。
  - **大模型底座切换**: 切换至 `DeepSeek` (`deepseek-v4-flash`)，采用 OpenAI SDK 兼容模式并开启 `JSON Output` 强制规范输出，完美解决裸数字、代码表达式等解析失败问题。
  - **稳定性增强**: 针对 AI 网关波动，引入 `Tenacity` 指数退避重试策略；同时在 Excel/PDF 渲染引擎中加入正则过滤机制，防御大模型生成的 `<script>` 或不可见控制字符导致引擎崩溃。
  - 新增支持“标的合同” (`ZLFJ_BDHT`) 业务场景的自动生成及评测白名单比对。
  - 重构了通用文件流生成逻辑，修复了单文件下载强制打 ZIP 包的问题。
  - 新增 `/generation_history` 和 `/generation_result` 接口，前后端使用唯一的 `TestCaseID` 透传状态，支持多维度分页历史查询。
- **文档链接**: [智能测试用例生成接口文档](./app/domain/ClearingService/ai_testcase_generator/README.md)

### 1.2 事中规则自动化测试模块 (`in_flight_rules_automation_tools`)
- **路径**: [`app/domain/ClearingService/in_flight_rules_automation_tools`](./app/domain/ClearingService/in_flight_rules_automation_tools/)
- **功能简介**:
  该模块基于 Playwright 构建，用于对前端页面的清算业务事中规则进行自动化 UI 校验。支持动态修改底层数据库数据以构造一致/不一致场景，通过模拟指令录入验证前端页面的红色/绿色拦截提示信息。该模块采用了高度可扩展的“注册表模式”，可轻松接入数百个不同的事中规则。
- **文档链接**: [事中规则自动化测试接口文档](./app/domain/ClearingService/in_flight_rules_automation_tools/README.md)

---

## 2. 环境依赖与运行

### 2.1 容器化部署（推荐，MacOS / Linux）
本项目已完成全栈容器化，支持一键部署。请确保本地已安装 [Docker Desktop](https://www.docker.com/)。

在项目**根目录（TestCasesGeneratorEVO）**下执行：
```bash
docker compose up -d --build
```
- 前端页面访问：`http://localhost:3000`
- 后端 API 文档：`http://localhost:8000/docs`

**注意事项**：
1. 启动前需在 `TestCasesGenerator/` 下创建 `.env` 文件（填写 DEEPSEEK_API_KEY，其余有默认值）。
2. MySQL 容器首次启动时会自动执行 `docker/mysql/init/001_schema.sql` 建表。
3. 使用 MinIO 作为本地对象存储（`http://localhost:9001`），无需连接云端 COS。

### 2.2 本地开发环境
本项目使用 Python 3.12，主要依赖项包括 `FastAPI`, `Celery`, `Uvicorn`, `RapidOCR`, `PyMuPDF`, `Playwright`, `ReportLab` 等。

如果需要使用 `in_flight_rules_automation_tools` 进行 UI 自动化，请确保已安装 Playwright 驱动：
```bash
pip install playwright
playwright install chromium
```

### 2.3 启动服务
在 `TestCasesGenerator/` 目录下，必须分别启动 API 服务和异步任务队列。

**启动 API 服务**：
```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

**启动 Celery Worker**（处理生成任务必需）：
```bash
# macOS/Linux：使用 prefork 池（默认）
celery -A app.core.celery_app worker --loglevel=info -c 10

# 开发调试：使用 solo 模式避免 fork 问题
celery -A app.core.celery_app worker --loglevel=info --pool=solo
```

---

## 3. 路由配置
所有的子模块路由都统一在 `app/domain/ClearingService_router.py` 中进行注册：
- 测试用例生成相关的接口前缀通常为：`/ai_testcase_generator`
- 事中规则自动化测试的接口前缀通常为：`/in_flight_rules`

可以通过访问 `http://127.0.0.1:8000/docs` 查看由 FastAPI 自动生成的完整 Swagger UI 接口文档。
