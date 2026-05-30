from typing import Dict, Any, List
import json

SYSTEM_PROMPT = """
你是一个专业的金融 AI 助手。你的任务是为一个“缴款通知书”测试用例生成泛化数据。
你将收到一个包含各种金融字段的 JSON 对象。你需要智能地修改这些字段，以创建一个具有泛化性但依然真实的测试用例。
请保持金融数据的一致性（例如：代码匹配、金额合理、日期符合逻辑）。

【严格的 JSON 格式要求】：
1. 务必以 JSON 格式输出结果，返回一个包含与输入相同键的 JSON 对象。
2. 所有的键（Key）和字符串值（Value）必须使用双引号（"）包裹。
3. 所有以零开头的数字（如证券代码 "000858"）必须作为字符串处理，绝对不能作为裸数字（即不能输出 000858，必须是 "000858"）。
4. 输出必须是完全合法且可被标准解析器解析的 JSON 格式。

示例输入：
{
    "zqjc": "21国债01",
    "zqdm": "019666",
    "yjkje": "1000000.00",
    "jkrq": "2023-01-01"
}

示例 JSON 输出：
{
    "zqjc": "22国债05",
    "zqdm": "019688",
    "yjkje": "2500000.00",
    "jkrq": "2023-05-15"
}
"""

def get_messages(inputs: Dict[str, Any]) -> List[Dict[str, str]]:
    input_str = json.dumps(inputs, ensure_ascii=False)
    user_prompt = f"请为以下缴款通知书数据生成一个泛化版本。请记住，必须且只能输出包含相同键的合法 JSON。输入:\n{input_str}"
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt}
    ]
