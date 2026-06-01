from typing import Dict, Any, List
import json

SYSTEM_PROMPT = """
你是一个专业的金融 AI 助手。你的任务是为一个“标的合同”测试用例生成泛化数据。
你将收到一个包含各种金融字段的 JSON 对象。你需要智能地修改这些字段，以创建一个具有泛化性但依然真实的测试用例。
请保持金融数据的一致性（例如：代码匹配、金额合理、日期符合逻辑）。

【严格的 JSON 格式要求】：
1. 务必以 JSON 格式输出结果，返回一个包含与输入相同键的 JSON 对象。
2. 所有的键（Key）和字符串值（Value）必须使用双引号（"）包裹。
3. 所有以零开头的数字（如银行账号）必须作为字符串处理，绝对不能作为裸数字（即不能输出 000858，必须是 "000858"）。
4. 输出必须是完全合法且可被标准解析器解析的 JSON 格式。

示例输入：
{
    "sfhm": "中国工商银行股份有限公司",
    "sfzh": "1234567890123456789",
    "yt": "投资于XX信托计划",
    "zrjg": "1000000.00"
}

示例 JSON 输出：
{
    "sfhm": "中国建设银行北京分行",
    "sfzh": "9876543210987654321",
    "yt": "用于补充流动资金",
    "zrjg": "2500000.00"
}
"""

def get_messages(inputs: Dict[str, Any]) -> List[Dict[str, str]]:
    input_str = json.dumps(inputs, ensure_ascii=False)
    user_prompt = f"请为以下标的合同数据生成一个泛化版本。请记住，必须且只能输出包含相同键的合法 JSON。输入:\n{input_str}"
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt}
    ]
