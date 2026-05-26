import logging
import requests
import json
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class LLMService:
    """
    LLM 服务类，负责调用自定义 API 生成泛化和对抗数据。
    """
    def __init__(self):
        self.api_url = "http://testhub-ai-runtime-gateway.paasuat.cmbchina.cn/agent/v1/chat-messages"
        self.user_id = "IT703434"
        
        # 定义不同任务的 API Token
        self.tokens = {
            "spvSubjectType": "app-C2O7pVVdqpfKuVOjrgCfl2dQ",
            "prdInvestmentScope": "app-C2O7pVVdadawdaOjrgCfl2dQ",
            "spvInvestmentScope": "app-C2O7pVVmnnuuukOjrgCfl2dQ",
            "adversarial": "app-C2O7pVVduikanggOjrgCfl2dQ",
            "ckxy": "app-C2O7pVVauicvggOjrgCfl2dQ",
            "jktzs": "app-C2O7pVVduikanggOjrgCcv38k",
            "jktzs_adversarial": "app-C2O7pVVduikanggOjrgCcv66k"
        }

    def _extract_answer_from_stream(self, response):
        import json
        last_answer = ""
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode('utf-8').strip()
                if decoded_line.startswith("data:"):
                    json_str = decoded_line[5:].strip()
                    if not json_str: continue
                    try:
                        data = json.loads(json_str)
                        if "answer" in data:
                            last_answer = data["answer"]
                    except json.JSONDecodeError:
                        continue
        return last_answer

    def _clean_and_parse_answer(self, last_answer, inputs):
        import json
        clean_answer = last_answer
        if "</think>" in clean_answer:
            parts = clean_answer.split("</think>")
            if len(parts) > 1: clean_answer = parts[-1].strip()
        
        try:
            clean_answer = clean_answer.strip()
            if clean_answer.startswith("```json"): clean_answer = clean_answer[7:]
            elif clean_answer.startswith("```"): clean_answer = clean_answer[3:]
            if clean_answer.endswith("```"): clean_answer = clean_answer[:-3]
            
            parsed_data = json.loads(clean_answer.strip())
            if isinstance(parsed_data, dict): return list(parsed_data.values())[0]
            return str(parsed_data)
        except json.JSONDecodeError:
            logger.warning(f"无法解析 JSON: {clean_answer[:50]}...")
            return clean_answer.strip()

    def _call_custom_api(self, token: str, inputs: Dict[str, Any]) -> str:
        headers = {
            "Authorization": f"Bearer {token}", "Content-Type": "application/json",
            "Accept": "text/event-stream", "Cache-Control": "no-cache", "Connection": "keep-alive"
        }
        payload = { "inputs": inputs, "query": "执行任务", "conversation_id": "", "user": self.user_id }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=payload, stream=True, timeout=300)
            response.raise_for_status()
            
            last_answer = self._extract_answer_from_stream(response)
            
            if not last_answer:
                 logger.warning("未从 API 响应中提取到有效 answer")
                 return list(inputs.values())[0] if inputs else "[ERROR]"
                 
            return self._clean_and_parse_answer(last_answer, inputs)
                
        except Exception as e:
            logger.error(f"API 调用失败: {e}")
            return list(inputs.values())[0] if inputs else "[ERROR]"
    def generate_spvSubjectType(self, element_value: str) -> str:
        """
        生成 spvSubjectType 的泛化数据
        """
        token = self.tokens["spvSubjectType"]
        inputs = {"spvSubjectType": element_value}
        return self._call_custom_api(token, inputs)

    def generate_prdInvestmentScope(self, element_value: str) -> str:
        """
        生成 prdInvestmentScope 的泛化数据
        """
        token = self.tokens["prdInvestmentScope"]
        inputs = {"prdInvestmentScope": element_value}
        return self._call_custom_api(token, inputs)

    def generate_spvInvestmentScope(self, element_value: str) -> str:
        """
        生成 spvInvestmentScope 的泛化数据
        """
        token = self.tokens["spvInvestmentScope"]
        inputs = {"spvInvestmentScope": element_value}
        return self._call_custom_api(token, inputs)

    def generate_adversarial_data(self, element_value: str) -> str:
        """
        生成对抗攻击数据
        """
        token = self.tokens["adversarial"]
        inputs = {"content": element_value} # 假设对抗接口接收 content 变量
        return self._call_custom_api(token, inputs)

    def generate_ckxy(self, business_process: str) -> str:
        """
        生成存款协议 (ckxy) 数据
        根据传入的业务流程(business_process)调用大模型进行生成
        """
        token = self.tokens["ckxy"]
        inputs = {"business_process": business_process} 
        return self._call_custom_api(token, inputs)

    def generate_jktzs(self, **kwargs) -> str:
        """
        生成缴款通知书 (jktzs) 测试集的泛化数据
        通过 **kwargs 动态接收 Excel 测试集中的所有变量字段（如 zqmc, zqdm_1 等）
        """
        token = self.tokens["jktzs"]
        # 直接将所有传入的变量组装成字典传给大模型网关
        inputs = kwargs
        return self._call_custom_api(token, inputs)

    def generate_jktzs_adversarial(self, **kwargs) -> str:
        """
        生成缴款通知书 (jktzs_adversarial) 测试集的对抗攻击数据
        通过 **kwargs 动态接收 Excel 测试集中的所有变量字段
        """
        token = self.tokens["jktzs_adversarial"]
        inputs = kwargs
        return self._call_custom_api(token, inputs)

