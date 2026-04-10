/**
 * AI Proxy v2.0 - 多模型接口统一封装
 * 支持 CSDN 与 GitCode 双端点，模型映射、失败自动降级、流式解析
 */

const AI_PROVIDERS = {
    csdn: {
        name: 'CSDN',
        baseUrl: 'https://models.csdn.net/v1/chat/completions',
        apiKey: 'sk-ffpztriquewtxvay',
        models: ['Deepseek-V3', 'qwen-vl-plus', 'doubao', 'ernie', 'gpt-4']
    },
    gitcode: {
        name: 'GitCode',
        baseUrl: 'https://ai.gitcode.com/models/v1/chat/completions',
        apiKey: 'sk-ffpztriquewtxvay', // 使用相同 key，实际使用时可配置
        models: ['deepseek-chat', 'qwen-plus', 'glm-4', 'baichuan2', 'yi-34b']
    }
};

// 模型映射表：统一内部名称到各提供商的实际模型名
const MODEL_MAPPING = {
    'Deepseek-V3': { csdn: 'Deepseek-V3', gitcode: 'deepseek-chat' },
    'qwen-vl-plus': { csdn: 'qwen-vl-plus', gitcode: 'qwen-plus' },
    'doubao': { csdn: 'doubao', gitcode: null },
    'ernie': { csdn: 'ernie', gitcode: null },
    'gpt-4': { csdn: 'gpt-4', gitcode: null },
    'deepseek-chat': { csdn: 'Deepseek-V3', gitcode: 'deepseek-chat' },
    'qwen-plus': { csdn: 'qwen-vl-plus', gitcode: 'qwen-plus' },
    'glm-4': { csdn: null, gitcode: 'glm-4' },
    'baichuan2': { csdn: null, gitcode: 'baichuan2' },
    'yi-34b': { csdn: null, gitcode: 'yi-34b' }
};

class AIProxy {
    constructor() {
        this.currentProvider = localStorage.getItem('ai-provider') || 'csdn';
        this.modelHistory = new Map();
        this.retryCount = 0;
        this.maxRetries = 2;
        
        // Task 8: 错误码定义 v2.2
        this.ERROR_CODES = {
            'UI-01': '用户输入为空',
            'UI-02': '网络请求超时',
            'UI-03': 'AI 返回格式错误',
            'UI-04': '浏览器兼容性错误',
            'UI-05': '跨域被拦截',
            'UI-06': 'OCR 识别为空',
            'UI-07': '文档解析失败',
            'UI-08': '用例生成接口超时'
        };
        
        // 错误日志存储
        this.errorLogs = JSON.parse(localStorage.getItem('aiErrorLogs') || '[]');
    }

    /**
     * 设置当前提供商
     */
    setProvider(provider) {
        if (AI_PROVIDERS[provider]) {
            this.currentProvider = provider;
            localStorage.setItem('ai-provider', provider);
            return true;
        }
        return false;
    }

    /**
     * 获取当前提供商信息
     */
    getProvider() {
        return AI_PROVIDERS[this.currentProvider];
    }

    /**
     * 获取所有可用提供商列表
     */
    getAvailableProviders() {
        return Object.keys(AI_PROVIDERS).map(key => ({
            id: key,
            name: AI_PROVIDERS[key].name,
            models: AI_PROVIDERS[key].models
        }));
    }

    /**
     * 模型名称转换：内部名 -> 提供商实际模型名
     */
    resolveModel(internalModel) {
        const mapping = MODEL_MAPPING[internalModel];
        if (!mapping) return internalModel;
        return mapping[this.currentProvider] || internalModel;
    }

    /**
     * 构建准确率优化 Prompt
     */
    buildOptimizedPrompt(userPrompt, enableOptimization = true) {
        if (!enableOptimization) return userPrompt;

        const optimizationInstructions = `
【测试用例生成规范】
请严格按照以下结构输出测试用例：

## 测试概述
简要说明测试目标和范围

## 测试场景
### 场景 1：正常流程
- 前置条件：
- 测试步骤：
  1. 
  2. 
  3. 
- 预期结果：

### 场景 2：异常流程
- 前置条件：
- 测试步骤：
  1. 
  2. 
- 预期结果：

## 测试数据
| 字段 | 类型 | 有效值 | 边界值 | 无效值 |

## 可执行脚本
\`\`\`javascript
// 自动化测试代码
\`\`\`

【质量要求】
- 覆盖等价类划分、边界值分析
- 包含至少 3 个异常场景
- 提供可运行的自动化脚本
- 使用清晰的 Markdown 格式
`;

        return `${optimizationInstructions}\n\n用户需求：${userPrompt}`;
    }

