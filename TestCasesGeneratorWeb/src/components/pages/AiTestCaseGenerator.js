import React, { useState, useMemo, useEffect } from 'react';
import { message, Upload, Button, Switch, Table, Input, Select, DatePicker, Space, InputNumber, Modal, Tooltip, Badge } from 'antd';
import { UploadOutlined, SearchOutlined, FilterOutlined, DownloadOutlined, EyeOutlined, SyncOutlined } from '@ant-design/icons';
import * as XLSX from 'xlsx';
import AiTestCaseGeneratorService from '../../services/AiTestCaseGeneratorService';

import './AiTestCaseGenerator.css';

// 日期工具函数 - 替代moment功能
const dateUtils = {
    // 格式化日期为 YYYY-MM-DD HH:mm:ss
    formatDate: (date, format = 'YYYY-MM-DD HH:mm:ss') => {
        if (!date || !(date instanceof Date) || isNaN(date.getTime())) {
            return '';
        }

        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        const hours = String(date.getHours()).padStart(2, '0');
        const minutes = String(date.getMinutes()).padStart(2, '0');
        const seconds = String(date.getSeconds()).padStart(2, '0');

        return format
            .replace('YYYY', year)
            .replace('MM', month)
            .replace('DD', day)
            .replace('HH', hours)
            .replace('mm', minutes)
            .replace('ss', seconds);
    },

    // 解析日期字符串（简化版本，只支持标准格式）
    parseDate: (dateString) => {
        if (!dateString) return null;

        // 尝试多种格式解析
        const date = new Date(dateString);
        if (!isNaN(date.getTime())) {
            return date;
        }

        // 尝试处理 YYYY-MM-DD HH:mm:ss 格式
        const isoString = dateString.replace(' ', 'T') + 'Z';
        const isoDate = new Date(isoString);
        if (!isNaN(isoDate.getTime())) {
            return isoDate;
        }

        return null;
    },

    // 获取当天的开始时间（00:00:00）
    startOfDay: (date = new Date()) => {
        const newDate = new Date(date);
        newDate.setHours(0, 0, 0, 0);
        return newDate;
    },

    // 添加天数
    addDays: (date, days) => {
        const newDate = new Date(date);
        newDate.setDate(newDate.getDate() + days);
        return newDate;
    },

    // 判断日期是否在范围内
    isBetween: (date, start, end, inclusivity = '[]') => {
        if (!(date instanceof Date) || !(start instanceof Date) || !(end instanceof Date)) {
            return false;
        }

        const time = date.getTime();
        const startTime = start.getTime();
        const endTime = end.getTime();

        switch (inclusivity) {
            case '()': return time > startTime && time < endTime;
            case '[)': return time >= startTime && time < endTime;
            case '(]': return time > startTime && time <= endTime;
            case '[]': return time >= startTime && time <= endTime;
            default: return time >= startTime && time <= endTime;
        }
    },

    // 检查是否为有效日期
    isValidDate: (date) => {
        return date instanceof Date && !isNaN(date.getTime());
    }
};

// 需要上传测试集和模板文件的业务流程
const REQUIRES_TEMPLATE_PROCESSES = ['缴款通知书', '标的合同'];

