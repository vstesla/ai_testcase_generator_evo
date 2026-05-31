from pydantic import BaseModel, Field
from typing import Optional, List, Dict

class GenerateResponse(BaseModel):
    """
    生成响应模型
    """
    TestCaseID: str             # 案例集 ID
    TestCaseGenStatus: str      # 生成状态 (P/Y/N)
    Message: str                # 消息描述
    DownloadUrl: Optional[str] = None # 下载链接 (可选)
    Attachments: Optional[List[Dict[str, str]]] = None
    is_comparison_done: Optional[bool] = None
