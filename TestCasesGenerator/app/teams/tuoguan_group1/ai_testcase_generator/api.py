from fastapi import APIRouter, HTTPException, Form, UploadFile, File, Query
from pydantic import BaseModel
from typing import Optional
from enum import Enum
from app.teams.tuoguan_group1.ai_testcase_generator.process_service import ProcessService
from app.teams.tuoguan_group1.ai_testcase_generator.schemas import GenerateResponse
from app.common.cos import ObjectStorage
from app.common.db.db_utils import DBUtils
import logging
import asyncio
import os
import shutil
import time
from datetime import datetime
from fastapi.responses import StreamingResponse
from urllib.parse import quote

# 配置日志记录
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai_testcase_generator")

# 初始化服务
process_service = ProcessService()
cos_service = ObjectStorage()
DB = DBUtils()

class BusinessProcessEnum(str, Enum):
    offline_required = "他行定存-线下必备条款"
    online_no_cert = "他行定存-线上-不开具实证书必备条款"
    online_with_cert = "他行定存-线上-开具实证书必备条款"
    current_required = "他行活期必备条款"
    jktzs_required = "缴款通知书"



def _record_generation_result(result: dict):
    try:
        from app.common.db.db_utils import DBUtils
        DB = DBUtils()
        from datetime import datetime
        existing = DB.select(table='ai_testcase_generate_record', columns=['test_case_id','status','message','create_time','update_time'], where={"test_case_id": result["TestCaseID"]})
        if not existing:
            record_data = {
                "test_case_id": result["TestCaseID"],
                "status": result["TestCaseGenStatus"],
                "message": result["Message"],
                "create_time": datetime.now(),
                "update_time": datetime.now(),
                "is_comparison_done": result.get("is_comparison_done", False)
            }
            if not DB.insert("ai_testcase_generate_record", record_data):
                logger.error("Failed to insert record into ai_testcase_generate_record table")
            else:
                logger.info(f"Successfully inserted record: {result['TestCaseID']}")
        
        if "Attachments" in result:
            for att in result["Attachments"]:
                att_id = att["attachment_id"]
                existing_att = DB.select(table='ai_testcase_generate_attachments', columns=['attachment_id','test_case_id','download_url','create_time','update_time'],where={"attachment_id": att_id})
                if not existing_att:
                    att_data = {
                        "attachment_id": att_id,
                        "test_case_id": result["TestCaseID"],
                        "download_url": att["download_url"],
                        "create_time": datetime.now(),
                        "update_time": datetime.now()
                    }
                    DB.insert("ai_testcase_generate_attachments", att_data)
    except Exception as db_error:
        logger.error(f"Database insertion error: {db_error}")
