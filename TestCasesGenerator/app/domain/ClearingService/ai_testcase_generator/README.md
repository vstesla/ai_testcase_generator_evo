# 智能测试用例生成接口文档

本文档详细描述了测试用例生成接口的使用方法、参数说明及注意事项。

## 1. 接口简介

该服务提供三种核心能力，通过两个独立的 API 接口对外提供服务：
1. **测试集泛化 (`/api/generate`)**：支持用户上传 Excel 配置文件（测试集），后端自动解析、利用**内部 AI Agent 服务**进行数据泛化和对抗攻击生成，最终返回新的 Excel 测试用例文件。
2. **存款协议生成 (`/api/generate_attachments`)**：无需上传文件，用户只需选择业务流程并指定数量，后端将调用 AI Agent 生成协议内容，并排版生成 PDF 格式的存款协议文件。
3. **缴款通知书生成 (`/api/generate_attachments`)**：用户上传缴款通知书测试集（Excel）和模板（Word），支持调用 AI 泛化或生成对抗样本替换模板变量生成 PDF，并自动发起后台异步请求调用“解析小助”评估 PDF 内容解析准确性。

所有生成的文件均会实时回传至腾讯云 COS，并返回下载链接。

## 2. 接口详情

### 2.1 测试集泛化接口
- **接口地址**: `/ai_testcase_generator/generate`
- **请求方法**: `POST`
- **Content-Type**: `multipart/form-data`

#### 请求参数 (Form Data)

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- | :--- |
| `file` | File | 是 | - | 原始测试集 Excel 文件（.xlsx）。 |
| `enable_generalization` | Boolean | 否 | `True` | 是否开启数据泛化。 |
| `enable_adversarial` | Boolean | 否 | `False` | 是否开启对抗攻击。 |

**请求示例**:
```bash
curl -X POST "http://127.0.0.1:8000/ai_testcase_generator/generate" \
     -F "file=@/path/to/SmartJudgeConfigs.xlsx" \
     -F "enable_generalization=true" \
     -F "enable_adversarial=true"
```

### 2.2 指令附件生成接口 (存款协议 / 缴款通知书)
- **接口地址**: `/ai_testcase_generator/generate_attachments`
- **请求方法**: `POST`
- **Content-Type**: `multipart/form-data`

#### 请求参数 (Form Data)

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- | :--- |
| `business_process` | String | 是 | - | 业务流程。可选值：`他行定存-线下必备条款`, `他行定存-线上-不开具实证书必备条款`, `他行定存-线上-开具实证书必备条款`, `他行活期必备条款`, `缴款通知书` |
| `jktzs_file` | File | 否 | - | 缴款通知书测试集.xlsx 文件。**当 business_process 为“缴款通知书”时必填**。 |
| `jktzs_template` | File | 否 | - | 缴款通知书模板.docx 文件。**当 business_process 为“缴款通知书”时必填**。 |
| `file_count` | Integer | 否 | `0` | 需要生成的附件 (PDF) 数量。 |
| `enable_generalization` | Boolean | 否 | `False` | 泛化开关。 |
| `enable_adversarial` | Boolean | 否 | `False` | 对抗生成开关。 |
| `enable_comparison` | Boolean | 否 | `True` | 是否开启自动比对评测。 |

**请求示例 1: 存款协议生成 (cURL)**:
```bash
curl -X POST "http://127.0.0.1:8000/ai_testcase_generator/generate_attachments" \
     -F "business_process=他行定存-线上-不开具实证书必备条款" \
     -F "file_count=2"
```

**请求示例 2: 缴款通知书生成 (cURL)**:
```bash
curl -X POST "http://127.0.0.1:8000/ai_testcase_generator/generate_attachments" \
     -F "business_process=缴款通知书" \
     -F "jktzs_file=@/path/to/缴款通知书测试集.xlsx" \
     -F "jktzs_template=@/path/to/缴款通知书模板.docx" \
     -F "file_count=3" \
     -F "enable_generalization=true"
```

### 2.3 比对结果查询接口
- **接口地址**: `/ai_testcase_generator/comparison_result`
- **请求方法**: `GET`

#### 请求参数 (Query)

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- | :--- |
| `test_case_id` | String | 是 | - | 测试集生成的批次 ID，即生成接口返回的 `TestCaseID`。 |

