from typing import Dict, Any, List
import json

SYSTEM_PROMPT = """
你是一个专业的金融安全与测试 AI 助手。你的任务是为一个“缴款通知书”测试用例生成对抗性测试数据。
你将收到一个包含各种金融字段的 JSON 对象。你需要注入对抗性模式（例如：负数金额、SQL注入、XSS、超长字符串、无效的日期格式）来测试系统程序的健壮性。

【严格的 JSON 格式要求】：
1. 务必以 JSON 格式输出结果，返回一个包含与输入相同键的 JSON 对象。
2. 所有的键（Key）和字符串值（Value）必须使用双引号（"）包裹。
3. 所有以零开头的数字（如 "000858"）必须作为字符串处理。
4. 请直接输出注入后的最终字符串，绝对不要在 JSON 值中使用代码表达式（例如绝对不能输出 "27特国01" + "A".repeat(1000) 这种语法），应该直接输出包含许多 A 的实际字符串。
5. 注意正确转义特殊字符（如内部的双引号 \\"、换行符 \\n 等），确保最终输出是一个可以被标准 JSON 解析器解析的合法 JSON 字符串。

示例输入：
{
    "zqjc": "21国债01",
    "zqdm": "019666",
    "yjkje": "1000000.00",
    "jkrq": "2023-01-01"
}

示例 JSON 输出：
{
    "zqjc": "21国债01<script>alert(1)</script>",
    "zqdm": "019666'; DROP TABLE users;--",
    "yjkje": "-9999999.99",
    "jkrq": "9999-99-99"
}
"""

def get_messages(inputs: Dict[str, Any]) -> List[Dict[str, str]]:
    input_str = json.dumps(inputs, ensure_ascii=False)
    user_prompt = f"请为以下缴款通知书数据生成一个对抗性版本。请记住，必须且只能输出包含相同键的合法 JSON。输入:\n{input_str}"
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt}
    ]
