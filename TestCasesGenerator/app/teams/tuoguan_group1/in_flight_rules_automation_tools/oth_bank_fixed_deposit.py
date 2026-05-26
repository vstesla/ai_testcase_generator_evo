import logging
import time
from datetime import datetime
from typing import Dict, Any, List, Tuple

# 引入 Playwright 的同步 API，适用于编写线性的自动化测试脚本
from playwright.sync_api import sync_playwright, expect
import requests

# 假设项目中有通用的 DBUtils，路径根据实际情况调整
from app.common.db.db_utils import DBUtils

# 引入基类，保障扩展性
from app.teams.tuoguan_group1.in_flight_rules_automation_tools.base_rule import BaseInFlightRuleAutomation

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OthBankFixedDepositAutomation(BaseInFlightRuleAutomation):
    """
    他行定存 - 外汇交易中心数据比对 - 事中规则自动化测试工具
    """
    
    def __init__(self):
        self.db = DBUtils()

    def update_trade_center_data(self, cjonbr: str, custom_updates: Dict[str, Any] = None):
        """
        (1) 构造测试数据：修改 INFTYCK 表中指定 CJONBR 的记录。
        """
        today_str = datetime.now().strftime("%Y-%m-%d 00:00:00.000")
        
        updates = {
            "TRSDAT": today_str,
            "SCJSRQ": today_str,
            "DQZQRQ": today_str
        }
        
        if custom_updates:
            updates.update(custom_updates)
            
        set_clause = ", ".join([f"{k} = %s" for k in updates.keys()])
        values = list(updates.values())
        values.append(cjonbr)
        
        sql = f"UPDATE TGUSER.INFTYCK SET {set_clause} WHERE CJONBR = %s"
        
        try:
            self.db.execute_query(sql, tuple(values))
            logger.info(f"成功更新 CJONBR={cjonbr} 的数据: {updates}")
        except Exception as e:
            logger.error(f"更新 CJONBR={cjonbr} 失败: {e}")
            raise

    def create_order(self, payload: dict) -> str:
        """
        (2) 前置准备：模拟调用 order_create 接口发起指令，获取 order_id
        """
        url = "http://api.example.com/order_create"
        try:
            # 真实对接时解除注释
            # response = requests.post(url, json=payload)
            # response.raise_for_status()
            # order_id = response.json().get("order_id")
            order_id = f"MOCK_ORDER_{int(time.time())}"
            logger.info(f"成功创建指令, order_id: {order_id}")
            return order_id
        except Exception as e:
            logger.error(f"发起指令失败: {e}")
            return f"MOCK_ORDER_{int(time.time())}"

    def verify_in_flight_rule(self, order_id: str, cjonbr: str, expected_msgs: List[str]):
        """
        (3) UI 自动化执行：通过 Playwright 操作前端页面，触发并验证事中规则。
        """
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False, args=['--start-maximized'])
            context = browser.new_context(no_viewport=True)
            page = context.new_page()
            
            try:
                page.goto("http://frontend.example.com/instruction_view")
                
                page.locator("input[placeholder='请输入指令编号']").fill(order_id)
                page.locator("button:has-text('查询')").click()
                
                page.locator("button:has-text('指令经办')").first.click()
                
                base_locator = page.frame_locator("iframe").first 
                cjonbr_input = base_locator.get_by_label("外汇交易中心成交编号") 
                
                cjonbr_input.fill(cjonbr)
                cjonbr_input.blur() 
                
                page.wait_for_timeout(2000) 
                
                for msg in expected_msgs:
                    msg_span = base_locator.locator(f"span:has-text('{msg}')").first
                    msg_span.scroll_into_view_if_needed()
                    expect(msg_span).to_be_visible(timeout=5000)
                        
                logger.info(f"✅ 指令 {order_id} (CJONBR: {cjonbr}) 自动化校验通过！")
                
            except Exception as e:
                logger.error(f"❌ UI 自动化校验失败: {e}")
                page.screenshot(path=f"error_{order_id}_{cjonbr}.png")
                raise
            finally:
                page.wait_for_timeout(3000)
                browser.close()

    def run_automation_batch(self, test_case_count: int) -> Tuple[int, int]:
        """
        实现基类接口，封装当前规则特有的批量案例生成和执行逻辑。
        将特定业务的循环处理逻辑内聚在类中，而非暴露在 api.py 中，极大提升扩展性。
        """
        comparison_count = 0
        correct_count = 0
        
        # 预设可用的CJONBR列表 (数据库中已插入的记录)
        available_cjonbrs = [f"CR202605011464{i}" for i in range(1, 7)]
        actual_test_count = min(test_case_count, len(available_cjonbrs))
        
        for i in range(actual_test_count):
            cjonbr = available_cjonbrs[i]
            comparison_count += 1
            
            try:
                # 奇数次测试一致场景，偶数次测试不一致场景
                is_consistent_scenario = (i % 2 == 0)
                
                if is_consistent_scenario:
                     custom_updates = {
                         "TYCKJE": 1000000.00,
                         "RCVBNK": "招商银行"
                     }
                     expected_msgs = ["外汇交易中心数据一致"]
                else:
                     custom_updates = {
                         "TYCKJE": 999999.00,
                         "RCVBNK": "错误银行"
                     }
                     expected_msgs = [
                         "外汇交易中心数据：999999.00", 
                         "外汇交易中心数据：错误银行"
                     ]
                
                # 1. 更新数据库
                self.update_trade_center_data(cjonbr=cjonbr, custom_updates=custom_updates)
                
                # 2. 模拟创建指令
                order_payload = {"cjonbr": cjonbr, "amount": 1000000.00}
                order_id = self.create_order(payload=order_payload)
                
                # 3. UI 自动化验证
                self.verify_in_flight_rule(order_id=order_id, cjonbr=cjonbr, expected_msgs=expected_msgs)
                
                correct_count += 1
                
            except Exception as e:
                 logger.error(f"案例 {cjonbr} 测试失败: {e}")
                 continue
                 
        return comparison_count, correct_count


if __name__ == "__main__":
    # __main__ 方法被极大简化，仅作为当前脚本的独立调试入口
    # 所有内部逻辑(如一致/不一致场景拼装)都已内聚在 run_automation_batch 中
    auto_tool = OthBankFixedDepositAutomation()
    
    logger.info("开始执行本地联调...")
    # 调试执行2条记录：1条一致场景，1条不一致场景
    comp_count, corr_count = auto_tool.run_automation_batch(test_case_count=2)
    
    logger.info(f"本地联调结束 -> 总案例数: {comp_count}, 成功数: {corr_count}")