**请求示例 (cURL)**:
```bash
curl -X GET "http://127.0.0.1:8000/ai_testcase_generator/comparison_result?test_case_id=TC_JKTZS_20260512001716"
```

**响应示例 (JSON)**:
```json
{
    "code": 200,
    "message": "success",
    "data": [
        {
            "file_type": "缴款通知书",
            "file_sub_type": "证券1",
            "element_key": "je",
            "element_name": "金额",
            "comparison_count": 3,
            "correct_count": 3,
            "correct_percentage": 1.0,
            "mistake_count": 0,
            "unclear_count": 0,
            "pass_or_not": "Y"
        }
    ]
}
```

### 2.5 查询 OCR 服务状态接口
**接口地址**：`/ai_testcase_generator/ocr_status`
**请求方法**：`GET`
**功能描述**：用于前端查询底层的解析小助（OCR）服务是否处于正常开启状态。系统默认使用极速的本地进程内 OCR 引擎，如果环境变量配置了 `USE_IN_PROCESS_OCR=false`，则会根据配置去检查远程微服务栈或远端 OCR 服务。
**响应示例**：
```json
{
    "code": 200,
    "message": "success",
    "data": {
        "ocr_enabled": true
    }
}
```

## 3. 响应结构 (JSON)

| 字段名 | 类型 | 说明 |
| :--- | :--- | :--- |
| `TestCaseID` | String | 生成的测试用例集批次唯一 ID（基于时间戳）。 |
| `TestCaseGenStatus` | String | 生成状态。`Y` 表示成功，`N` 表示失败。 |
| `Message` | String | 结果描述或错误信息。 |
| `DownloadUrl` | String | 生成文件的下载链接（COS 地址）。仅在“测试集泛化”模式下返回单文件链接。 |
| `Attachments` | Array | 生成的附件列表。仅在生成指令附件（存款协议/缴款通知书）时返回。 |
| `Attachments[].attachment_id` | String | 单个附件文件的唯一 ID（即 COS 上传后的 file_id）。 |
| `Attachments[].download_url` | String | 单个附件文件的下载链接。 |
| `is_comparison_done` | Boolean | 比对评测状态。如果不开启评测则直接返回 `true`；开启时初始返回 `false`，待后台比对完成后可在数据库查询。 |

**成功响应示例 (测试集泛化)**:
```json
{
    "TestCaseID": "TC_1769534376769",
    "TestCaseGenStatus": "Y",
    "Message": "Successfully processed 60 items.",
    "DownloadUrl": "https://lt8605-user1-dev-1304137470.cos.ap-guangzhou.myqcloud.com/.../TC_1769534376769.xlsx"
}
```

**成功响应示例 (指令附件生成)**:
```json
{
    "TestCaseID": "TC_JKTZS_20260512001716",
    "TestCaseGenStatus": "Y",
    "Message": "Successfully generated 3 attachments.",
    "Attachments": [
        {
            "attachment_id": "file_123abc",
            "download_url": "https://..."
        },
        {
            "attachment_id": "file_456def",
            "download_url": "https://..."
        }
    ],
    "is_comparison_done": false
}
```

## 5. 内部流程与数据存储

### 5.1 核心技术实现点
- **最新架构与特性**:
  - **纯本地进程内 OCR 解析**: 引入基于 `PyMuPDF` 和 `RapidOCR` 的 Python 原生函数级调用能力。省去了容器间的 HTTP 网络开销，大幅降低了环境依赖门槛，实现了生成后极速且离线的白名单评测闭环。
  - **动态白名单比对**: 新增前端比对字段动态选择。支持根据上传的 Word 模板文件名动态解析目标比对字段，并通过 `selected_comparison_fields` 透传至后端的文本包含算法。
  - **并发性能与稳定性飞跃**: 彻底修复了 FastAPI 同步数据库查询导致的线程池死锁，以及高并发请求下的 504 Gateway Timeout 报错，优化了 MySQL 默认事务隔离与连接泄漏的问题，保证了系统在前台多轮询环境下的绝对稳定。
  - **异步架构升级**: 引入 `Celery` + `Redis` 异步任务队列，彻底解决大批量（如 300 份）协议生成导致的 HTTP 接口超时问题。
  - **大模型底座切换**: 切换至 `DeepSeek` (`deepseek-v4-flash`)，采用 OpenAI SDK 兼容模式并开启 `JSON Output` 强制规范输出，完美解决裸数字、代码表达式等解析失败问题。
  - **稳定性增强**: 针对 AI 网关波动，引入 `Tenacity` 指数退避重试策略；同时在 Excel/PDF 渲染引擎中加入正则过滤机制，防御大模型生成的 `<script>` 或不可见控制字符导致引擎崩溃。
  - 新增支持“标的合同” (`ZLFJ_BDHT`) 业务场景的自动生成及评测白名单比对。
  - 重构了通用文件流生成逻辑，修复了单文件下载强制打 ZIP 包的问题。
  - 新增 `/generation_history` 和 `/generation_result` 接口，前后端使用唯一的 `TestCaseID` 透传状态，支持多维度分页历史查询。
