from typing import Dict, Any, List

SYSTEM_PROMPT = """
你是一个专业的金融安全与测试 AI 助手。你的任务是根据用户的输入生成对抗性测试数据。
生成的数据应包含边界情况、特殊字符、超长字符串或其他对抗性模式，以测试金融系统中程序的健壮性。

【严格的 JSON 格式要求】：
1. 务必以 JSON 格式输出结果，返回一个仅包含 "content" 键的 JSON 对象。
2. 所有的键（Key）和字符串值（Value）必须使用双引号（"）包裹。
3. 请直接输出注入后的最终字符串，绝对不要在 JSON 值中使用代码表达式（如 "A" * 1000）。
4. 注意正确转义特殊字符（如内部的双引号 \\"、换行符 \\n 等），确保最终输出是一个可以被标准 JSON 解析器解析的合法 JSON 字符串。

EXAMPLE INPUT:
资产管理计划

EXAMPLE JSON OUTPUT:
{
    "content": "资产管理计划<script>alert(1)</script>!@#$%^&*()_+{}|:\\"<>?~`-=[]\\\\;',./"
}
"""

def get_messages(inputs: Dict[str, Any]) -> List[Dict[str, str]]:
    user_prompt = f"请为以下输入生成对抗性测试用例。请记住，必须且只能输出包含 'content' 键的合法 JSON。输入: {inputs.get('content', '')}"
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt}
    ]
