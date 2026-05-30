/**
 * 统一API服务
 * 统一管理所有API请求，确保Authorization字段的一致性
 */
import axios from 'axios';
import { message } from 'antd';
import { getApiConfig, buildApiUrl } from '../configs/apiConfig';

// Mock auth utilities since they are missing
const getToken = () => null;
const handleNotLogin = () => {};
const setToken = () => {};
const isTokenExpired = () => false;

// Mock tracking service since it's missing
const trackingService = {
  track: async () => {},
  autoTrack: () => {}
};

// 创建统一的axios实例
const unifiedService = axios.create({
  timeout: 10000,
  withCredentials: true
});

// 请求拦截器 - 统一添加Authorization头
unifiedService.interceptors.request.use(
  async (config) => {
    const token = getToken();
    
    // 统一使用标准的Authorization头
    if (token && config.headers) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }

    // 添加缓存控制头，防止304问题
    if (config.headers) {
      config.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate';
      config.headers['Pragma'] = 'no-cache';
      config.headers['Expires'] = '0';
    }

    // 检查token是否过期
    if (token && isTokenExpired()) {
      message.warning('登录已过期，请重新登录');
      handleNotLogin();
      return Promise.reject(new Error('Token expired'));
    }

    // 自动追踪用户行为（基于路由匹配的装饰器模式）
    // 如果配置了手动追踪，优先使用手动配置
    if (config.meta?.track === true) {
      // 使用微任务异步处理追踪，避免阻塞主请求
      Promise.resolve().then(() => {
        trackingService.track(config, config.meta).catch(error => {
          console.warn('用户行为追踪处理失败:', error);
        });
      });
    } else {
      // 使用自动追踪（装饰器模式）
      trackingService.autoTrack(config, config.meta);
    }

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
unifiedService.interceptors.response.use(
  (response) => {
    // 检查响应头中是否有新的token
    if (response?.headers?.['x-auth-token']) {
      setToken(response.headers['x-auth-token']);
    }
    
    // 处理标准Authorization响应头（如果后端返回）
    if (response?.headers?.['authorization']){
      const authHeader = response.headers['authorization'];
      if (authHeader.startsWith('Bearer ')) {
        const newToken = authHeader.substring(7); // 去掉'Bearer '前缀
        setToken(newToken);
      }
    }

    return response;
  },
  (error) => {
    if (error.response) {
      const status = error.response.status;
      const errorMessage = error.response.data?.message || '请求失败';

      // 401未授权处理
      if (status === 401) {
        message.error('未授权，请重新登录');
        handleNotLogin();
        return Promise.reject(error);
      }

      // 403禁止访问
      if (status === 403) {
        message.error('权限不足，无法访问该资源');
        return Promise.reject(error);
      }

      // 其他错误显示错误信息
      message.error(`请求失败 (${status}): ${errorMessage}`);
    } else {
      // 网络错误等情况
      message.error(`网络错误: ${error.message || '请检查网络连接'}`);
    }
    return Promise.reject(error);
  }
);

/**
 * 使用配置的服务和端点进行GET请求
 * @param {string} serviceType - 服务类型
 * @param {string} endpointKey - 端点键名
 * @param {Object} params - 查询参数
 * @param {Object} pathParams - 路径参数
 * @returns {Promise} 请求响应
 */
export const unifiedGet = async (serviceType, endpointKey, params = {}, pathParams = {}, config={}) => {
  try {
    const apiConfig = getApiConfig(serviceType, endpointKey);
    
    // 构建完整的URL，处理路径参数
    let url = apiConfig.url;
    if (pathParams && Object.keys(pathParams).length > 0) {
      for (const [key, value] of Object.entries(pathParams)) {
        url = url.replace(`{${key}}`, value);
      }
    }
    
    console.log(`统一GET请求: ${url}`);
    
    const getConfig = {
      params: params,
      ...config
    };
    
    const response = await unifiedService.get(url, getConfig);
    return response;
  } catch (error) {
    console.error(`统一GET请求失败:`, error);
    throw error;
  }
};

/**
 * 使用配置的服务和端点进行POST请求
 * @param {string} serviceType - 服务类型
 * @param {string} endpointKey - 端点键名
 * @param {Object} data - 请求数据
 * @param {Object} config - 额外配置
 * @returns {Promise} 请求响应
 */
export const unifiedPost = async (serviceType, endpointKey, data = {}, config = {}) => {
  try {
    const apiConfig = getApiConfig(serviceType, endpointKey);
    console.log(`统一POST请求: ${apiConfig.url}`);
    
    const response = await unifiedService.post(apiConfig.url, data, config);
    return response;
  } catch (error) {
    console.error(`统一POST请求失败:`, error);
    throw error;
  }
};

/**
 * 使用配置的服务和端点进行文件上传
 * @param {string} serviceType - 服务类型
 * @param {string} endpointKey - 端点键名
 * @param {FormData} formData - 表单数据
 * @param {Function} onProgress - 进度回调函数
 * @param {Object} config - 额外配置
 * @returns {Promise} 上传响应
 */
export const unifiedUpload = async (serviceType, endpointKey, formData, onProgress = null, config = {}) => {
  const uploadConfig = {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress: (progressEvent) => {
      if (onProgress && progressEvent.total) {
        const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        onProgress(progress);
      }
    },
    ...config // 合并额外的配置
  };

  try {
    const apiConfig = getApiConfig(serviceType, endpointKey);
    let url = apiConfig.url;

    // 从 config 中提取 queryParams
    const { pathParams = {} } = config;

    // 添加查询参数
    if (Object.keys(pathParams).length > 0) {
      const searchParams = new URLSearchParams(pathParams);
      url += `?${searchParams.toString()}`;
    }
    console.log(`统一文件上传: ${url}`);
    const response = await unifiedService.post(url, formData, uploadConfig);
    return response;
  } catch (error) {
    console.error(`统一文件上传失败:`, error);
    throw error;
  }
};

/**
 * 使用配置的服务和端点进行PUT请求
 * @param {string} serviceType - 服务类型
 * @param {string} endpointKey - 端点键名
 * @param {Object} data - 请求数据
 * @param {Object} config - 额外配置
 * @returns {Promise} 请求响应
 */
export const unifiedPut = async (serviceType, endpointKey, data = {}, config = {}) => {
  try {
    const apiConfig = getApiConfig(serviceType, endpointKey);
    console.log(`统一PUT请求: ${apiConfig.url}`);

    const response = await unifiedService.put(apiConfig.url, data, config);
    return response;
  } catch (error) {
    console.error(`统一PUT请求失败:`, error);
    throw error;
  }
};

/**
 * 使用配置的服务和端点进行DELETE请求
 * @param {string} serviceType - 服务类型
 * @param {string} endpointKey - 端点键名
 * @param {Object} config - 额外配置
 * @returns {Promise} 请求响应
 */
export const unifiedDelete = async (serviceType, endpointKey, config = {}) => {
  try {
    const apiConfig = getApiConfig(serviceType, endpointKey);
    console.log(`统一DELETE请求: ${apiConfig.url}`);

    const response = await unifiedService.delete(apiConfig.url, config);
    return response;
  } catch (error) {
    console.error(`统一DELETE请求失败:`, error);
    throw error;
  }
};

/**
 * 直接使用URL进行请求（适用于不需要配置的特殊情况）
 * @param {string} url - 完整的URL
 * @param {Object} config - 额外请求配置
 * @returns {Promise} 请求响应
 */
export const unifiedRequest = async (url, config = {}) => {
  try {
    console.log(`统一直接请求: ${url}`);
    const requestConfig = {
      url,
      ...config // 支持传入额外配置
    };
    
    const response = await unifiedService(requestConfig);
    return response;
  } catch (error) {
    console.error(`统一直接请求失败:`, error);
    throw error;
  }
};

// 导出统一的API服务实例
const unifiedApiService = {
  get: unifiedGet,
  post: unifiedPost,
  put: unifiedPut,
  delete: unifiedDelete,
  upload: unifiedUpload,
  request: unifiedRequest,
  // 导出原始的axios实例供特殊需求使用
  instance: unifiedService
};

export default unifiedApiService;