- **ReportLab PDF 渲染引擎**：支持高度定制化的样式排版、复杂表格合并及多段落混合渲染，并在底层解决了中英文混合字体的适配问题。
- **并发锁机制控制**：在处理多文件批量上传 COS 时，引入了 `asyncio.Lock()` 机制，有效避免了高并发场景下由于数据库 ID 自增逻辑（`file_id_generator`）引发的**主键冲突 (Race Condition)**，保障了批量生成的稳定性。
- **文件流式传输**：摒弃传统本地落盘后再下载的模式，采用内存流（`BytesIO`）配合 FastAPI 的 `StreamingResponse` 极大地降低了服务器 IO 压力。
- **智能自动打包**：前端调用下载接口时，若生成文件 > 1，系统会自动在内存中构建 ZIP 压缩包（利用 `zipfile`），一次性下发给用户。

本系统采用 **COS 作为核心数据中转站**，数据库仅用于操作日志记录。

### 5.2 目录与数据流向

### 模式一：测试集泛化流程
1.  **Step 1**: 用户上传原始 Excel -> 存入 COS 路径 `ClearingService/ai_testcase_generator/{YYYY-MM-DD_TIMESTAMP}/{filename}`。
2.  **Step 2**: 后端下载原始文件，解析并拆分为 3 个中间文件 (`spvSubjectType.xlsx`, `prdInvestmentScope.xlsx`, `spvInvestmentScope.xlsx`)。
3.  **Step 3**: 中间文件上传至 COS 路径 `.../intermediate/{filename}`。
4.  **Step 4**: 后端下载中间文件 -> 调用 **内部 AI Agent 接口** 进行泛化/对抗处理。
5.  **Step 5**: 生成最终结果 Excel -> 上传至 COS 路径 `ClearingService/ai_testcase_generator/{YYYY-MM-DD_TIMESTAMP}/{TC_TIMESTAMP}.xlsx`。

### 模式二：存款协议生成流程
1.  **Step 1**: 后端根据传入的 `business_process`，调用 **内部 AI Agent 接口** 获取协议文本（JSON格式）。
2.  **Step 2**: 后端解析文本，处理换行与特殊字符，并使用 `reportlab` 库生成带标题和中文字体的 PDF 文件。
3.  **Step 3**: 循环生成 `file_count` 次，将每个生成的 PDF 上传至 COS 路径 `ClearingService/ai_testcase_generator/{YYYY-MM-DD_TIMESTAMP}/ckxy/TC_{业务流程}_{序号}_{时间戳}.pdf`。
4.  **Step 4**: 将生成记录（含 `test_case_id` 和 `business_process`）插入数据库 `ai_testcase_generate_record` 表。
5.  **Step 5 (可选, 后台异步)**: 如果 `enable_comparison` 开启，自动将生成的 PDF 提交至 **解析小助** 接口。系统轮询远程数据库获取解析结果，得出评测结论存入数据库 `ai_evaluation_result` 表。

