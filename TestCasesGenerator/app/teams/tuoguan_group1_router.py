from fastapi import APIRouter
from app.teams.tuoguan_group1.ai_testcase_generator import router as ai_testcase_generator_router
from app.teams.tuoguan_group1.in_flight_rules_automation_tools.api import router as in_flight_rules_router

tuoguan_group1_router = APIRouter()

# 包含 ai_testcase_generator 的路由
# 由于 api.py 中已经定义了 /api/generate 这样的完整路径，这里不需要额外的前缀，
# 但为了清晰，我们可以添加 tags
tuoguan_group1_router.include_router(ai_testcase_generator_router, tags=["ai_testcase_generator"])

# 包含事中规则自动化测试的路由
tuoguan_group1_router.include_router(in_flight_rules_router, tags=["in_flight_rules"])
