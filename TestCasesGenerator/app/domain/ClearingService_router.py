from fastapi import APIRouter
from app.domain.ClearingService.ai_testcase_generator.api import router as ai_testcase_generator_router
from app.domain.ClearingService.in_flight_rules_automation_tools.api import router as in_flight_rules_router

clearing_service_router = APIRouter()

# 智能测试用例生成模块路由
clearing_service_router.include_router(
    ai_testcase_generator_router,
    tags=["AI 测试用例与附件生成模块"]
)

# 事中规则自动化测试模块路由
clearing_service_router.include_router(
    in_flight_rules_router,
    tags=["事中规则自动化测试模块"]
)