@router.post("/generate", response_model=GenerateResponse)
async def generate(
        file: UploadFile = File(..., description="原始测试集文件"),
        enable_generalization: bool = Form(True, description="是否开启泛化"),
        enable_adversarial: bool = Form(False, description="是否开启对抗攻击")
):
    """
    处理数据集接口：执行测试集泛化与对抗生成。
    """

    temp_local_path = None
    try:
        # 1. 准备文件元数据
        timestamp = int(time.time() * 1000)
        date_str = datetime.now().strftime("%Y-%m-%d")
        original_filename = file.filename

        # 定义固定常量
        FILE_SOURCE = "tuoguan1"
        SKILL_DESCRIPTION = "ai_testcase_generator"
        FILE_PATH_IDENTIFIER = f"{date_str}_{timestamp}"  # 对应 DB 的 file_path 列
        USER_ID = "IT703434"
        USER_NAME = "梁金伟"

        # 构造 COS 存储路径
        # 格式: tuoguan1/ai_testcase_generator/YYYY-MM-DD_TIMESTAMP/filename
        cos_path = f"{FILE_SOURCE}/{SKILL_DESCRIPTION}/{FILE_PATH_IDENTIFIER}/{original_filename}"

        # 2. 保存上传文件到本地临时目录
        temp_dir = process_service.TEMP_DIR
        os.makedirs(temp_dir, exist_ok=True)
        temp_local_path = os.path.join(temp_dir, f"upload_{timestamp}_{original_filename}")

        with open(temp_local_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        logger.info(f"File saved locally to {temp_local_path}")

        # 3. 上传到 COS (ObjectStorage 会处理 DB 记录和 ID 生成)
        file_id = await asyncio.to_thread(
            cos_service.upload_file,
            temp_local_path,
            cos_path,
            USER_ID,
            USER_NAME
        )

        logger.info(f"Original file uploaded. ID: {file_id}")

        # 4. 调用处理服务
        result = await process_service.process_dataset(
            cos_path=cos_path,
            file_id=file_id,
            file_path_identifier=FILE_PATH_IDENTIFIER,  # 传递路径标识，方便后续中间文件使用同一目录
            enable_generalization=enable_generalization,
            enable_adversarial=enable_adversarial
        )

        # 5. 记录处理结果到数据库
        _record_generation_result(result)

        return result

    except Exception as e:
        logger.error(f"Processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # 清理上传的临时文件
        if temp_local_path and os.path.exists(temp_local_path):
            try:
                os.remove(temp_local_path)
            except OSError:
                pass

@router.post("/generate_attachments", response_model=GenerateResponse)
async def generate_attachments(
        business_process: str = Form(...,
                                     description="业务流程 (如'存款协议'、'缴款通知书'、'标的合同'等)"),
        jktzs_file: UploadFile = File(None, description="测试集.xlsx文件上传 (缴款通知书/标的合同等)"),
        jktzs_template: UploadFile = File(None, description="模板.docx文件上传 (缴款通知书/标的合同等)"),
        file_count: Optional[int] = Form(1, ge=0, description="需要生成的指令附件pdf的数量"),
        enable_generalization: bool = Form(False, description="泛化开关"),
        enable_adversarial: bool = Form(False, description="对抗生成开关"),
        enable_comparison: bool = Form(True, description="是否开启自动比对评测")
):
    """
    指令附件生成接口：
    1. 支持原有的存款协议生成(business_process非 缴款通知书/标的合同)
    2. 支持基于模板的生成(business_process为 缴款通知书/标的合同)
    """
    timestamp = int(time.time() * 1000)
    date_str = datetime.now().strftime("%Y-%m-%d")
    FILE_PATH_IDENTIFIER = f"{date_str}_{timestamp}"

    # === 分发业务处理逻辑 ===
    # 1. 存款协议逻辑
    if business_process not in ["缴款通知书", "标的合同"]:
        if file_count <= 0:
            raise HTTPException(status_code=400, detail="存款协议生成需要指定文件数量大于0")
        try:
            result = await process_service.process_ckxy(
                business_process=business_process,
                count=file_count,
                file_path_identifier=FILE_PATH_IDENTIFIER,
                enable_comparison=enable_comparison
            )
            # === 结果落库 ===
            # 抽取公共落库逻辑，统一插入 ai_testcase_generate_record 和 ai_testcase_generate_attachments 表
            _record_generation_result(result)

            return result

        except Exception as e:
            logger.error(f"CKXY Processing failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    # 2. 基于模板的文档生成逻辑 (缴款通知书/标的合同等)
    if not jktzs_file or not jktzs_template:
        raise HTTPException(status_code=400, detail="生成该类型文档需要上传测试集和模板文件")
    if file_count <= 0:
        raise HTTPException(status_code=400, detail="需要生成的文件数量必须大于0")

    temp_jktzs_file_path = None
    temp_jktzs_template_path = None
    try:
        temp_dir = process_service.TEMP_DIR
        os.makedirs(temp_dir, exist_ok=True)
        
        # 保存上传的文件
        temp_jktzs_file_path = os.path.join(temp_dir, f"upload_{timestamp}_{jktzs_file.filename}")
        with open(temp_jktzs_file_path, "wb") as buffer:
            shutil.copyfileobj(jktzs_file.file, buffer)

        temp_jktzs_template_path = os.path.join(temp_dir, f"upload_{timestamp}_{jktzs_template.filename}")
        with open(temp_jktzs_template_path, "wb") as buffer:
            shutil.copyfileobj(jktzs_template.file, buffer)

        # 调用 Service 层执行具体的 PDF 渲染、合并单元格及 COS 上传逻辑
        result = await process_service.process_jktzs_attachment(
            business_process=business_process,
            jktzs_file_path=temp_jktzs_file_path,
            jktzs_template_path=temp_jktzs_template_path,
            file_count=file_count,
            enable_generalization=enable_generalization,
            enable_adversarial=enable_adversarial,
            file_path_identifier=FILE_PATH_IDENTIFIER,
            timestamp=timestamp,
            enable_comparison=enable_comparison
        )
        
        # 为了兼容统一落库逻辑，提取所需变量
        attachments = result.get("Attachments", [])
        test_case_id_batch = result.get("test_case_id_batch", "")

        # === 结果落库 ===
        # 抽取公共落库逻辑，统一插入 ai_testcase_generate_record 和 ai_testcase_generate_attachments 表
        _record_generation_result(result)

        return result

    except Exception as e:
        logger.error(f"JKTZS Processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # 清理临时文件
        for path in [temp_jktzs_file_path, temp_jktzs_template_path]:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass

@router.get("/download_files")
async def download_files(
    test_case_id: str = Query(..., description="测试用例ID（案例集ID）"),
    file_type: Optional[str] = Query(None, description="文件类型（用于命名）"),
    file_sub_type: Optional[str] = Query(None, description="文件子类型（用于命名）")
):
    """
    流式下载文件接口（支持PDF、XLSX等多种格式）

    功能：
    - 如果只有1个文件，直接下载该文件
    - 如果有多个文件，打包成ZIP后下载

    命名规则：
    - 单个文件: {test_case_id}.扩展名（根据实际文件类型）
    - 多个文件: {test_case_id}_{file_type}_{file_sub_type}_{数量}.zip

    流程：
    1. 从数据库查询test_case_id对应的所有附件
    2. 从COS下载文件到临时目录
    3. 根据数量决定返回方式（单个文件或ZIP）
    4. 返回文件流给前端
    5. 清理临时文件
    """
    try:
        logger.info(f"Download request received for test_case_id: {test_case_id}")

        # 调用服务层获取文件流
        file_stream, filename, is_zip = await process_service.download_files_as_stream(
            test_case_id=test_case_id,
            file_type=file_type,
            file_sub_type=file_sub_type
        )

        # 根据文件类型设置媒体类型
        if is_zip:
            media_type = "application/zip"
        elif filename.endswith('.xlsx'):
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        elif filename.endswith('.pdf'):
            media_type = "application/pdf"
        else:
            media_type = "application/octet-stream"

        # 返回流式响应
        def iterfile():
            file_stream.seek(0)
            while True:
                chunk = file_stream.read(65536)
                if not chunk:
                    break
                yield chunk

        # 对文件名进行URL编码，支持中文文件名
        encoded_filename = quote(filename, safe='')
        headers = {
            # 使用 filename*= 语法支持UTF-8编码的文件名（RFC 5987）
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}",
            "Access-Control-Expose-Headers": "Content-Disposition"
        }

        logger.info(f"Returning file: {filename}, type: {'ZIP' if is_zip else 'FILE'}")

        return StreamingResponse(
            iterfile(),
            media_type=media_type,
            headers=headers
        )

    except ValueError as ve:
        logger.error(f"Download failed - {str(ve)}")
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        logger.error(f"Download failed for test_case_id {test_case_id}: {e}")
        raise HTTPException(status_code=500, detail=f"下载失败: {str(e)}")


@router.get("/ocr_status")
async def check_ocr_status():
    """
    前端查询接口：检查解析小助(OCR)服务是否已开启。
    """
    try:
        is_enabled = await process_service.check_ocr_status()
        return {"code": 200, "message": "success", "data": {"ocr_enabled": is_enabled}}
    except Exception as e:
        logger.error(f"Failed to query OCR status: {e}")
        raise HTTPException(status_code=500, detail=f"查询OCR状态失败: {str(e)}")

@router.get("/generation_history")
async def get_generation_history(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量")
):
    """
    前端查询接口：获取历史生成批次列表（支持分页）。
    """
    try:
        from app.common.db.db_utils import DBUtils
        db = DBUtils()

        # 计算分页偏移量
        offset = (page - 1) * page_size

        # 查询总数
        count_sql = "SELECT COUNT(*) as total FROM ai_testcase_generate_record"
        total_rows = db.execute_query(count_sql)
        total = total_rows[0]['total'] if total_rows else 0

        # 查询数据
        query_sql = """
            SELECT
                test_case_id, status, message, create_time, update_time, is_comparison_done
            FROM ai_testcase_generate_record
            ORDER BY create_time DESC
            LIMIT %s OFFSET %s
        """
        rows = db.execute_query(query_sql, (page_size, offset))

        result_data = []
        for row in rows:
            result_data.append({
                "test_case_id": row.get("test_case_id"),
                "status": row.get("status"),
                "message": row.get("message"),
                "create_time": row.get("create_time").strftime("%Y-%m-%d %H:%M:%S") if row.get("create_time") else None,
                "update_time": row.get("update_time").strftime("%Y-%m-%d %H:%M:%S") if row.get("update_time") else None,
                "is_comparison_done": bool(row.get("is_comparison_done"))
            })

        return {
            "code": 200,
            "message": "success",
            "data": {
                "total": total,
                "page": page,
                "page_size": page_size,
                "records": result_data
            }
        }

    except Exception as e:
        logger.error(f"Failed to query generation history: {e}")
        raise HTTPException(status_code=500, detail=f"查询生成历史失败: {str(e)}")


@router.get("/generation_result")
async def get_generation_result(test_case_id: str = Query(..., description="测试集生成的批次ID")):
    """
    前端查询接口：根据 test_case_id 查询单次生成的详情，包含生成的附件列表。
    """
    try:
        from app.common.db.db_utils import DBUtils
        db = DBUtils()

        # 查询主记录
        record_rows = db.select(
            table='ai_testcase_generate_record',
            columns=['test_case_id', 'status', 'message', 'create_time', 'update_time', 'is_comparison_done'],
            where={'test_case_id': test_case_id}
        )
        if not record_rows:
            return {"code": 404, "message": "未找到对应的生成记录", "data": None}
        
        record = record_rows[0]
        result_data = {
            "test_case_id": record.get("test_case_id"),
            "status": record.get("status"),
            "message": record.get("message"),
            "create_time": record.get("create_time").strftime("%Y-%m-%d %H:%M:%S") if record.get("create_time") else None,
            "update_time": record.get("update_time").strftime("%Y-%m-%d %H:%M:%S") if record.get("update_time") else None,
            "is_comparison_done": bool(record.get("is_comparison_done")),
            "attachments": []
        }

        # 查询附件列表
        attachments = db.select(
            table='ai_testcase_generate_attachments',
            columns=['attachment_id', 'download_url', 'create_time'],
            where={'test_case_id': test_case_id}
        )
        
        for att in attachments:
            result_data["attachments"].append({
                "attachment_id": att.get("attachment_id"),
                "download_url": att.get("download_url"),
                "create_time": att.get("create_time").strftime("%Y-%m-%d %H:%M:%S") if att.get("create_time") else None
            })

        return {"code": 200, "message": "success", "data": result_data}

    except Exception as e:
        logger.error(f"Failed to query generation result for {test_case_id}: {e}")
        raise HTTPException(status_code=500, detail=f"查询生成详情失败: {str(e)}")


@router.get("/comparison_result")
async def get_comparison_result(test_case_id: str = Query(..., description="测试集生成的批次ID")):
    """
    前端查询接口：根据 test_case_id 查询 comparison_info 表里的比对结果详情。
    返回标准的 JSON 格式数据供前端渲染。
    """
    try:
        from app.common.db.db_utils import DBUtils
        db = DBUtils()

        # 按照文件类型、子类型、要素字段进行排序，保证前端展示的顺序稳定
        query_sql = """
            SELECT 
                file_type, file_sub_type, element_key, element_name,
                comparison_count, correct_count, correct_percentage, 
                mistake_count, unclear_count, pass_or_not
            FROM comparison_info
            WHERE test_case_id = %s
            ORDER BY file_type, file_sub_type, element_key
        """
        rows = db.execute_query(query_sql, (test_case_id,))

        if not rows:
            return {"code": 200, "message": "暂无比对结果或比对正在进行中", "data": []}

        result_data = []
        for row in rows:
            print(row)
            result_data.append({
                "file_type": row["file_type"],
                "file_sub_type": row["file_sub_type"],
                "element_key": row["element_key"],
                "element_name": row["element_name"],
                "comparison_count": row["comparison_count"],
                "correct_count": row["correct_count"],
                "correct_percentage": row["correct_percentage"],
                "mistake_count": row["mistake_count"],
                "unclear_count": row["unclear_count"],
                "pass_or_not": row["pass_or_not"]
            })

        return {"code": 200, "message": "success", "data": result_data}

    except Exception as e:
        logger.error(f"Failed to query comparison result for {test_case_id}: {e}")
        raise HTTPException(status_code=500, detail=f"查询比对结果失败: {str(e)}")