    /**
     * 调用 AI 接口（支持流式）
     */
    async call(model, messages, options = {}) {
        const {
            stream = true,
            temperature = 0.7,
            topP = 0.7,
            maxTokens = 2000,
            enableOptimization = true,
            provider = this.currentProvider
        } = options;

        // 记忆化参数
        const cacheKey = `${provider}:${model}`;
        if (!this.modelHistory.has(cacheKey)) {
            this.modelHistory.set(cacheKey, { temperature, topP, calls: 0 });
        }
        const history = this.modelHistory.get(cacheKey);
        history.calls++;

        // 构建 Prompt
        const optimizedMessages = messages.map(msg => {
            if (msg.role === 'user' && enableOptimization) {
                return { ...msg, content: this.buildOptimizedPrompt(msg.content) };
            }
            return msg;
        });

        // 解析模型名
        const resolvedModel = this.resolveModel(model);
        const providerConfig = AI_PROVIDERS[provider];

        if (!resolvedModel) {
            throw new Error(`模型 ${model} 在 ${provider} 平台不可用`);
        }

        try {
            const response = await fetch(providerConfig.baseUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${providerConfig.apiKey}`
                },
                body: JSON.stringify({
                    model: resolvedModel,
                    messages: optimizedMessages,
                    stream,
                    temperature,
                    top_p: topP,
                    max_tokens: maxTokens
                })
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(`${provider} API 错误 ${response.status}: ${errorData.message || response.statusText}`);
            }

            if (stream) {
                return this.readStream(response.body, provider);
            } else {
                const data = await response.json();
                return data.choices?.[0]?.message?.content || '';
            }

        } catch (error) {
            // 失败自动降级：尝试切换到另一提供商
            if (this.retryCount < this.maxRetries) {
                const alternativeProvider = provider === 'csdn' ? 'gitcode' : 'csdn';
                console.log(`[${provider}] 请求失败，尝试降级到 [${alternativeProvider}]`);
                this.retryCount++;
                return this.call(model, messages, { ...options, provider: alternativeProvider });
            }
            
            this.retryCount = 0;
            throw error;
        }
    }

    /**
     * 流式读取响应
     */
    async *readStream(stream, provider) {
        const reader = stream.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        try {
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop();

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const data = line.slice(6);
                        if (data === '[DONE]') return;
                        try {
                            const parsed = JSON.parse(data);
                            const content = parsed.choices?.[0]?.delta?.content;
                            if (content) {
                                yield content;
                            }
                        } catch (e) {
                            console.warn(`[${provider}] 解析流数据失败:`, e);
                        }
                    }
                }
            }
        } finally {
            reader.releaseLock();
        }
    }

    /**
     * 批量调用（用于对比不同模型结果）
     */
    async batchCall(models, messages, options = {}) {
        const results = [];
        
        for (const model of models) {
            try {
                const result = await this.call(model, messages, { ...options, stream: false });
                results.push({ model, result, success: true });
            } catch (error) {
                results.push({ model, error: error.message, success: false });
            }
        }

        return results;
    }

    /**
     * 获取模型历史统计
     */
    getModelStats() {
        const stats = {};
        for (const [key, history] of this.modelHistory.entries()) {
            const [provider, model] = key.split(':');
            if (!stats[provider]) stats[provider] = {};
            stats[provider][model] = history;
        }
        return stats;
    }

    /**
     * 清除历史记录
     */
    clearHistory() {
        this.modelHistory.clear();
    }

    /**
     * Task 8: 错误日志记录 v2.2
     */
    logError(errorCode, message, details = {}) {
        const errorEntry = {
            id: Date.now(),
            timestamp: new Date().toISOString(),
            errorCode,
            errorMessage: this.ERROR_CODES[errorCode] || '未知错误',
            message,
            details,
            provider: this.currentProvider,
            resolved: false
        };
        
        // 同一错误 5 次以内合并计数
        const recentErrors = this.errorLogs.filter(e => 
            e.errorCode === errorCode && 
            !e.resolved &&
            new Date(e.timestamp) > new Date(Date.now() - 3600000) // 1 小时内
        );
        
        if (recentErrors.length >= 5) {
            // 超出后只记 +N
            const firstError = recentErrors[0];
            firstError.details.count = (firstError.details.count || 1) + 1;
            firstError.details.lastOccurrence = errorEntry.timestamp;
            this.errorLogs[0] = firstError;
        } else {
            this.errorLogs.unshift(errorEntry);
        }
        
        // 保留最近 500 条
        this.errorLogs = this.errorLogs.slice(0, 500);
        localStorage.setItem('aiErrorLogs', JSON.stringify(this.errorLogs));
        
        console.error(`[AI Proxy Error ${errorCode}] ${message}`, details);
        return errorEntry;
    }

    /**
     * 获取错误日志
     */
    getErrorLogs(options = {}) {
        const { type, resolved, limit = 50 } = options;
        let logs = this.errorLogs;
        
        if (type) {
            logs = logs.filter(l => l.errorCode === type);
        }
        
        if (resolved !== undefined) {
            logs = logs.filter(l => l.resolved === resolved);
        }
        
        return logs.slice(0, limit);
    }

    /**
     * 标记错误为已解决
     */
    resolveError(errorId) {
        const error = this.errorLogs.find(e => e.id === errorId);
        if (error) {
            error.resolved = true;
            error.resolvedAt = new Date().toISOString();
            localStorage.setItem('aiErrorLogs', JSON.stringify(this.errorLogs));
            return true;
        }
        return false;
    }

    /**
     * 获取自动修复建议
     */
    getAutoFixSuggestion(errorCode) {
        const suggestions = {
            'UI-05': {
                action: '启动本地代理',
                description: '跨域请求被浏览器拦截，请启动本地 CORS 代理脚本',
                command: 'node cors-proxy.js',
                link: 'cors-proxy.html'
            },
            'UI-06': {
                action: '切换 OCR 语言',
                description: 'OCR 识别结果为空，请尝试切换识别语言或上传更清晰的图片',
                languages: ['chi_sim', 'eng', 'chi_tra']
            },
            'UI-07': {
                action: '重新上传文档',
                description: '文档解析失败，请检查文件格式或尝试重新上传',
                supportedFormats: ['.docx', '.xlsx', '.pdf', '.jpg', '.png']
            },
            'UI-08': {
                action: '切换模型源',
                description: '用例生成接口超时，请尝试切换到另一模型源或稍后重试',
                providers: ['csdn', 'gitcode']
            }
        };
        
        return suggestions[errorCode] || {
            action: '查看错误详情',
            description: '未知错误，请查看完整错误日志'
        };
    }

    /**
     * 一键打包日志
     */
    packageErrorLogs() {
        const packageData = {
            version: '2.2',
            exportedAt: new Date().toISOString(),
            userAgent: navigator.userAgent,
            totalErrors: this.errorLogs.length,
            unresolvedCount: this.errorLogs.filter(e => !e.resolved).length,
            errors: this.errorLogs,
            stats: {
                byErrorCode: {},
                byProvider: {}
            }
        };
        
        // 统计各错误码数量
        this.errorLogs.forEach(e => {
            packageData.stats.byErrorCode[e.errorCode] = (packageData.stats.byErrorCode[e.errorCode] || 0) + 1;
            packageData.stats.byProvider[e.provider] = (packageData.stats.byProvider[e.provider] || 0) + 1;
        });
        
        // 压缩：只保留最近 100 条详细日志
        packageData.errors = this.errorLogs.slice(0, 100);
        
        const blob = new Blob([JSON.stringify(packageData, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `error_logs_${new Date().toISOString().split('T')[0]}_${Date.now()}.json`;
        a.click();
        URL.revokeObjectURL(url);
        
        return packageData;
    }

    /**
     * 清空错误日志
     */
    clearErrorLogs() {
        this.errorLogs = [];
        localStorage.removeItem('aiErrorLogs');
    }
}

// 导出单例
const aiProxy = new AIProxy();

// 兼容旧版 callAI 函数
async function callAI(model, messages, stream = true, temperature = 0.7, topP = 0.7) {
    return aiProxy.call(model, messages, { stream, temperature, topP });
}

// 导出供全局使用
window.AIProxy = AIProxy;
window.aiProxy = aiProxy;
window.callAI = callAI;