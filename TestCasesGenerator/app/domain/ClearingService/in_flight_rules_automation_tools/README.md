# 事中规则自动化测试工具 (In-Flight Rules Automation Tools)

本模块是一个基于 FastAPI 和 Playwright 构建的自动化测试服务，主要用于清算领域各项“事中规则”的自动化校验。

该工具通过接口触发测试任务，底层自动模拟数据库数据篡改、指令发起以及前端页面 UI 的自动化校验，最终输出一致性比对结果。本系统采用高度可扩展的**注册表模式 (Registry Pattern)** 与**面向接口编程**设计，能够轻松支持后续 100+ 条不同事中规则的快速接入。

---

## 1. 核心架构设计

为了保证系统的高可扩展性和健壮性，代码结构设计如下：

*   **`base_rule.py`**: 抽象基类 `BaseInFlightRuleAutomation`。强制所有具体规则必须继承该类并实现 `run_automation_batch` 方法，保障对外调用接口的统一性。
*   **`api.py`**: 接口层。定义了业务类型 (`BusinessTypeEnum`) 与规则名称 (`RuleNameEnum`) 枚举，并通过 `RULE_REGISTRY` 字典管理接口路由到具体执行类的分发逻辑，彻底消除庞大的 if-else 判断。
*   **`oth_bank_fixed_deposit.py`**: 具体的业务规则执行类示例。实现了“他行定存 - 外汇交易中心数据比对”规则。内聚了数据库更新、接口 Mock 以及 Playwright 跨域 iframe 强行滚动的 UI 自动化逻辑。

---

## 2. 如何扩展新规则

当需要开发一条新的事中规则时，请遵循以下 3 个步骤：

1.  **编写具体业务脚本**:
    在目录下新建 Python 文件，创建一个继承自 `BaseInFlightRuleAutomation` 的类，并在其中实现 `run_automation_batch` 方法。
2.  **追加枚举类型**:
    在 `api.py` 中，找到 `BusinessTypeEnum` 和 `RuleNameEnum`，追加新的业务类型和规则名称。
3.  **注册执行类**:
    在 `api.py` 的 `RULE_REGISTRY` 字典中增加映射关系：
    ```python
    (BusinessTypeEnum.NEW_BUSINESS, RuleNameEnum.NEW_RULE): NewAutomationClass
    ```

---

## 3. 接口文档

### 3.1 执行事中规则自动化测试

*   **接口地址**: `/in_flight_rules/run_automation`
*   **请求方法**: `POST`
*   **Content-Type**: `application/json`

#### 请求参数 (Body)

| 参数名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| `business_type` | Enum(String) | 是 | 业务类型。目前支持：`他行定存` |
| `rule_name` | Enum(String) | 是 | 事中规则名称。目前支持：`外汇交易中心数据比对` |
| `test_case_count` | Integer | 是 | 需要执行测试的案例总数。必须大于 0 |

**请求示例**:
```json
{
    "business_type": "他行定存",
    "rule_name": "外汇交易中心数据比对",
    "test_case_count": 4
}
```

#### 响应结构 (JSON)

| 字段名 | 类型 | 说明 |
| :--- | :--- | :--- |
| `test_case_id` | String | 本次测试任务的唯一批次 ID，格式如：`TC_IFR_OBFD_WHJYSJ_1684392000000` |
| `comparison_count` | Integer | 实际执行比对的测试案例总次数 |
| `correct_count` | Integer | UI 自动化断言通过的成功次数 |
| `correct_percentage` | Float | 测试通过率（百分比），如 `100.0` 表示 100% |

**响应示例**:
```json
{
    "test_case_id": "TC_IFR_OBFD_WHJYSJ_1716012345678",
    "comparison_count": 4,
    "correct_count": 4,
    "correct_percentage": 100.0
}
```

---

## 4. 运行与调试

### 4.1 本地联调单个规则
如果仅需调试某一条具体的规则脚本，无需启动 FastAPI，直接运行对应的 Python 文件即可：
```bash
python app/domain/ClearingService/in_flight_rules_automation_tools/oth_bank_fixed_deposit.py
```

### 4.2 注意事项
1.  **Playwright 依赖**: 本工具依赖 `playwright` 进行 UI 自动化。如果是首次运行，请确保已安装浏览器驱动：
    ```bash
    pip install playwright
    playwright install chromium
    ```
2.  **异步防阻塞**: UI 自动化测试属于长耗时的同步阻塞任务，`api.py` 中已通过 `await asyncio.to_thread(...)` 将其转移至后台线程池运行，确保 FastAPI 事件循环不被卡死。
3.  **截图保留现场**: 当 UI 验证（如找不到提示元素、断言超时）失败时，脚本会在当前目录下自动截取一张名为 `error_指令编号_成交编号.png` 的截图，便于错误排查。