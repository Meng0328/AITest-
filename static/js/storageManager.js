/**
 * Storage Manager - 统一数据存储管理模块
 * 提供历史记录、操作记录、文件存储的持久化功能
 * 支持 localStorage 和 File System Access API
 */

class StorageManager {
    constructor() {
        this.STORAGE_KEYS = {
            HISTORY: 'ai_test_history',
            ACTIVITY: 'ai_test_activity',
            FILES: 'ai_test_files',
            FILE_CONTENTS: 'ai_test_file_contents'
        };
        
        // 初始化存储
        this._initStorage();
    }
    
    /**
     * 初始化存储空间
     */
    _initStorage() {
        if (!localStorage.getItem(this.STORAGE_KEYS.HISTORY)) {
            localStorage.setItem(this.STORAGE_KEYS.HISTORY, JSON.stringify([]));
        }
        if (!localStorage.getItem(this.STORAGE_KEYS.ACTIVITY)) {
            localStorage.setItem(this.STORAGE_KEYS.ACTIVITY, JSON.stringify([]));
        }
        if (!localStorage.getItem(this.STORAGE_KEYS.FILES)) {
            localStorage.setItem(this.STORAGE_KEYS.FILES, JSON.stringify([]));
        }
        if (!localStorage.getItem(this.STORAGE_KEYS.FILE_CONTENTS)) {
            localStorage.setItem(this.STORAGE_KEYS.FILE_CONTENTS, JSON.stringify({}));
        }
    }
    
    // ==================== 历史记录管理 ====================
    
    /**
     * 添加历史记录
     * @param {Object} record - 历史记录对象
     */
    addHistory(record) {
        const history = this.getHistory();
        const newRecord = {
            id: this._generateId(),
            timestamp: Date.now(),
            ...record
        };
        history.unshift(newRecord);
        localStorage.setItem(this.STORAGE_KEYS.HISTORY, JSON.stringify(history));
        return newRecord;
    }
    
    /**
     * 获取所有历史记录
     * @returns {Array} 历史记录数组
     */
    getHistory() {
        return JSON.parse(localStorage.getItem(this.STORAGE_KEYS.HISTORY) || '[]');
    }
    
    /**
     * 根据 ID 获取历史记录
     * @param {string} id - 记录 ID
     * @returns {Object|null} 历史记录对象
     */
    getHistoryById(id) {
        const history = this.getHistory();
        return history.find(item => item.id === id) || null;
    }
    
    /**
     * 删除历史记录
     * @param {string} id - 记录 ID
     * @returns {boolean} 是否删除成功
     */
    deleteHistory(id) {
        const history = this.getHistory();
        const filtered = history.filter(item => item.id !== id);
        localStorage.setItem(this.STORAGE_KEYS.HISTORY, JSON.stringify(filtered));
        return true;
    }
    
    /**
     * 清空历史记录
     */
    clearHistory() {
        localStorage.setItem(this.STORAGE_KEYS.HISTORY, JSON.stringify([]));
    }
    
    // ==================== 操作记录管理 ====================
    
    /**
     * 记录操作日志
     * @param {string} action - 操作类型
     * @param {string} module - 模块名称
     * @param {Object} details - 详细信息
     * @param {string} status - 状态 (success/error/warning)
     */
    logActivity(action, module, details = {}, status = 'success') {
        const activities = this.getActivities();
        const newActivity = {
            id: this._generateId(),
            timestamp: Date.now(),
            action,
            module,
            details,
            status
        };
        activities.unshift(newActivity);
        
        // 保留最近 1000 条记录
        if (activities.length > 1000) {
            activities.splice(500);
        }
        
        localStorage.setItem(this.STORAGE_KEYS.ACTIVITY, JSON.stringify(activities));
        return newActivity;
    }
    
    /**
     * 获取所有操作记录
     * @returns {Array} 操作记录数组
     */
    getActivities() {
        return JSON.parse(localStorage.getItem(this.STORAGE_KEYS.ACTIVITY) || '[]');
    }
    
    /**
     * 根据模块筛选操作记录
     * @param {string} module - 模块名称
     * @returns {Array} 操作记录数组
     */
    getActivitiesByModule(module) {
        const activities = this.getActivities();
        return activities.filter(item => item.module === module);
    }
    
    /**
     * 根据状态筛选操作记录
     * @param {string} status - 状态 (success/error/warning)
     * @returns {Array} 操作记录数组
     */
    getActivitiesByStatus(status) {
        const activities = this.getActivities();
        return activities.filter(item => item.status === status);
    }
    
    /**
     * 清空操作记录
     */
    clearActivities() {
        localStorage.setItem(this.STORAGE_KEYS.ACTIVITY, JSON.stringify([]));
    }
    
    // ==================== 文件存储管理 ====================
    
