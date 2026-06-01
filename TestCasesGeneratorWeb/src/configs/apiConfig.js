/**
 * 统一接口配置管理
 * 收拢所有后端接口配置，便于统一管理和维护
 */

// 环境配置
const ENV_CONFIG = {
  development: {
    API_BASE_URL: '/api',  // 开发环境使用相对路径，通过代理转发
    AI_QA_BASE_URL: '/api' // 开发环境使用相对路径，通过代理转发
  },
  production: {
    API_BASE_URL: '/api',
    AI_QA_BASE_URL: '/api'
  },
  test: {
    API_BASE_URL: '/api',
    AI_QA_BASE_URL: '/api'
  }
};

// 获取当前环境
const getCurrentEnv = () => {
  return process.env.NODE_ENV || 'development';
};
// 获取环境配置
const getEnvConfig = () => {
  const env = getCurrentEnv();
  return ENV_CONFIG[env] || ENV_CONFIG.development;
};

// 接口端点配置
const API_ENDPOINTS = {
    //智能测试集泛化与附件生成工具
  AI_TESTCASE_GENERATOR: {
    GENERALIZE_TESTCASES: '/ai_testcase_generator/generate',
    GENERATE_ATTACHMENTS: '/ai_testcase_generator/generate_attachments',
    DOWNLOAD_ATTACHMENTS: '/ai_testcase_generator/download_files',
    GET_OCR_STATUS: '/ai_testcase_generator/ocr_status',
    GET_COMPARISON_RESULTS: '/ai_testcase_generator/comparison_result',
    GET_GENERATION_HISTORY: '/ai_testcase_generator/generation_history',
    GET_GENERATION_RESULT: '/ai_testcase_generator/generation_result',
    GET_COMPARISON_FIELDS: '/ai_testcase_generator/comparison_fields'
  }
};

// 获取当前环境配置
const currentEnvConfig = getEnvConfig();

// 统一接口配置
const API_CONFIG = {
  // 基础URL配置
  BASE_URLS: {
    MAIN: currentEnvConfig.API_BASE_URL,
    AI_QA: currentEnvConfig.AI_QA_BASE_URL
  },

  // 接口端点
  ENDPOINTS: API_ENDPOINTS,

  // 请求超时配置（毫秒）- 调整为10分钟匹配nginx配置
  TIMEOUT: {
    DEFAULT: 600000,  // 10分钟
    UPLOAD: 1200000,  // 20分钟
    DOWNLOAD: 1200000 // 20分钟
  },

  // 重试配置
  RETRY: {
    MAX_RETRIES: 3,
    RETRY_DELAY: 1000
  },

  // 文件上传配置
  UPLOAD: {
    MAX_FILE_SIZE: 50 * 1024 * 1024, // 50MB
    SUPPORTED_TYPES: {
      DOCUMENT: ['.docx'],
      MARKDOWN: ['.md', '.markdown'],
      EXCEL: ['.xlsx']
    }
  }
};

/**
 * 构建完整的API URL
 * @param {string} baseUrlKey - 基础URL的键名 (MAIN 或 AI_QA)
 * @param {string} endpoint - 接口端点
 * @returns {string} 完整的API URL
 */
export const buildApiUrl = (baseUrlKey, endpoint) => {
  const baseUrl = API_CONFIG.BASE_URLS[baseUrlKey];
  if (baseUrl === undefined || baseUrl === null) {
    throw new Error(`未知的基础URL键名: ${baseUrlKey}`);
  }
  return `${baseUrl}${endpoint}`;
};

/**
 * 获取接口配置
 * @param {string} serviceName - 服务名称
 * @param {string} endpointKey - 端点键名
 * @returns {Object} 接口配置信息
 */
export const getApiConfig = (serviceName, endpointKey) => {
  const endpoint = API_CONFIG.ENDPOINTS[serviceName]?.[endpointKey];
  if (!endpoint) {
    throw new Error(`未知的服务或端点: ${serviceName}.${endpointKey}`);
  }

  // 根据服务类型确定基础URL
  let baseUrlKey = 'MAIN';
  if (serviceName === 'AI_QA') {
    baseUrlKey = 'AI_QA';
  }

  return {
    url: buildApiUrl(baseUrlKey, endpoint),
    timeout: API_CONFIG.TIMEOUT.DEFAULT,
    baseUrlKey
  };
};

/**
 * 获取当前环境信息
 * @returns {string} 当前环境
 */
export const getCurrentEnvironment = () => {
  return getCurrentEnv();
};

/**
 * 获取上传配置
 * @param {string} fileType - 文件类型 (DOCUMENT, MARKDOWN, EXCEL)
 * @returns {Object} 上传配置
 */
export const getUploadConfig = (fileType = 'DOCUMENT') => {
  const config = {
    maxSize: API_CONFIG.UPLOAD.MAX_FILE_SIZE,
    supportedTypes: API_CONFIG.UPLOAD.SUPPORTED_TYPES[fileType] || API_CONFIG.UPLOAD.SUPPORTED_TYPES.DOCUMENT
  };

  return config;
};

/**
 * 验证文件类型是否支持
 * @param {File} file - 文件对象
 * @param {string} fileType - 文件类型 (DOCUMENT, MARKDOWN, EXCEL)
 * @returns {boolean} 是否支持
 */
export const validateFileType = (file, fileType = 'DOCUMENT') => {
  const config = getUploadConfig(fileType);
  const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
  return config.supportedTypes.includes(fileExtension);
};

/**
 * 验证文件大小是否在限制内
 * @param {File} file - 文件对象
 * @returns {boolean} 是否在限制内
 */
export const validateFileSize = (file) => {
  return file.size <= API_CONFIG.UPLOAD.MAX_FILE_SIZE;
};

export default API_CONFIG;