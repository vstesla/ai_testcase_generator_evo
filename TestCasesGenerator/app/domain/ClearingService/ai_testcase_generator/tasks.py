import asyncio
import logging
import traceback
from app.core.celery_app import celery_app
from app.domain.ClearingService.ai_testcase_generator.process_service import ProcessService
from app.domain.ClearingService.ai_testcase_generator.api import _record_generation_result

logger = logging.getLogger(__name__)

@celery_app.task(bind=True)
def generate_attachments_task(
    self, 
    business_process: str, 
    jktzs_file_path: str, 
    jktzs_template_path: str, 
    file_count: int,
    enable_generalization: bool, 
    enable_adversarial: bool, 
    file_path_identifier: str, 
    timestamp: int, 
    enable_comparison: bool,
    test_case_id_batch: str = None,
    selected_comparison_fields: str = None
):
    """
    异步任务：大批量处理指令附件的生成
    """
    logger.info(f"Task started: generate_attachments_task, business_process={business_process}")
    
    async def _run_process():
        process_service = ProcessService()
        try:
            # 1. 核心生成逻辑
            result = await process_service.process_file_attachment(
                business_process=business_process,
                jktzs_file_path=jktzs_file_path,
                jktzs_template_path=jktzs_template_path,
                file_count=file_count,
                enable_generalization=enable_generalization,
                enable_adversarial=enable_adversarial,
                file_path_identifier=file_path_identifier,
                timestamp=timestamp,
                enable_comparison=enable_comparison,
                test_case_id_batch=test_case_id_batch,
                defer_comparison_task=True,
                selected_comparison_fields=selected_comparison_fields
            )
            
            # 2. 结果落库
            _record_generation_result(result)

            # 3. 生成完成后，单独分发比通任务，避免 Celery 当前事件循环关闭导致 create_task 丢失
            if enable_comparison and result.get("TestCaseGenStatus") == "Y" and result.get("generated_file_info"):
                compare_attachments_task.delay(
                    test_case_id=result["TestCaseID"],
                    generated_file_info=result["generated_file_info"],
                    business_process=business_process,
                    selected_comparison_fields=selected_comparison_fields
                )
            return result
            
        except Exception as e:
            logger.error(f"Error in Celery Task: {e}")
            logger.error(traceback.format_exc())
            
            # 失败落库记录
            error_result = {
                "TestCaseID": test_case_id_batch if test_case_id_batch else f"TC_{timestamp}",
                "TestCaseGenStatus": "N",
                "Message": f"异步处理失败: {str(e)}",
            }
            _record_generation_result(error_result)
            return error_result

    # 运行协程
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(_run_process())
    finally:
        loop.close()
        # 清理在 API 接口中接收并保存的临时上传文件
        import os
        for path in [jktzs_file_path, jktzs_template_path]:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                    logger.info(f"Cleaned up temp file in Celery Task: {path}")
                except OSError as e:
                    logger.warning(f"Failed to clean up temp file {path}: {e}")


@celery_app.task(bind=True)
def compare_attachments_task(self, test_case_id: str, generated_file_info, business_process: str = None, selected_comparison_fields: str = None):
    """异步任务：处理解析与比对，完成后更新 comparison_info 与 is_comparison_done。"""

    async def _run_compare():
        process_service = ProcessService()
        await process_service._parse_and_evaluate(
            test_case_id=test_case_id, 
            generated_file_info=generated_file_info,
            business_process=business_process,
            selected_comparison_fields=selected_comparison_fields
        )
        return {"test_case_id": test_case_id, "is_comparison_done": True}

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(_run_compare())
    except Exception as e:
        logger.error(f"Error in compare Celery Task: {e}")
        logger.error(traceback.format_exc())
        return {"test_case_id": test_case_id, "is_comparison_done": False, "message": str(e)}
    finally:
        loop.close()
