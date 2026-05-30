/**
 * AiTestCaseGeneratorService.js
 * 
 * 逻辑层服务，用于处理“智审核测试集泛化生成”前端页面的业务逻辑与后端接口交互。
 * 主要职责：
 * 1. 封装后端接口请求（例如生成附件、获取生成历史等）。
 * 2. 处理业务状态和数据转换。
 * 3. 将 UI 组件与具体业务逻辑解耦，提高代码可维护性。
 */

import unifiedApiService from './unifiedApiService';
import API_CONFIG from '../configs/apiConfig';

export const AiTestCaseGeneratorService = {
  /**
   * 调用后端接口生成测试附件 (指令附件生成)
   * 
   * @param {Object} params - 请求参数
   * @param {string} params.business_process - 业务流程，如"缴款通知书"
   * @param {File} [params.upload_file] - 测试集 Excel 文件 (当为缴款通知书时传 jktzs_file)
   * @param {File} [params.template_file] - 模板 Word 文件 (当为缴款通知书时传 jktzs_template)
   * @param {number} params.file_count - 生成的文件数量
   * @param {boolean} params.enable_generalization - 是否开启泛化
   * @param {boolean} params.enable_adversarial - 是否开启对抗生成
   * @param {boolean} params.enable_comparison - 是否开启比对评测
   * @returns {Promise<Object>} 后端返回的生成结果
   */
  generateAttachments: async (params) => {
    const formData = new FormData();
    
    // 必填参数
    formData.append('business_process', params.business_process);
    
    if (params.file_count !== undefined) {
      formData.append('file_count', params.file_count);
    }
    
    if (params.enable_generalization !== undefined) {
      formData.append('enable_generalization', params.enable_generalization);
    }
    
    if (params.enable_adversarial !== undefined) {
      formData.append('enable_adversarial', params.enable_adversarial);
    }
    
    if (params.enable_comparison !== undefined) {
      formData.append('enable_comparison', params.enable_comparison);
    }

    // 条件必填参数：需要模板的流程需要测试集文件和模板文件
    if (['缴款通知书', '标的合同'].includes(params.business_process)) {
      if (params.upload_file) {
        formData.append('jktzs_file', params.upload_file);
      }
      if (params.template_file) {
        formData.append('jktzs_template', params.template_file);
      }
    }

    try {
      const response = await unifiedApiService.upload(
        'AI_TESTCASE_GENERATOR',
        'GENERATE_ATTACHMENTS',
        formData,
        null, // onProgress
        { timeout: API_CONFIG.TIMEOUT.UPLOAD } // config 覆盖默认 timeout
      );
      return response.data;
    } catch (error) {
      console.error('generateAttachments API Error:', error);
      throw new Error(error.response?.data?.detail || error.message || '接口请求失败');
    }
  },

  /**
   * 调用后端接口进行测试集泛化
   * 
   * @param {Object} params - 请求参数
   * @param {File} params.file - 原始测试集 Excel 文件
   * @param {boolean} params.enable_generalization - 是否开启数据泛化
   * @param {boolean} params.enable_adversarial - 是否开启对抗攻击
   * @returns {Promise<Object>} 后端返回的生成结果
   */
  generate: async (params) => {
    const formData = new FormData();
    
    formData.append('file', params.file);
    
    if (params.enable_generalization !== undefined) {
      formData.append('enable_generalization', params.enable_generalization);
    }
    
    if (params.enable_adversarial !== undefined) {
      formData.append('enable_adversarial', params.enable_adversarial);
    }

    try {
      const response = await unifiedApiService.upload(
        'AI_TESTCASE_GENERATOR',
        'GENERALIZE_TESTCASES',
        formData,
        null, // onProgress
        { timeout: API_CONFIG.TIMEOUT.UPLOAD } // config 覆盖默认 timeout
      );
      return response.data;
    } catch (error) {
      console.error('generate API Error:', error);
      throw new Error(error.response?.data?.detail || error.message || '接口请求失败');
    }
  },

  /**
   * 调用后端接口查询比对评测结果
   * 
   * @param {string} test_case_id - 测试集生成的批次 ID
   * @returns {Promise<Object>} 后端返回的比对结果
   */
  getComparisonResult: async (test_case_id) => {
    try {
      const response = await unifiedApiService.get(
        'AI_TESTCASE_GENERATOR',
        'GET_COMPARISON_RESULTS',
        { test_case_id }
      );
      return response.data;
    } catch (error) {
      console.error('getComparisonResult API Error:', error);
      throw new Error(error.response?.data?.detail || error.message || '接口请求失败');
    }
  },

  /**
   * 调用后端接口获取历史生成批次列表（分页）
   * 
   * @param {Object} params - 请求参数
   * @param {number} params.page - 页码
   * @param {number} params.page_size - 每页数量
   * @returns {Promise<Object>} 后端返回的生成历史列表
   */
  getGenerationHistory: async (params = { page: 1, page_size: 20 }) => {
    try {
      const response = await unifiedApiService.get(
        'AI_TESTCASE_GENERATOR',
        'GET_GENERATION_HISTORY',
        params
      );
      return response; // 注意这里直接返回 response，因为业务代码里是通过 response.data.records 获取的
    } catch (error) {
      console.error('getGenerationHistory API Error:', error);
      throw new Error(error.response?.data?.detail || error.message || '获取历史记录失败');
    }
  },

  /**
   * 调用后端接口查询单次生成的详情
   * 
   * @param {string} test_case_id - 测试集生成的批次 ID
   * @returns {Promise<Object>} 后端返回的生成详情
   */
  getGenerationResult: async (test_case_id) => {
    try {
      const response = await unifiedApiService.get(
        'AI_TESTCASE_GENERATOR',
        'GET_GENERATION_RESULT',
        { test_case_id }
      );
      return response; // 同样返回外层结构
    } catch (error) {
      console.error('getGenerationResult API Error:', error);
      throw new Error(error.response?.data?.detail || error.message || '获取生成详情失败');
    }
  },

  /**
   * 调用后端接口查询 OCR 服务状态
   * 
   * @returns {Promise<Object>} 返回 OCR 服务状态信息
   */
  getOcrStatus: async () => {
    try {
      const response = await unifiedApiService.get(
        'AI_TESTCASE_GENERATOR',
        'GET_OCR_STATUS'
      );
      return response;
    } catch (error) {
      console.error('getOcrStatus API Error:', error);
      throw new Error(error.response?.data?.detail || error.message || '获取OCR服务状态失败');
    }
  },

  /**
   * 下载附件 - 调用DOWNLOAD_ATTACHMENTS接口
   *
   * @param {Object} params - 请求参数
   * @param {string} params.test_case_id - 测试集ID
   * @param {string} params.file_type - 文件类型
   * @param {string} params.file_sub_type - 文件子类型
   * @returns {Promise<Blob>} 返回二进制文件流
   */
  downloadAttachments: async (params) => {
    try {
      console.log('发送附件下载请求到: AI_TESTCASE_GENERATOR.DOWNLOAD_ATTACHMENTS');
      console.log('下载参数:', params);

      // 使用统一的API服务，设置responseType为blob
      const response = await unifiedApiService.get(
        'AI_TESTCASE_GENERATOR',
        'DOWNLOAD_ATTACHMENTS',
        {
          test_case_id: params.test_case_id,
          file_type: params.file_type,
          file_sub_type: params.file_sub_type
        },
        {}, // pathParams
        {
          responseType: 'blob', // 重要：设置响应类型为blob
          timeout: API_CONFIG.TIMEOUT.DOWNLOAD
        }
      );
      
      // 尝试从 header 中提取文件名
      let filename = null;
      const contentDisposition = response.headers && response.headers['content-disposition'];
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename\*=UTF-8''([^;]+)/i) || 
                              contentDisposition.match(/filename="?([^";]+)"?/i);
        if (filenameMatch && filenameMatch[1]) {
          filename = decodeURIComponent(filenameMatch[1]);
        }
      }
      
      return { blob: response.data, filename };
    } catch (error) {
      console.error('downloadAttachments API Error:', error);
      throw new Error(error.response?.data?.detail || error.message || '接口请求失败');
    }
  },

  /**
   * 下载文件辅助方法
   * @param {string} url - 文件的下载链接
   */
  downloadFile: (url) => {
    if (!url) return;
    const link = document.createElement('a');
    link.href = url;
    // 从 URL 中提取文件名
    link.download = url.split('/').pop() || 'download';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }
};

export default AiTestCaseGeneratorService;
