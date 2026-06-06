from typing import Dict, Any, List

SYSTEM_PROMPT = """
你是一个专业的金融 AI 助手。你的任务是根据用户的输入为“SPV投资范围”生成泛化数据。
生成的数据应保持金融业务的合理性、专业性，并引入合理的变异以用于测试目的。
请务必以 JSON 格式输出结果，并包含一个唯一的键 "spvInvestmentScope"。

示例输入：
仅限投资于银行存款

示例 JSON 输出：
{
    "spvInvestmentScope": "银行存款、同业存单、货币市场基金"
}
"""

def get_messages(inputs: Dict[str, Any]) -> List[Dict[str, str]]:
    user_prompt = f"请为以下SPV投资范围生成泛化数据。请记住，必须且只能输出包含 'spvInvestmentScope' 键的合法 JSON。输入: {inputs.get('spvInvestmentScope', '')}"
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt}
    ]
