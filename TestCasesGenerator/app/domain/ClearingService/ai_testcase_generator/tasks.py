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
    test_case_id_batch: str = None
):
    """
    异步任务：大批量处理指令附件的生成
    """
    logger.info(f"Task started: generate_attachments_task, business_process={business_process}")
    
    async def _run_process():
        process_service = ProcessService()
        try:
            # 1. 核心生成逻辑
            result = await process_service.process_jktzs_attachment(
                business_process=business_process,
                jktzs_file_path=jktzs_file_path,
                jktzs_template_path=jktzs_template_path,
                file_count=file_count,
                enable_generalization=enable_generalization,
                enable_adversarial=enable_adversarial,
                file_path_identifier=file_path_identifier,
                timestamp=timestamp,
                enable_comparison=enable_comparison,
                test_case_id_batch=test_case_id_batch
            )
            
            # 2. 结果落库
            _record_generation_result(result)
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
