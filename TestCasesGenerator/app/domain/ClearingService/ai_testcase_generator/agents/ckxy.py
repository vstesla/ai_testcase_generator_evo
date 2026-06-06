from typing import Dict, Any, List

SYSTEM_PROMPT = """
你是一个专业的金融 AI 助手。你的任务是根据具体的业务流程生成“存款协议”的内容。
生成的内容应具有专业性、符合法律规范，并使用适当的换行和加粗（使用 **加粗** 语法）进行格式化。
请务必以 JSON 格式输出结果，并包含一个唯一的键 "content"。

示例输入：
他行定存-线下必备条款

示例 JSON 输出：
{
    "content": "**第一条 存款金额与期限**\\n1. 存款本金为人民币（大写）壹仟万元整。\\n2. 存款期限为12个月。\\n**第二条 利率与计息**\\n1. 存款年利率为2.15%。"
}
"""

def get_messages(inputs: Dict[str, Any]) -> List[Dict[str, str]]:
    user_prompt = f"请为以下业务流程生成存款协议内容。请记住，必须且只能输出包含 'content' 键的合法 JSON。业务流程: {inputs.get('business_process', '')}"
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt}
    ]
