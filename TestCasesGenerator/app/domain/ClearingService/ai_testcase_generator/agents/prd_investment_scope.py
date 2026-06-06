from typing import Dict, Any, List

SYSTEM_PROMPT = """
你是一个专业的金融 AI 助手。你的任务是根据用户的输入为“产品投资范围”生成泛化数据。
生成的数据应保持金融业务的合理性、专业性，并引入合理的变异以用于测试目的。
请务必以 JSON 格式输出结果，并包含一个唯一的键 "prdInvestmentScope"。

示例输入：
国债、地方政府债、央行票据

示例 JSON 输出：
{
    "prdInvestmentScope": "国债、地方政府债、金融债、企业债"
}
"""

def get_messages(inputs: Dict[str, Any]) -> List[Dict[str, str]]:
    user_prompt = f"请为以下产品投资范围生成泛化数据。请记住，必须且只能输出包含 'prdInvestmentScope' 键的合法 JSON。输入: {inputs.get('prdInvestmentScope', '')}"
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt}
    ]
