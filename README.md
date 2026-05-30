# AI 测试用例与附件生成系统 EVO (AI TestCase Generator EVO)

这是一个基于前后端分离架构的智能化测试辅助平台，专为托管业务等金融场景设计。系统对接内部 AI Agent 服务，提供测试数据的自动化泛化、对抗攻击生成、指令附件的动态排版与生成，以及结合 OCR 引擎的自动化结构比对评测能力。

## 🌟 核心业务场景

1. **测试集智能泛化与对抗生成**：支持基于原始 Excel 测试集，通过大模型进行数据泛化（扩充正常场景）和对抗攻击（注入异常场景）。
2. **指令附件动态生成**：支持生成排版精美的 PDF/Word 附件，目前支持的业务场景包括：
   - 缴款通知书（需上传基础测试集 Excel 与 Word 模板）
   - **标的合同**（需上传基础测试集 Excel 与 Word 模板） - *✨ New!*
   - 各类他行定存/活期必备条款
3. **自动化评测与比对**：将生成的附件推送至解析引擎，并在前端实时展示字段级解析准确率报告。
4. **全链路历史追溯**：提供强大的联合查询能力，支持通过多维度条件检索历史生成记录与比对明细，支持弹窗展示并导出 Excel 分析报表。

## 🏗️ 项目架构

本项目采用前后端代码同仓管理：

- [**TestCasesGenerator (后端)**](./TestCasesGenerator/README.md)
  - 基于 `FastAPI` 构建的高性能异步 API。
  - 集成了 `Celery` + `Redis` 异步任务队列，支持大批量并发生成任务（如一次性生成 300 份指令附件）。
  - 集成了 `Playwright` 用于 UI 自动化，全面对接 **DeepSeek (deepseek-v4-flash)** 大模型服务（基于 OpenAI SDK 兼容模式，开启 JSON Output 稳定输出），并引入 `Tenacity` 指数退避重试策略应对网关波动。
- [**TestCasesGeneratorWeb (前端)**](./TestCasesGeneratorWeb/README.md)
  - 基于 `React` 和 `Ant Design` 构建的现代化单页应用 (SPA)。
  - 提供响应式的配置面板、进度定时轮询（完美适配 Celery 后台队列）、历史数据检索及结果分析大屏。

## 🚀 部署与运行策略

根据本项目的环境特性，我们制定了以下双端开发与部署策略：

### 方案 A：Windows 本地开发模式（主力开发）
由于部分 Windows 机器底层虚拟化（WSL）组件损坏，**推荐开发调试统一在物理机本地环境运行**。

1. **后端 API 启动**:
   ```bash
   cd TestCasesGenerator
   # 请确保已配置好 .env 文件 (包含 COS_SECRET_ID, REDIS_URL, DEEPSEEK_API_KEY 等敏感信息)
   uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```
2. **异步队列 Celery Worker 启动** (必须启动才能处理生成任务):
   ```bash
   cd TestCasesGenerator
   # Windows 环境下推荐使用 threads 池或 solo 模式启动
   celery -A app.core.celery_app worker --loglevel=info -P threads -c 10
   ```
3. **前端启动**:
   ```bash
   cd TestCasesGeneratorWeb
   npm install
   npm start
   ```
   *前端服务将运行在 `http://localhost:3000`，并通过代理与后端交互。*

### 方案 B：Mac/Linux 容器化部署模式（测试与生产）
后续若在 MacBook 等类 Unix 设备上运行，可直接使用内置的 Docker 编排一键启动：

```bash
# 在项目根目录下执行
docker-compose up -d --build
```
- 前端页面访问：`http://localhost`
- 后端接口访问：`http://localhost:8000/docs`

> **注意**：容器化部署时，同样需要在后端目录下提供包含有效密钥的 `.env` 文件。

## 📝 团队开发规范

- **Commit 规范**: 严格使用 `类型: 描述` 格式（中文），如 `feat: 新增标的合同生成支持`、`fix: 修复XX异常`、`docs: 更新文档`。
- **文档维护**: 每次功能变更必须同步更新对应目录下的 `README.md`，说明新功能、用法及注意事项。
- **代码质量**: 函数圈复杂度必须 $\le 15$，嵌套层数必须 $\le 5$。避免硬编码，保证系统健壮性。
- **测试与清理**: 充分测试正常/异常输入，确保业务稳定；每次测试完成后主动清理产生的临时文件与脏数据。

---
*版权所有 © Clearing Service Automation Tools*
