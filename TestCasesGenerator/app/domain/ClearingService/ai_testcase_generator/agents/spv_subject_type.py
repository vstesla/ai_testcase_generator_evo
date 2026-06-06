from typing import Dict, Any, List

SYSTEM_PROMPT = """
你是一个专业的金融 AI 助手。你的任务是根据用户的输入为“SPV主体类型”生成泛化数据。
生成的数据应保持金融业务的合理性、专业性，并引入合理的变异以用于测试目的。
请务必以 JSON 格式输出结果，并包含一个唯一的键 "spvSubjectType"。

示例输入：
信托计划

示例 JSON 输出：
{
    "spvSubjectType": "资产管理计划"
}
"""

def get_messages(inputs: Dict[str, Any]) -> List[Dict[str, str]]:
    user_prompt = f"请为以下SPV主体类型生成泛化数据。请记住，必须且只能输出包含 'spvSubjectType' 键的合法 JSON。输入: {inputs.get('spvSubjectType', '')}"
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt}
    ]