    /**
     * 保存文件
     * @param {File} file - 文件对象
     * @param {string} category - 分类
     * @returns {Object} 文件元数据
     */
    async saveFile(file, category = 'default') {
        const fileId = this._generateId();
        const fileContent = await this._readFileAsBase64(file);
        
        const fileMeta = {
            id: fileId,
            name: file.name,
            size: file.size,
            type: file.type,
            category,
            uploadTime: Date.now(),
            lastModified: file.lastModified
        };
        
        // 保存元数据
        const files = this.getFiles();
        files.unshift(fileMeta);
        localStorage.setItem(this.STORAGE_KEYS.FILES, JSON.stringify(files));
        
        // 保存文件内容
        const contents = this.getFileContents();
        contents[fileId] = fileContent;
        localStorage.setItem(this.STORAGE_KEYS.FILE_CONTENTS, JSON.stringify(contents));
        
        // 记录操作
        this.logActivity('file_upload', 'files', { fileName: file.name, fileSize: file.size });
        
        return fileMeta;
    }
    
    /**
     * 获取所有文件元数据
     * @returns {Array} 文件元数据数组
     */
    getFiles() {
        return JSON.parse(localStorage.getItem(this.STORAGE_KEYS.FILES) || '[]');
    }
    
    /**
     * 根据分类获取文件
     * @param {string} category - 分类
     * @returns {Array} 文件元数据数组
     */
    getFilesByCategory(category) {
        const files = this.getFiles();
        return files.filter(item => item.category === category);
    }
    
    /**
     * 获取文件内容
     * @param {string} fileId - 文件 ID
     * @returns {string|null} Base64 编码的文件内容
     */
    getFileContent(fileId) {
        const contents = this.getFileContents();
        return contents[fileId] || null;
    }
    
    /**
     * 获取所有文件内容
     * @returns {Object} 文件内容对象
     */
    getFileContents() {
        return JSON.parse(localStorage.getItem(this.STORAGE_KEYS.FILE_CONTENTS) || '{}');
    }
    
    /**
     * 删除文件
     * @param {string} fileId - 文件 ID
     * @returns {boolean} 是否删除成功
     */
    deleteFile(fileId) {
        // 删除元数据
        const files = this.getFiles();
        const filteredFiles = files.filter(item => item.id !== fileId);
        localStorage.setItem(this.STORAGE_KEYS.FILES, JSON.stringify(filteredFiles));
        
        // 删除内容
        const contents = this.getFileContents();
        delete contents[fileId];
        localStorage.setItem(this.STORAGE_KEYS.FILE_CONTENTS, JSON.stringify(contents));
        
        // 记录操作
        this.logActivity('file_delete', 'files', { fileId });
        
        return true;
    }
    
    /**
     * 下载文件
     * @param {string} fileId - 文件 ID
     */
    downloadFile(fileId) {
        const files = this.getFiles();
        const file = files.find(item => item.id === fileId);
        if (!file) {
            throw new Error('文件不存在');
        }
        
        const content = this.getFileContent(fileId);
        if (!content) {
            throw new Error('文件内容不存在');
        }
        
        const link = document.createElement('a');
        link.href = content;
        link.download = file.name;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        // 记录操作
        this.logActivity('file_download', 'files', { fileName: file.name });
    }
    
    /**
     * 清空文件存储
     */
    clearFiles() {
        localStorage.setItem(this.STORAGE_KEYS.FILES, JSON.stringify([]));
        localStorage.setItem(this.STORAGE_KEYS.FILE_CONTENTS, JSON.stringify({}));
        this.logActivity('files_cleared', 'files');
    }
    
    // ==================== 工具方法 ====================
    
    /**
     * 生成唯一 ID
     * @returns {string} 唯一 ID
     */
    _generateId() {
        return 'id_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
    
    /**
     * 读取文件为 Base64
     * @param {File} file - 文件对象
     * @returns {Promise<string>} Base64 字符串
     */
    _readFileAsBase64(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => resolve(reader.result);
            reader.onerror = reject;
            reader.readAsDataURL(file);
        });
    }
    
    /**
     * 格式化时间戳
     * @param {number} timestamp - 时间戳
     * @returns {string} 格式化后的时间字符串
     */
    formatTimestamp(timestamp) {
        const date = new Date(timestamp);
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        const hours = String(date.getHours()).padStart(2, '0');
        const minutes = String(date.getMinutes()).padStart(2, '0');
        const seconds = String(date.getSeconds()).padStart(2, '0');
        
        return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
    }
    
    /**
     * 格式化文件大小
     * @param {number} bytes - 字节数
     * @returns {string} 格式化后的大小字符串
     */
    formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    /**
     * 获取存储统计信息
     * @returns {Object} 统计信息
     */
    getStorageStats() {
        const history = this.getHistory();
        const activities = this.getActivities();
        const files = this.getFiles();
        const contents = this.getFileContents();
        
        let totalFileSize = 0;
        files.forEach(file => {
            totalFileSize += file.size;
        });
        
        return {
            historyCount: history.length,
            activityCount: activities.length,
            fileCount: files.length,
            totalFileSize,
            totalFileSizeFormatted: this.formatFileSize(totalFileSize)
        };
    }
}

// 导出单例
const storageManager = new StorageManager();
window.StorageManager = StorageManager;
window.storageManager = storageManager;