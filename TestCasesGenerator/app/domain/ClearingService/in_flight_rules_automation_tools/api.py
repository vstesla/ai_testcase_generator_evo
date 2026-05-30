from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from enum import Enum
import time
import logging
import asyncio
from typing import Type

# 引入基类和具体的实现类
from app.domain.ClearingService.in_flight_rules_automation_tools.base_rule import BaseInFlightRuleAutomation
from app.domain.ClearingService.in_flight_rules_automation_tools.oth_bank_fixed_deposit import OthBankFixedDepositAutomation

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/in_flight_rules")

# ================= 扩展性设计：业务类型与规则名称枚举 =================
# 通过枚举严格控制入参，方便后续开发直接在此追加即可，前端也可通过 OpenAPI 文档直接获取
class BusinessTypeEnum(str, Enum):
    OTH_BANK_FIXED_DEPOSIT = "他行定存"
    # 后续可直接追加，如：
    # CURRENT_DEPOSIT = "活期存款"
    # FINANCIAL_MANAGEMENT = "理财产品"

class RuleNameEnum(str, Enum):
    TRADE_CENTER_DATA_MATCH = "外汇交易中心数据比对"
    # 后续可直接追加，如：
    # AMOUNT_LIMIT_CHECK = "金额超限校验"
    # ACCOUNT_STATUS_CHECK = "账户状态异常校验"

class InFlightRuleRequest(BaseModel):
    business_type: BusinessTypeEnum
    rule_name: RuleNameEnum
    test_case_count: int

class InFlightRuleResponse(BaseModel):
    test_case_id: str
    comparison_count: int
    correct_count: int
    correct_percentage: float


# ================= 扩展性设计：规则执行注册表 (Registry Pattern) =================
# 将 (业务类型, 规则名称) 映射到对应的自动化执行类。
# 以后新增 100+ 个事中规则时，只需：
# 1. 在枚举中追加名称
# 2. 编写新的继承自 BaseInFlightRuleAutomation 的执行类
# 3. 将其注册到此字典中。
# 好处：彻底消除 api.py 中可能出现的几十上百个 if-elif-else 语句，符合开闭原则。
RULE_REGISTRY: dict[tuple[BusinessTypeEnum, RuleNameEnum], Type[BaseInFlightRuleAutomation]] = {
    (BusinessTypeEnum.OTH_BANK_FIXED_DEPOSIT, RuleNameEnum.TRADE_CENTER_DATA_MATCH): OthBankFixedDepositAutomation,
    
    # 示例：
    # (BusinessTypeEnum.CURRENT_DEPOSIT, RuleNameEnum.AMOUNT_LIMIT_CHECK): CurrentDepositAmountLimitAutomation,
}


@router.post("/run_automation", response_model=InFlightRuleResponse)
async def run_in_flight_rule_automation(request: InFlightRuleRequest = Body(...)):
    """
    执行事中规则自动化测试
    """
    if request.test_case_count <= 0:
         raise HTTPException(status_code=400, detail="测试案例数必须大于0")

    # 根据请求获取对应的自动化测试类
    rule_key = (request.business_type, request.rule_name)
    automation_class = RULE_REGISTRY.get(rule_key)
    
    if not automation_class:
        raise HTTPException(
            status_code=400, 
            detail=f"暂不支持该组合的自动化测试: 业务[{request.business_type.value}], 规则[{request.request.rule_name.value}]"
        )

    # 实例化对应的执行工具
    automation_tool = automation_class()

    # 生成唯一的测试案例ID
    timestamp = int(time.time() * 1000)
    # 此处 ID 也可以根据具体的业务类型和规则名称进行动态缩写，此处为了兼容先固定格式
    test_case_id = f"TC_IFR_OBFD_WHJYSJ_{timestamp}"
    
    try:
        # 使用 asyncio.to_thread 防止 Playwright 和数据库等同步操作阻塞 FastAPI 的事件循环
        # 调用统一的基类接口 run_automation_batch
        comparison_count, correct_count = await asyncio.to_thread(
            automation_tool.run_automation_batch,
            request.test_case_count
        )
    except Exception as e:
        logger.error(f"自动化测试执行异常: {e}")
        raise HTTPException(status_code=500, detail=f"自动化测试执行异常: {str(e)}")
    
    # 计算正确率
    correct_percentage = round((correct_count / comparison_count) * 100, 2) if comparison_count > 0 else 0.0
    
    return InFlightRuleResponse(
        test_case_id=test_case_id,
        comparison_count=comparison_count,
        correct_count=correct_count,
        correct_percentage=correct_percentage
    )
