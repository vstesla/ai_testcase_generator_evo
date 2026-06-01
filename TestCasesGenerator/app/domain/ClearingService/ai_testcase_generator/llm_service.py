import os
import json
import logging
from typing import List, Dict, Any

from openai import OpenAI, APIConnectionError, RateLimitError, APIStatusError
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

from app.domain.ClearingService.ai_testcase_generator.agents import (
    spv_subject_type,
    prd_investment_scope,
    spv_investment_scope,
    adversarial,
    ckxy,
    jktzs,
    jktzs_adversarial,
    bdht,
    bdht_adversarial
)

logger = logging.getLogger(__name__)

class LLMService:
    """
    LLM 服务类，负责调用 DeepSeek API 生成泛化和对抗数据。
    统一管理和数据清洗解析 LLM 返回的数据。
    """
    def __init__(self):
        # 优先从环境变量获取 DEEPSEEK_API_KEY，如果没有则使用默认值
        api_key = os.environ.get("DEEPSEEK_API_KEY", "sk-f2e82e6bca1643909869b5ef4c6c4e74")
        
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )
        self.model = "deepseek-v4-flash" # 使用用户指定的 deepseek-v4-flash 模型

    # 设计指数退避重试策略应对可能的 AI 网关波动
    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(5),
        retry=retry_if_exception_type((APIConnectionError, RateLimitError, APIStatusError)),
        reraise=True
    )
    def _call_api_with_retry(self, messages: List[Dict[str, str]]) -> Any:
        logger.info("Calling DeepSeek API...")
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            response_format={'type': 'json_object'},
            max_tokens=4096,
            temperature=0.7
        )
        return response.choices[0].message.content

    def _call_deepseek_api(self, messages: List[Dict[str, str]], fallback_val: Any = "[ERROR]") -> Any:
        try:
            content = self._call_api_with_retry(messages)
            return self._clean_and_parse_answer(content)
        except Exception as e:
            logger.error(f"DeepSeek API 调用失败（已重试）: {e}")
            return fallback_val

    def _clean_and_parse_answer(self, last_answer: str) -> Any:
        """
        清洗并解析LLM返回的answer内容

        处理步骤：
        1. 移除```...```标签（AI思考过程）
        2. 移除Markdown代码块标记
        3. 解析JSON并提取对应的值
        """
        clean_answer = last_answer.strip()

        # 移除```标签（AI思考过程）
        if "</think>" in clean_answer:
            parts = clean_answer.split("</think>")
            if len(parts) > 1: clean_answer = parts[-1].strip()

        try:
            # 清洗Markdown代码块标记
            clean_answer = clean_answer.strip()
            if clean_answer.startswith("```json"): clean_answer = clean_answer[7:]
            elif clean_answer.startswith("```"): clean_answer = clean_answer[3:]
            if clean_answer.endswith("```"): clean_answer = clean_answer[:-3]

            parsed_data = json.loads(clean_answer.strip())
            if isinstance(parsed_data, dict):
                # 如果只有一个键值对，返回值（兼容旧逻辑）
                if len(parsed_data) == 1:
                    return list(parsed_data.values())[0]
                # 如果有多个键值对，返回完整字典（缴款通知书场景）
                else:
                    return parsed_data
            return str(parsed_data)
        except json.JSONDecodeError:
            # JSON解析失败时返回清洗后的文本
            logger.warning(f"无法解析 JSON: {clean_answer[:50]}...")
            return clean_answer.strip()

    def generate_spvSubjectType(self, element_value: str) -> str:
        """生成 spvSubjectType 的泛化数据"""
        inputs = {"spvSubjectType": element_value}
        messages = spv_subject_type.get_messages(inputs)
        return self._call_deepseek_api(messages, fallback_val=element_value)

    def generate_prdInvestmentScope(self, element_value: str) -> str:
        """生成 prdInvestmentScope 的泛化数据"""
        inputs = {"prdInvestmentScope": element_value}
        messages = prd_investment_scope.get_messages(inputs)
        return self._call_deepseek_api(messages, fallback_val=element_value)

    def generate_spvInvestmentScope(self, element_value: str) -> str:
        """生成 spvInvestmentScope 的泛化数据"""
        inputs = {"spvInvestmentScope": element_value}
        messages = spv_investment_scope.get_messages(inputs)
        return self._call_deepseek_api(messages, fallback_val=element_value)

    def generate_adversarial_data(self, element_value: str) -> str:
        """生成对抗攻击数据"""
        inputs = {"content": element_value}
        messages = adversarial.get_messages(inputs)
        return self._call_deepseek_api(messages, fallback_val=element_value)

    def generate_ckxy(self, business_process: str) -> str:
        """生成存款协议 (ckxy) 数据"""
        inputs = {"business_process": business_process} 
        messages = ckxy.get_messages(inputs)
        return self._call_deepseek_api(messages, fallback_val="[ERROR] Failed to generate content.")

    def generate_jktzs(self, **kwargs) -> Any:
        """生成缴款通知书 (jktzs) 测试集的泛化数据"""
        messages = jktzs.get_messages(kwargs)
        return self._call_deepseek_api(messages, fallback_val=kwargs)

    def generate_jktzs_adversarial(self, **kwargs) -> Any:
        """生成缴款通知书 (jktzs_adversarial) 测试集的对抗攻击数据"""
        messages = jktzs_adversarial.get_messages(kwargs)
        return self._call_deepseek_api(messages, fallback_val=kwargs)

    def generate_bdht(self, **kwargs) -> Any:
        """生成标的合同 (bdht) 测试集的泛化数据"""
        messages = bdht.get_messages(kwargs)
        return self._call_deepseek_api(messages, fallback_val=kwargs)

    def generate_bdht_adversarial(self, **kwargs) -> Any:
        """生成标的合同 (bdht_adversarial) 测试集的对抗攻击数据"""
        messages = bdht_adversarial.get_messages(kwargs)
        return self._call_deepseek_api(messages, fallback_val=kwargs)