### 模式三：缴款通知书生成流程
1.  **Step 1**: 用户上传测试集 (Excel) 和模板 (Word)，后端将文件存入临时目录。模板文件的命名应遵循“附件类型+模板+下划线+附件子类型+序号”的规则（如“缴款通知书模板_证券1”），后端将根据该命名动态调整后续的比对评测白名单。
2.  **Step 2**: 根据测试集中的 `TEST_AUDIT_ID` 对数据进行分组。如果开启了泛化或对抗开关，则调用 **内部 AI Agent 接口** 针对每组数据生成新内容，并将泛化/对抗后的数据合并保存为新的中间 Excel 文件上传至 COS。
3.  **Step 3**: 解析 Word 模板中的段落和表格，识别并替换 `$变量名$` 标识符。使用 `reportlab` 库重新排版并渲染成中英文混排、带表格网格线的 PDF 文件。
4.  **Step 4**: 循环复用测试数据直到满足指定的 `file_count` 数量，将生成的 PDF 批量上传至 COS 路径 `ClearingService/ai_testcase_generator/{YYYY-MM-DD_TIMESTAMP}/jktzs/TC_缴款通知书_{序号}_{时间戳}.pdf`。
5.  **Step 5**: 将生成记录插入数据库 `ai_testcase_generate_record` 表，并返回所有 PDF 的 COS 下载链接。
6.  **Step 6 (可选, 后台异步)**: 如果 `enable_comparison` 开启，自动将生成的 PDF 提交至 **解析小助** 接口。系统轮询远程数据库获取解析结果，并根据步骤1提取的附件子类型动态提取白名单字段进行评测（完全正确/部分正确/错误），最终结论存入数据库 `ai_evaluation_result` 表，比对明细存入 `attachments_compare_result` 表。

### 5.3 数据库表设计
*   **文件日志 (`file_common_table`)**: 每次文件上传（原始文件、中间文件、结果文件、PDF）都会在该表中生成记录。
*   **生成批次日志 (`ai_testcase_generate_record`)**: 记录生成的批次信息，确保每次请求的 `test_case_id` 在本表中唯一。
*   **生成附件记录 (`ai_testcase_generate_attachments`)**: 记录每次请求生成的多个 PDF 附件详情（`attachment_id` 和 `download_url`），通过 `test_case_id` 关联至生成批次。
*   **解析评测结果 (`ai_evaluation_result`)**: 用于记录缴款通知书在“解析小助”中的结构化解析评测结论（完全正确/部分正确/错误），基于 `test_case_id` 和 `file_id` 关联。
*   **评测明细 (`attachments_compare_result`)**: 记录每个文件字段级的对比明细，包含期望值、解析值、相似度得分和匹配状态。

## 6. 环境配置

系统依赖以下环境变量（通过 `.env` 文件或系统环境变量配置）：

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DEEPSEEK_API_KEY` | DeepSeek API 密钥 | (**必填**) |
| `DEEPSEEK_BASE_URL` | DeepSeek API 地址 | `https://api.deepseek.com` |
| `DEEPSEEK_MODEL` | 模型名称 | `deepseek-v4-flash` |
| `DB_HOST` / `DB_PORT` / `DB_USER` / `DB_PASSWORD` / `DB_NAME` | MySQL 连接信息 | 见 `.env` |
| `COS_SECRET_ID` / `COS_SECRET_KEY` / `COS_ENDPOINT` / `COS_BUCKET_NAME` | 对象存储配置 | MinIO 本地或腾讯云 COS |
| `REDIS_URL` | Celery Broker 地址 | `redis://127.0.0.1:6379/0` |
| `USE_IN_PROCESS_OCR` | 使用进程内 OCR | `true` |

> **Docker 部署**：容器内已预配置 MinIO 作为本地对象存储、MariaDB 作为数据库、Redis 作为消息队列。只需在 `.env` 中填入 `DEEPSEEK_API_KEY` 即可启动。

## 7. 运行与测试

### Docker 部署（推荐）
```bash
# 在项目根目录执行
docker compose up -d --build
```
访问 `http://localhost:8000/docs` 查看 API 文档。

### 本地启动 (macOS/Linux)
```bash
# API 服务
cd TestCasesGenerator
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# Celery Worker
celery -A app.core.celery_app worker --loglevel=info -c 10
```

## 8. 注意事项

1.  **文件路径**: 上传到 COS 的文件不会覆盖旧文件，每次请求都会基于时间戳创建新的目录。请根据响应中的 `DownloadUrl` 获取最新结果。
2.  **网络连通性**: 请确保部署环境能够访问内网 AI Agent 网关 (`testhub-ai-runtime-gateway.paasuat.cmbchina.cn`) 以及腾讯云 COS 服务。
3.  **API 稳定性**: 泛化和对抗攻击依赖外部 AI 服务，如果遇到响应超时或格式错误，系统会执行降级处理（保留原始值），并在日志中记录错误。