const MainPage = () => {
    // 业务参数状态
    const [functionType, setFunctionType] = useState('指令附件生成&比对'); // 新增：功能类型
    const [businessProcess, setBusinessProcess] = useState('缴款通知书');
    const [fileCount, setFileCount] = useState(1);
    const [generalizationEnabled, setGeneralizationEnabled] = useState(false);
    const [adversarialEnabled, setAdversarialEnabled] = useState(false);
    const [comparisonEnabled, setComparisonEnabled] = useState(true);

    // 文件上传状态
    const [fileList, setFileList] = useState([]);
    const [templateFileList, setTemplateFileList] = useState([]);

    // 处理文件上传
    const handleUpload = (info) => {
        let fileList = [...info.fileList];

        // 限制只能上传一个文件
        fileList = fileList.slice(-1);

        // 检查文件类型
        const isXlsx = fileList[0]?.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' ||
            fileList[0]?.name?.endsWith('.xlsx');

        if (fileList.length > 0 && !isXlsx) {
            message.error('请上传xlsx格式的文件');
            fileList = []; // 清空无效文件
        }

        setFileList(fileList);
    };

    // 处理模板文件上传
    const handleTemplateUpload = (info) => {
        let list = [...info.fileList].slice(-1);

        // 检查是否为 Word 文件 (.docx)
        const isDocx = list[0]?.type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' ||
            list[0]?.name?.endsWith('.docx');

        if (list.length > 0 && !isDocx) {
            message.error('请上传 .docx 格式的模板文件');
            list = [];
        }
        setTemplateFileList(list);
    };

    const [loading, setLoading] = useState(false);
    const [generatedResults, setGeneratedResults] = useState([]);
    const [historyLoading, setHistoryLoading] = useState(false);

    // 比对结果状态
    const [comparisonResults, setComparisonResults] = useState([]); // 原始比对结果数据
    const [comparisonSearchText, setComparisonSearchText] = useState('');
    const [comparisonStatusFilter, setComparisonStatusFilter] = useState('all');
    const [comparisonDateRange, setComparisonDateRange] = useState(null);

    // 详情弹窗状态
    const [detailModalVisible, setDetailModalVisible] = useState(false);
    const [currentDetailData, setCurrentDetailData] = useState([]); // 当前查看的详情数据
    const [currentTestCaseId, setCurrentTestCaseId] = useState(''); // 当前查看的案例集ID

    // OCR服务状态
    const [ocrStatus, setOcrStatus] = useState(false);
    const [ocrLoading, setOcrLoading] = useState(false);

    // 获取OCR服务状态
    const fetchOcrStatus = async (silent = false) => {
        try {
            setOcrLoading(true);
            if (!silent) message.loading({ content: '获取OCR服务状态中...', key: 'ocrStatus' });
            
            const response = await AiTestCaseGeneratorService.getOcrStatus();
            
            if (response && response.code === 200 && response.data) {
                setOcrStatus(response.data.ocr_enabled === true);
                if (!silent) message.success({ content: '获取OCR状态成功', key: 'ocrStatus' });
            } else {
                setOcrStatus(false);
                if (!silent) message.error({ content: '获取OCR状态失败', key: 'ocrStatus' });
            }
        } catch (error) {
            setOcrStatus(false);
            if (!silent) message.error({ content: `获取OCR状态异常: ${error.message}`, key: 'ocrStatus' });
        } finally {
            setOcrLoading(false);
        }
    };

    // 加载历史生成记录
    const fetchGenerationHistory = async () => {
        try {
            setHistoryLoading(true);
            const response = await AiTestCaseGeneratorService.getGenerationHistory({ page: 1, page_size: 100 });
            if (response && response.data && response.data.records) {
                const historyData = response.data.records.map(record => ({
                    key: record.test_case_id,
                    TestCaseID: record.test_case_id,
                    TestCaseGenStatus: record.status,
                    Message: record.message,
                    createTime: record.create_time,
                    // 默认赋予一个空链接，真实的链接可能需要调用详情接口获取，不过对于展示来说可以兼容
                    DownloadUrl: '',
                    businessProcess: record.message?.includes('泛化') ? '测试集泛化' : '指令附件生成'
                }));
                setGeneratedResults(historyData);
            }
        } catch (error) {
            message.error(`加载历史记录失败: ${error.message}`);
        } finally {
            setHistoryLoading(false);
        }
    };

    // 组件挂载时拉取历史记录
    useEffect(() => {
        fetchGenerationHistory();
        fetchOcrStatus(true); // 静默获取OCR状态
    }, []);

    // 计算按钮是否应该被禁用
    const isGenerateBtnDisabled = useMemo(() => {
        if (loading) return true;

        if (functionType === '测试集泛化') {
            // 测试集泛化：必须上传测试集
            return fileList.length === 0;
        } else if (functionType === '指令附件生成&比对') {
            if (REQUIRES_TEMPLATE_PROCESSES.includes(businessProcess)) {
                // 需要模板的流程：必须同时上传测试集和模板
                return fileList.length === 0 || templateFileList.length === 0;
            }
            // 其他存款协议：不需要上传文件
            return false;
        }

        return false;
    }, [loading, functionType, businessProcess, fileList, templateFileList]);

    // 搜索和筛选状态
    const [searchText, setSearchText] = useState('');
    const [statusFilter, setStatusFilter] = useState('all');
    const [dateRange, setDateRange] = useState([]);

    // 生成泛化数据
    const handleGenerate = async () => {
        // 需要模板的流程和测试集泛化需要上传测试集 Excel 文件
        if ((functionType === '测试集泛化' || REQUIRES_TEMPLATE_PROCESSES.includes(businessProcess)) && fileList.length === 0) {
            message.warning('请先上传测试集 Excel 文件');
            return;
        }

        if (functionType === '指令附件生成&比对' && REQUIRES_TEMPLATE_PROCESSES.includes(businessProcess) && templateFileList.length === 0) {
            message.warning(`当前流程（${businessProcess}）需要上传 Word 模板文件`);
            return;
        }

        if (functionType !== '测试集泛化' && comparisonEnabled && !ocrStatus) {
            message.warning('OCR服务未开启，请联系开发开启后进行评测比对');
            return;
        }

        if (functionType !== '测试集泛化' && fileCount < 1) {
            message.warning('文件数量至少为 1');
            return;
        }

        setLoading(true);
        message.info('开始请求后端服务，请稍候...');

        try {
            let result;
            if (functionType === '测试集泛化') {
                const params = {
                    file: fileList[0].originFileObj,
                    enable_generalization: generalizationEnabled,
                    enable_adversarial: adversarialEnabled,
                };
                result = await AiTestCaseGeneratorService.generate(params);
            } else {
                // 组装参数，调用服务层接口
                const params = {
                    business_process: businessProcess,
                    file_count: fileCount,
                    enable_generalization: generalizationEnabled,
                    enable_adversarial: adversarialEnabled,
                    enable_comparison: comparisonEnabled,
                };

                if (REQUIRES_TEMPLATE_PROCESSES.includes(businessProcess)) {
                    params.upload_file = fileList[0].originFileObj;
                    params.template_file = templateFileList[0].originFileObj;
                }

                result = await AiTestCaseGeneratorService.generateAttachments(params);
            }

            // 将后端返回结果组装后塞入表格数据源
            const newResult = {
                key: result.TestCaseID || `TC_${Date.now()}`,
                TestCaseID: result.TestCaseID || '-',
                TestCaseGenStatus: result.TestCaseGenStatus || 'N',
                Message: result.Message || '操作完成',
                DownloadUrl: result.DownloadUrl || '',
                createTime: dateUtils.formatDate(new Date())
            };

            // 提取 Attachments 并展示（如果有）
            if (result.Attachments && Array.isArray(result.Attachments) && result.Attachments.length > 0) {
                // 如果后端返回了多个附件链接，将它们拼接在一起
                const attachmentUrls = result.Attachments.map(att => att.download_url).filter(Boolean);
                if (attachmentUrls.length > 0) {
                    newResult.DownloadUrl = attachmentUrls.join(';');
                }
            }

            // 保存历史记录，将新结果添加到已有结果的前面
            setGeneratedResults(prevResults => [newResult, ...prevResults]);
            message.success('生成任务已成功完成！');

            // 如果开启了比对评测，自动轮询获取比对结果
            if (comparisonEnabled && result.TestCaseID) {
                pollComparisonResult(result.TestCaseID, newResult.createTime);
            }
        } catch (error) {
            message.error(error.message || '生成失败，请检查网络或后端服务');
        } finally {
            setLoading(false);
        }
    };

    // 轮询获取比对结果
    const pollComparisonResult = async (testCaseId, createTime, retryCount = 0) => {
        const MAX_RETRIES = 100; // 最大重试次数
        const RETRY_INTERVAL = 5000; // 重试间隔(ms)

        try {
            const response = await AiTestCaseGeneratorService.getComparisonResult(testCaseId);

            if (response && response.data && response.data.length > 0) {
                // 将获取到的比对明细组装并存入列表
                const newComparisonResults = response.data.map((item, index) => ({
                    key: `${testCaseId}_${index}`,
                    TestCaseID: testCaseId,
                    createTime: createTime,
                    ...item
                }));

                setComparisonResults(prev => [...newComparisonResults, ...prev]);
                message.success(`案例集 ${testCaseId} 的比对结果已返回`);
            } else if (retryCount < MAX_RETRIES) {
                // 如果没有数据说明还在比对中，继续轮询
                setTimeout(() => {
                    pollComparisonResult(testCaseId, createTime, retryCount + 1);
                }, RETRY_INTERVAL);
            } else {
                message.warning(`案例集 ${testCaseId} 比对超时`);
            }
        } catch (error) {
            console.error('获取比对结果失败:', error);
            if (retryCount < MAX_RETRIES) {
                setTimeout(() => {
                    pollComparisonResult(testCaseId, createTime, retryCount + 1);
                }, RETRY_INTERVAL);
            }
        }
    };
    // 下载文件函数 - 调用DOWNLOAD_ATTACHMENTS接口直接下载
    const handleDownload = async (record) => {
        if (!record || !record.TestCaseID) {
            message.warning('缺少必要的下载参数');
            return;
        }

        try {
            message.loading({ content: '正在下载文件...', key: 'download' });

            // 调用下载接口获取二进制流（blob）
            const blob = await AiTestCaseGeneratorService.downloadAttachments({
                test_case_id: record.TestCaseID,
                file_type: record.file_type || '',
                file_sub_type: record.file_sub_type || ''
            });

            // 判断文件后缀：如果功能是测试集泛化，固定为 .xlsx；否则后端会自动处理为 zip 或 pdf
            const extension = record.businessProcess === '测试集泛化' ? '.xlsx' : '.zip';
            const filename = `${record.TestCaseID}${extension}`;

            // 创建下载链接并触发下载
            const blobUrl = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = blobUrl;
            link.download = filename;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);

            // 释放Blob URL
            URL.revokeObjectURL(blobUrl);

            message.success({ content: `文件下载成功: ${filename}`, key: 'download' });
        } catch (error) {
            message.error({ content: `下载失败: ${error.message || '未知错误'}`, key: 'download' });
            console.error('下载失败:', error);
        }
    };

    // 查询比对结果
    const handleQueryComparisonResults = async () => {
        if (comparisonSearchText.trim()) {
            // 如果输入了特定的 TestCaseID，直接调用后端接口查询历史数据
            try {
                message.loading({ content: '正在查询比对结果...', key: 'query_comp' });
                const response = await AiTestCaseGeneratorService.getComparisonResult(comparisonSearchText.trim());
                
                if (response && response.code === 200 && response.data && response.data.length > 0) {
                    const newComparisonResults = response.data.map((item, index) => ({
                        key: `${comparisonSearchText.trim()}_${index}_${Date.now()}`,
                        TestCaseID: comparisonSearchText.trim(),
                        createTime: dateUtils.formatDate(new Date()), // 历史查询暂用当前时间占位，或从生成结果中匹配
                        ...item
                    }));
                    
                    // 将查询到的结果合并到列表中（去重）
                    setComparisonResults(prev => {
                        const filtered = prev.filter(p => p.TestCaseID !== comparisonSearchText.trim());
                        return [...newComparisonResults, ...filtered];
                    });
                    message.success({ content: '比对结果查询完成', key: 'query_comp' });
                } else {
                    message.warning({ content: '暂无该案例集的比对结果', key: 'query_comp' });
                }
            } catch (error) {
                message.error({ content: `查询失败: ${error.message}`, key: 'query_comp' });
            }
            return;
        }

        if (generatedResults.length === 0) {
            message.warning('暂无生成结果，且未输入案例集ID');
            return;
        }

        message.info('开始查询比对结果...');
        console.log('开始查询比对结果，生成结果数量:', generatedResults.length);

        let hasResults = false;

        // 对所有生成结果查询比对结果
        for (const result of generatedResults) {
            if (result.TestCaseID && result.TestCaseID !== '-') {
                try {
                    console.log(`正在查询案例集 ${result.TestCaseID} 的比对结果...`);
                    const response = await AiTestCaseGeneratorService.getComparisonResult(result.TestCaseID);
                    console.log(`案例集 ${result.TestCaseID} 的比对结果响应:`, response);

                    // 响应格式: { code: 200, message: "success", data: [...] }
                    if (response && response.code === 200 && response.data && Array.isArray(response.data) && response.data.length > 0) {
                        // 将获取到的比对明细组装并存入列表
                        const newComparisonResults = response.data.map((item, index) => ({
                            key: `${result.TestCaseID}_${index}_${Date.now()}`,
                            TestCaseID: result.TestCaseID,
                            createTime: result.createTime,
                            ...item
                        }));

                        console.log(`案例集 ${result.TestCaseID} 找到 ${newComparisonResults.length} 条比对结果`);
                        setComparisonResults(prev => [...newComparisonResults, ...prev]);
                        hasResults = true;
                    } else {
                        console.log(`案例集 ${result.TestCaseID} 暂无比对结果或响应格式不正确`);
                    }
                } catch (error) {
                    console.error(`查询案例集 ${result.TestCaseID} 的比对结果失败:`, error);
                }
            }
        }

        if (hasResults) {
            message.success('比对结果查询完成，已更新列表');
        } else {
            message.info('比对结果查询完成，暂无新的比对结果');
        }
    };

    // 按test_case_id分组比对结果
    const groupedComparisonResults = useMemo(() => {
        const groups = {};

        comparisonResults.forEach(result => {
            const testCaseId = result.TestCaseID;
            if (!groups[testCaseId]) {
                groups[testCaseId] = [];
            }
            groups[testCaseId].push(result);
        });

        // 转换为数组并计算汇总信息
        return Object.keys(groups).map((testCaseId, index) => {
            const items = groups[testCaseId];
            const createTime = items[0]?.createTime || '';

            // 计算平均正确率
            let totalPercentage = 0;
            let validCount = 0;
            items.forEach(item => {
                const percentage = parseFloat(item.correct_percentage);
                if (!isNaN(percentage)) {
                    totalPercentage += percentage;
                    validCount++;
                }
            });
            const avgPercentage = validCount > 0 ? (totalPercentage / validCount) : 0;

            // 判断比对状态：如果所有项都通过则为"比对完成"，否则为"比对失败"
            const allPassed = items.every(item => item.pass_or_not === 'Y');
            const status = allPassed ? '比对完成' : '比对失败';

            return {
                key: testCaseId,
                index: index + 1,
                TestCaseID: testCaseId,
                status: status,
                avgPercentage: avgPercentage,
                createTime: createTime,
                detailCount: items.length,
                details: items // 保存详细数据
            };
        });
    }, [comparisonResults]);

    // 查看详情
    const handleViewDetail = (record) => {
        setCurrentTestCaseId(record.TestCaseID);
        setCurrentDetailData(record.details);
        setDetailModalVisible(true);
    };

    // 下载比对结果（Excel格式）
    const handleDownloadComparisonResult = (record) => {
        const details = record.details;

    // 准备导出数据
        const exportData = details.map(item => ({
            '案例集 ID': item.TestCaseID,
            '比对状态': item.pass_or_not === 'Y' ? '通过' : '失败',
            '文件类型': item.file_type,
            '子类型': item.file_sub_type,
            '要素名称': item.element_name,
            '要素键': item.element_key,
            '比对总数': item.comparison_count,
            '正确数': item.correct_count,
            '错误数': item.mistake_count,
            '不清晰数': item.unclear_count,
            '正确率': `${parseFloat(item.correct_percentage).toFixed(2)}%`,
            '创建时间': item.createTime
        }));

        // 使用XLSX导出
        const ws = XLSX.utils.json_to_sheet(exportData);
        const wb = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(wb, ws, "比对结果详情");
        const filename = `比对结果_${record.TestCaseID}_${dateUtils.formatDate(new Date(), 'YYYYMMDD_HHmmss')}.xlsx`;
        XLSX.writeFile(wb, filename);
        message.success('比对结果导出成功');
    };

    // 详情弹窗表格列定义
    const detailColumns = [
        {
            title: '案例集 ID',
            dataIndex: 'TestCaseID',
            key: 'TestCaseID',
            width: 150,
        },
        {
            title: '比对状态',
            dataIndex: 'pass_or_not',
            key: 'pass_or_not',
            width: 100,
            render: (status) => (
                <span style={{
                    color: status === 'Y' ? '#52c41a' : '#ff4d4f',
                    fontWeight: 'bold'
                }}>
                    {status === 'Y' ? '通过' : '失败'}
                </span>
            ),
        },
        {
            title: '文件类型',
            dataIndex: 'file_type',
            key: 'file_type',
            width: 120,
        },
        {
            title: '子类型',
            dataIndex: 'file_sub_type',
            key: 'file_sub_type',
            width: 100,
        },
        {
            title: '要素名称',
            dataIndex: 'element_name',
            key: 'element_name',
            width: 120,
        },
        {
            title: '要素键',
            dataIndex: 'element_key',
            key: 'element_key',
            width: 120,
        },
        {
            title: '比对总数',
            dataIndex: 'comparison_count',
            key: 'comparison_count',
            width: 100,
        },
        {
            title: '正确数',
            dataIndex: 'correct_count',
            key: 'correct_count',
            width: 100,
            render: (count) => <span style={{ color: '#52c41a' }}>{count}</span>
        },
        {
            title: '错误数',
            dataIndex: 'mistake_count',
            key: 'mistake_count',
            width: 100,
            render: (count) => <span style={{ color: count > 0 ? '#ff4d4f' : 'inherit' }}>{count}</span>
        },
        {
            title: '不清晰数',
            dataIndex: 'unclear_count',
            key: 'unclear_count',
            width: 100,
        },
        {
            title: '正确率',
            dataIndex: 'correct_percentage',
            key: 'correct_percentage',
            width: 100,
            render: (percent) => `${parseFloat(percent).toFixed(2)}%`
        },
    ];

    // 搜索和筛选逻辑 - 最终健壮版本
    const filteredResults = useMemo(() => {
        return generatedResults.filter(result => {
            // 案例集ID搜索
            const matchesSearch = searchText === '' ||
                (result.TestCaseID && result.TestCaseID.toLowerCase().includes(searchText.toLowerCase()));

            // 生成状态筛选
            const matchesStatus = statusFilter === 'all' ||
                result.TestCaseGenStatus === statusFilter;

            // 创建时间筛选 - 最终健壮版本
            let matchesDate = true;

            // 检查日期范围是否有效
            const isDateRangeValid = dateRange &&
                Array.isArray(dateRange) &&
                dateRange.length === 2 &&
                dateRange[0] &&
                dateRange[1] &&
                dateUtils.isValidDate(dateRange[0]) &&
                dateUtils.isValidDate(dateRange[1]);


            if (isDateRangeValid) {
                try {
                    // 确保result.createTime存在且有效
                    if (!result.createTime) {
                        matchesDate = true; // 如果创建时间为空，不过滤
                    } else {
                        const resultDate = dateUtils.parseDate(result.createTime);

                        if (dateUtils.isValidDate(resultDate)) {
                            const startDate = dateUtils.startOfDay(dateRange[0]);
                            const endDate = dateUtils.startOfDay(dateUtils.addDays(dateRange[1], 1)); // 包含结束日期的全天
                            matchesDate = dateUtils.isBetween(resultDate, startDate, endDate, '[)'); // 包含开始，不包含结束（因为结束是下一天的开始）
                        } else {
                            matchesDate = true; // 如果结果日期无效，不过滤
                        }
                    }


                } catch (error) {
                    console.warn('日期解析错误:', error);
                    matchesDate = true; // 如果解析失败，不过滤该记录
                }
            }

            return matchesSearch && matchesStatus && matchesDate;
        }).sort((a, b) => {
            // 按创建时间升序排序
            const dateA = a.createTime ? dateUtils.parseDate(a.createTime) : null;
            const dateB = b.createTime ? dateUtils.parseDate(b.createTime) : null;

            if (!dateA && !dateB) return 0;
            if (!dateA) return 1; // 没有时间的排后面
            if (!dateB) return -1;

            return dateA - dateB; // 升序排序
        });
    }, [generatedResults, searchText, statusFilter, dateRange]);

    // 清空筛选条件 - 最终健壮版本
    const handleClearFilters = () => {
        setSearchText('');
        setStatusFilter('all');
        setDateRange(null); // 设置为 null，清空日期范围
    };

    // 比对结果搜索和筛选逻辑
    const filteredComparisonResults = useMemo(() => {
        return comparisonResults.filter(result => {
            // 案例集ID搜索
            const matchesSearch = comparisonSearchText === '' ||
                (result.TestCaseID && result.TestCaseID.toLowerCase().includes(comparisonSearchText.toLowerCase()));

            // 状态筛选
            const matchesStatus = comparisonStatusFilter === 'all' ||
                result.pass_or_not === comparisonStatusFilter;

            // 创建时间筛选
            let matchesDate = true;
            const isDateRangeValid = comparisonDateRange &&
                Array.isArray(comparisonDateRange) &&
                comparisonDateRange.length === 2 &&
                comparisonDateRange[0] &&
                comparisonDateRange[1] &&
                dateUtils.isValidDate(comparisonDateRange[0]) &&
                dateUtils.isValidDate(comparisonDateRange[1]);

            if (isDateRangeValid) {
                try {
                    if (!result.createTime) {
                        matchesDate = true;
                    } else {
                        const resultDate = dateUtils.parseDate(result.createTime);
                        if (dateUtils.isValidDate(resultDate)) {
                            const startDate = dateUtils.startOfDay(comparisonDateRange[0]);
                            const endDate = dateUtils.startOfDay(dateUtils.addDays(comparisonDateRange[1], 1));
                            matchesDate = dateUtils.isBetween(resultDate, startDate, endDate, '[)');
                        }
                    }
                } catch (error) {
                    console.warn('比对结果日期解析错误:', error);
                }
            }

            return matchesSearch && matchesStatus && matchesDate;
        }).sort((a, b) => {
            // 按创建时间升序排序
            const dateA = a.createTime ? dateUtils.parseDate(a.createTime) : null;
            const dateB = b.createTime ? dateUtils.parseDate(b.createTime) : null;

            if (!dateA && !dateB) return 0;
            if (!dateA) return 1; // 没有时间的排后面
            if (!dateB) return -1;

            return dateA - dateB; // 升序排序
        });
    }, [comparisonResults, comparisonSearchText, comparisonStatusFilter, comparisonDateRange]);

    const handleClearComparisonFilters = () => {
        setComparisonSearchText('');
        setComparisonStatusFilter('all');
        setComparisonDateRange(null);
    };

    // 导出生成结果到 Excel
    const exportGeneratedResults = () => {
        if (filteredResults.length === 0) {
            message.warning('没有可导出的数据');
            return;
        }

        const exportData = filteredResults.map(item => ({
            '案例集 ID': item.TestCaseID,
            '生成状态': item.TestCaseGenStatus === 'Y' ? '生成成功' : '生成失败',
            '消息提示': item.Message,
            '创建时间': item.createTime,
            '案例下载链接': item.DownloadUrl
        }));

        const ws = XLSX.utils.json_to_sheet(exportData);
        const wb = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(wb, ws, "生成结果");
        XLSX.writeFile(wb, `生成结果_${dateUtils.formatDate(new Date(), 'YYYYMMDD_HHmmss')}.xlsx`);
        message.success('生成结果导出成功');
    };

    // 导出比对结果到 Excel
    const exportComparisonResults = () => {
        if (filteredComparisonResults.length === 0) {
            message.warning('没有可导出的数据');
            return;
        }

        const exportData = filteredComparisonResults.map(item => ({
            '案例集 ID': item.TestCaseID,
            '比对状态': item.pass_or_not === 'Y' ? '通过' : '失败',
            '文件类型': item.file_type,
            '子类型': item.file_sub_type,
            '要素名称': item.element_name,
            '比对总数': item.comparison_count,
            '正确数': item.correct_count,
            '错误数': item.mistake_count,
            '不清晰数': item.unclear_count,
            '正确率': `${(item.correct_percentage * 100).toFixed(2)}%`,
            '创建时间': item.createTime
        }));

        const ws = XLSX.utils.json_to_sheet(exportData);
        const wb = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(wb, ws, "比对结果");
        XLSX.writeFile(wb, `比对结果_${dateUtils.formatDate(new Date(), 'YYYYMMDD_HHmmss')}.xlsx`);
        message.success('比对结果导出成功');
    };

    // 表格列定义
    const columns = [
        {
            title: '序号',
            key: 'index',
            width: 80,
            render: (_, __, index) => index + 1,
        },
        {
            title: '案例集 ID',
            dataIndex: 'TestCaseID',
            key: 'TestCaseID',
            width: 180,
        },
        {
            title: '生成状态',
            dataIndex: 'TestCaseGenStatus',
            key: 'TestCaseGenStatus',
            width: 120,
            render: (status) => (
                <span style={{
                    color: status === 'Y' ? '#52c41a' : '#ff4d4f',
                    fontWeight: 'bold'
                }}>
                    {status === 'Y' ? '生成成功' : '生成失败'}
                </span>
            ),
        },
        {
            title: '消息提示',
            dataIndex: 'Message',
            key: 'Message',
            width: 250,
        },
        {
            title: '创建时间',
            dataIndex: 'createTime',
            key: 'createTime',
            width: 200,
        },
        {
            title: '案例下载',
            key: 'DownloadUrl',
            width: 120,
            render: (_, record) => (
                <Button
                    type={record.TestCaseGenStatus === 'Y' ? 'primary' : 'default'}
                    size="small"
                    disabled={record.TestCaseGenStatus !== 'Y'}
                    onClick={() => handleDownload(record)}
                >
                    下载文件
                </Button>
            ),
        },
    ];

    // 比对结果表格列定义（新的分组显示）
    const comparisonColumns = [
        {
            title: '序号',
            dataIndex: 'index',
            key: 'index',
            width: 80,
        },
        {
            title: '案例集 ID',
            dataIndex: 'TestCaseID',
            key: 'TestCaseID',
            width: 180,
        },
        {
            title: '比对状态',
            dataIndex: 'status',
            key: 'status',
            width: 120,
            render: (status) => (
                <span style={{
                    color: status === '比对完成' ? '#52c41a' : '#ff4d4f',
                    fontWeight: 'bold'
                }}>
                    {status}
                </span>
            ),
        },
        {
            title: '正确率',
            dataIndex: 'avgPercentage',
            key: 'avgPercentage',
            width: 120,
            render: (percent) => `${percent.toFixed(2)}%`
        },
        {
            title: '创建时间',
            dataIndex: 'createTime',
            key: 'createTime',
            width: 180,
        },
        {
            title: '比对详情',
            key: 'actions',
            width: 200,
            render: (_, record) => (
                <Space size="small">
                    <Button
                        type="link"
                        size="small"
                        icon={<EyeOutlined />}
                        onClick={() => handleViewDetail(record)}
                    >
                        详情
                    </Button>
                    <Button
                        type="link"
                        size="small"
                        icon={<DownloadOutlined />}
                        onClick={() => handleDownloadComparisonResult(record)}
                    >
                        下载
                    </Button>
                </Space>
            ),
        },
    ];

    return (
        <div className="ai-tcg-main-page">
            {/* 标题区域 */}
            <div className="ai-tcg-header-section">
                <h1 className="ai-tcg-main-title">智能测试集泛化与附件生成工具</h1>
                <p className="ai-tcg-subtitle">基于 AI 的测试集数据泛化、对抗攻击、指令附件生成&自动化校验</p >
            </div>

            {/* 开关与参数控制区域 */}
            <div className="ai-tcg-switch-section">
                {/* 第一行：功能类型、附件类型、文件数量 */}
                <div className="ai-tcg-switch-group" style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'center', alignItems: 'center', gap: '24px', width: '100%', marginBottom: '20px' }}>
                    <div className="ai-tcg-switch-item">
                        <span className="ai-tcg-switch-label">功能类型</span>
                        <Select
                            value={functionType}
                            onChange={setFunctionType}
                            style={{ width: 180 }}
                        >
                            <Select.Option value="测试集泛化">测试集泛化</Select.Option>
                            <Select.Option value="指令附件生成&比对">指令附件生成&比对</Select.Option>
                        </Select>
                    </div>

                    <div className="ai-tcg-switch-item">
                        <span className="ai-tcg-switch-label" style={{ color: functionType === '测试集泛化' ? 'rgba(0, 0, 0, 0.25)' : 'inherit' }}>附件类型</span>
                        <Select
                            value={businessProcess}
                            onChange={setBusinessProcess}
                            style={{ width: 220 }}
                            disabled={functionType === '测试集泛化'}
                        >
                            <Select.Option value="缴款通知书">缴款通知书</Select.Option>
                            <Select.Option value="标的合同">标的合同</Select.Option>
                            <Select.Option value="他行定存-线下必备条款">他行定存-线下必备条款</Select.Option>
                            <Select.Option value="他行定存-线上-不开具实证书必备条款">他行定存-线上-不开具实证书必备条款</Select.Option>
                            <Select.Option value="他行定存-线上-开具实证书必备条款">他行定存-线上-开具实证书必备条款</Select.Option>
                            <Select.Option value="他行活期必备条款">他行活期必备条款</Select.Option>
                        </Select>
                    </div>

                    <div className="ai-tcg-switch-item">
                        <span className="ai-tcg-switch-label">文件数量</span>
                        <InputNumber
                            min={1}
                            max={100}
                            value={fileCount}
                            onChange={setFileCount}
                            style={{ width: 80 }}
                            disabled={functionType === '测试集泛化'}
                        />
                    </div>
                </div>

                {/* 第二行：所有开关 */}
                <div className="ai-tcg-switch-group" style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'center', alignItems: 'center', gap: '32px', width: '100%' }}>
                    <div className="ai-tcg-switch-item">
                        <span className="ai-tcg-switch-label">泛化开关</span>
                        <Switch
                            checked={generalizationEnabled}
                            onChange={setGeneralizationEnabled}
                            checkedChildren="开启"
                            unCheckedChildren="关闭"
                        />
                    </div>
                    <div className="ai-tcg-switch-item">
                        <span className="ai-tcg-switch-label">对抗生成开关</span>
                        <Switch
                            checked={adversarialEnabled}
                            onChange={setAdversarialEnabled}
                            checkedChildren="开启"
                            unCheckedChildren="关闭"
                        />
                    </div>

                    <div className="ai-tcg-switch-item" style={{ display: 'flex', alignItems: 'center' }}>
                        <span className="ai-tcg-switch-label">评测比对开关</span>
                        <Switch
                            checked={functionType === '测试集泛化' ? false : comparisonEnabled}
                            onChange={setComparisonEnabled}
                            checkedChildren="开启"
                            unCheckedChildren="关闭"
                            disabled={functionType === '测试集泛化'}
                        />
                        {functionType !== '测试集泛化' && (
                            <Tooltip title="OCR服务是否开启指示器。点击刷新状态。如果OCR服务未开启，强行进行评测比对可能会失败。">
                                <div 
                                    style={{ marginLeft: 12, display: 'flex', alignItems: 'center', cursor: 'pointer' }}
                                    onClick={() => fetchOcrStatus(false)}
                                >
                                    <div style={{
                                        width: '10px',
                                        height: '10px',
                                        borderRadius: '50%',
                                        backgroundColor: ocrStatus ? '#52c41a' : '#ff4d4f',
                                        marginRight: '6px'
                                    }}></div>
                                    <span style={{ color: ocrStatus ? '#52c41a' : '#ff4d4f', fontSize: '13px', fontWeight: '500' }}>
                                        {ocrStatus ? 'OCR开启' : 'OCR关闭'}
                                    </span>
                                    {ocrLoading && <SyncOutlined spin style={{ marginLeft: 6, color: '#1890ff', fontSize: '12px' }} />}
                                </div>
                            </Tooltip>
                        )}
                    </div>
                </div>
            </div>

            {/* 文件上传区域 */}
            <div className="ai-tcg-upload-section">
                <div className="ai-tcg-upload-area-container">
                    {(REQUIRES_TEMPLATE_PROCESSES.includes(businessProcess) || functionType === '测试集泛化') && (
                        <div className="ai-tcg-upload-area">
                            <Upload
                                accept=".xlsx"
                                fileList={fileList}
                                onChange={handleUpload}
                                beforeUpload={() => false} // 阻止自动上传
                            >
                                <Button icon={<UploadOutlined />}>上传测试集 (.xlsx)</Button>
                            </Upload>
                        </div>
                    )}

                    {functionType === '指令附件生成&比对' && REQUIRES_TEMPLATE_PROCESSES.includes(businessProcess) && (
                        <div className="ai-tcg-upload-area">
                            <Upload
                                accept=".docx"
                                fileList={templateFileList}
                                onChange={handleTemplateUpload}
                                beforeUpload={() => false}
                            >
                                <Button icon={<UploadOutlined />}>上传模板 (.docx)</Button>
                            </Upload>
                        </div>
                    )}
                </div>

                {functionType === '指令附件生成&比对' && REQUIRES_TEMPLATE_PROCESSES.includes(businessProcess) && (
                    <p className="ai-tcg-upload-description">提示: 测试集请包含 TEST_AUDIT_ID, ELEMENT_KEY 等必需列。当前流程（{businessProcess}）需额外上传 Word 模板。</p >
                )}
                {functionType === '测试集泛化' && (
                    <p className="ai-tcg-upload-description">提示: 上传原始测试集 Excel 文件，自动进行数据泛化和对抗攻击生成。</p >
                )}

                <Button
                    type="primary"
                    className="ai-tcg-generate-btn"
                    onClick={handleGenerate}
                    disabled={isGenerateBtnDisabled}
                    loading={loading}
                >
                    {loading ? '处理中...' : (
                        functionType === '测试集泛化'
                            ? '处理测试集'
                            : (comparisonEnabled ? '生成附件与评测' : '生成附件')
                    )}
                </Button>
            </div>

            {/* 生成结果区域 */}
            <div className="ai-tcg-result-section visible">
                <div className="ai-tcg-result-header" style={{ paddingRight: '16px' }}>
                    <h3 className="ai-tcg-result-title">生成结果</h3>
                    <div className="ai-tcg-filter-info" style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                        {filteredResults.length !== generatedResults.length && (
                            <span className="ai-tcg-filter-count">
                                已筛选 {filteredResults.length} / {generatedResults.length} 条记录
                            </span>
                        )}
                        <Button
                            type="default"
                            icon={<DownloadOutlined />}
                            onClick={exportGeneratedResults}
                            disabled={filteredResults.length === 0}
                        >
                            导出
                        </Button>
                    </div>
                </div>

                {/* 搜索筛选工具栏 */}
                <div className="ai-tcg-search-filter-toolbar" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Space size="middle" wrap>
                        {/* 案例集ID搜索 */}
                        <Input
                            placeholder="搜索案例集ID"
                            prefix={<SearchOutlined />}
                            value={searchText}
                            onChange={(e) => setSearchText(e.target.value)}
                            style={{ width: 200 }}
                            allowClear
                        />

                        {/* 生成状态筛选 */}
                        <Select
                            value={statusFilter}
                            onChange={setStatusFilter}
                            style={{ width: 120 }}
                            placeholder="生成状态"
                        >
                            <Select.Option value="all">全部状态</Select.Option>
                            <Select.Option value="Y">生成成功</Select.Option>
                            <Select.Option value="N">生成失败</Select.Option>
                        </Select>

                        {/* 创建时间筛选 */}
                        <DatePicker.RangePicker
                            value={dateRange}
                            onChange={setDateRange}
                            placeholder={['开始时间', '结束时间']}
                            style={{ width: 240 }}
                            format="YYYY-MM-DD"
                            allowClear
                        />

                        {/* 清空筛选按钮 */}
                        <Button
                            icon={<FilterOutlined />}
                            onClick={handleClearFilters}
                            disabled={searchText === '' && statusFilter === 'all' && (!dateRange || dateRange.length === 0)}
                        >
                            清空筛选
                        </Button>
                    </Space>

                    {/* 查询按钮放右侧 */}
                    <Button
                        type="primary"
                        icon={<SearchOutlined />}
                        loading={historyLoading}
                        onClick={async () => {
                            if (searchText.trim()) {
                                // 精确查询单个历史记录
                                try {
                                    setHistoryLoading(true);
                                    const response = await AiTestCaseGeneratorService.getGenerationResult(searchText.trim());
                                    if (response && response.code === 200 && response.data) {
                                        const record = response.data;
                                        
                                        // 提取下载链接
                                        let downloadUrl = '';
                                        if (record.attachments && record.attachments.length > 0) {
                                            downloadUrl = record.attachments.map(att => att.download_url).filter(Boolean).join(';');
                                        }

                                        const historyData = [{
                                            key: record.test_case_id,
                                            TestCaseID: record.test_case_id,
                                            TestCaseGenStatus: record.status,
                                            Message: record.message,
                                            createTime: record.create_time,
                                            DownloadUrl: downloadUrl,
                                            businessProcess: record.message?.includes('泛化') ? '测试集泛化' : '指令附件生成'
                                        }];
                                        setGeneratedResults(historyData);
                                        message.success('查询完成');
                                    } else {
                                        setGeneratedResults([]);
                                        message.warning('未找到对应的生成记录');
                                    }
                                } catch (error) {
                                    message.error(`查询失败: ${error.message}`);
                                } finally {
                                    setHistoryLoading(false);
                                }
                            } else {
                                // 没有搜索词时重新拉取分页列表
                                await fetchGenerationHistory();
                                message.success('查询完成');
                            }
                        }}
                        style={{ minWidth: 100 }}
                    >
                        查询
                    </Button>
                </div>

                <Table
                    columns={columns}
                    dataSource={filteredResults}
                    pagination={{
                        pageSize: 5,
                        showSizeChanger: true,
                        showQuickJumper: true,
                        showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条记录`,
                    }}
                    size="middle"
                    locale={{
                        emptyText: filteredResults.length === 0 ? '暂无符合条件的结果' : '加载中...'
                    }}
                />
            </div >

            {/* 比对结果区域 */}
            <div className={`ai-tcg-result-section ${comparisonEnabled && functionType !== '测试集泛化' ? 'visible' : 'hidden'}`}>
                <div className="ai-tcg-result-header" style={{ paddingRight: '16px' }}>
                    <h3 className="ai-tcg-result-title">比对结果</h3>
                    <div className="ai-tcg-filter-info" style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                        {filteredComparisonResults.length !== comparisonResults.length && (
                            <span className="ai-tcg-filter-count">
                                已筛选 {filteredComparisonResults.length} / {comparisonResults.length} 条记录
                            </span>
                        )}
                        <Button
                            type="default"
                            icon={<DownloadOutlined />}
                            onClick={exportComparisonResults}
                            disabled={filteredComparisonResults.length === 0}
                        >
                            导出
                        </Button>
                    </div>
                </div>

                {/* 比对结果搜索筛选工具栏 */}
                <div className="ai-tcg-search-filter-toolbar" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Space size="middle" wrap>
                        {/* 案例集ID搜索 */}
                        <Input
                            placeholder="搜索案例集ID"
                            prefix={<SearchOutlined />}
                            value={comparisonSearchText}
                            onChange={(e) => setComparisonSearchText(e.target.value)}
                            style={{ width: 200 }}
                            allowClear
                        />

                        {/* 比对状态筛选 */}
                        <Select
                            value={comparisonStatusFilter}
                            onChange={setComparisonStatusFilter}
                            style={{ width: 120 }}
                            placeholder="比对状态"
                        >
                            <Select.Option value="all">全部状态</Select.Option>
                            <Select.Option value="Y">比对通过</Select.Option>
                            <Select.Option value="N">比对失败</Select.Option>
                        </Select>

                        {/* 创建时间筛选 */}
                        <DatePicker.RangePicker
                            value={comparisonDateRange}
                            onChange={setComparisonDateRange}
                            placeholder={['开始时间', '结束时间']}
                            style={{ width: 240 }}
                            format="YYYY-MM-DD"
                            allowClear
                        />

                        {/* 清空筛选按钮 */}
                        <Button
                            icon={<FilterOutlined />}
                            onClick={handleClearComparisonFilters}
                            disabled={comparisonSearchText === '' && comparisonStatusFilter === 'all' && (!comparisonDateRange || comparisonDateRange.length === 0)}
                        >
                            清空筛选
                        </Button>
                    </Space>

                    {/* 查询按钮放右侧 */}
                    <Button
                        type="primary"
                        icon={<SearchOutlined />}
                        onClick={handleQueryComparisonResults}
                        style={{ minWidth: 100 }}
                    >
                        查询
                    </Button>
                </div>

                <Table
                    columns={comparisonColumns}
                    dataSource={groupedComparisonResults}
                    scroll={{ x: 'max-content' }} // 添加水平滚动，防止列多时挤压
                    pagination={{
                        pageSize: 5,
                        showSizeChanger: true,
                        showQuickJumper: true,
                        showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条记录`,
                    }}
                    size="middle"
                    locale={{
                        emptyText: groupedComparisonResults.length === 0 ? '暂无符合条件的结果' : '加载中...'
                    }}
                />
            </div >

            {/* 比对结果详情弹窗 */}
            <Modal
                title={`比对结果详情 - 案例集ID: ${currentTestCaseId}`}
                open={detailModalVisible}
                onCancel={() => setDetailModalVisible(false)}
                footer={[
                    <Button key="close" onClick={() => setDetailModalVisible(false)}>
                        关闭
                    </Button>,
                    <Button
                        key="download"
                        type="primary"
                        icon={<DownloadOutlined />}
                        onClick={() => {
                            const record = groupedComparisonResults.find(r => r.TestCaseID === currentTestCaseId);
                            if (record) {
                                handleDownloadComparisonResult(record);
                            }
                        }}
                    >
                        下载Excel
                    </Button>,
                ]}
                width={1400}
            >
                <Table
                    columns={detailColumns}
                    dataSource={currentDetailData}
                    scroll={{ x: 'max-content' }}
                    pagination={{
                        pageSize: 10,
                        showSizeChanger: true,
                        showQuickJumper: true,
                        showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条记录`,
                    }}
                    size="small"
                />
            </Modal>
        </div >
    );
};

export default MainPage;