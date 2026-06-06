import abc
from typing import Tuple

class BaseInFlightRuleAutomation(abc.ABC):
    """
    事中规则自动化测试基类。
    
    设计理念：
    为了支持后续 100+ 条不同的事中规则，强制要求所有具体的规则自动化脚本继承该类，
    并实现 `run_automation_batch` 接口。
    这样底层 API 就可以通过工厂模式/注册表模式统一调用，实现极好的横向扩展性（符合开闭原则）。
    """
    
    @abc.abstractmethod
    def run_automation_batch(self, test_case_count: int) -> Tuple[int, int]:
        """
        执行批量自动化测试
        
        :param test_case_count: 需要执行的测试案例数
        :return: Tuple[int, int] 返回 (comparison_count, correct_count) 即 (总比对次数, 成功次数)
        """
        pass
