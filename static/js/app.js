/**
 * AI Test Hub - 通用应用脚本
 * 提供 WebSocket 连接、Toast 通知、API 请求等通用功能
 */

// ==================== 全局状态 ====================
window.APP_STATE = {
    socket: null,
    currentProjectId: null,
    currentUser: 'user_' + Math.random().toString(36).substr(2, 6),
    connected: false
};

// ==================== 初始化 ====================
document.addEventListener('DOMContentLoaded', function() {
    initSocket();
    loadProjects();
    console.log('AI Test Hub initialized');
});

// ==================== WebSocket 连接 ====================
function initSocket() {
    const socket = io();
    window.APP_STATE.socket = socket;
    
    socket.on('connect', function() {
        window.APP_STATE.connected = true;
        updateConnectionStatus(true);
        console.log('Connected to server');
    });
    
    socket.on('disconnect', function() {
        window.APP_STATE.connected = false;
        updateConnectionStatus(false);
        console.log('Disconnected from server');
    });
    
    // 项目事件
    socket.on('project_created', function(data) {
        showToast('新项目已创建：' + data.project.name, 'success');
        loadProjects();
    });
    
    socket.on('project_deleted', function(data) {
        showToast('项目已删除', 'info');
        loadProjects();
    });
    
    // 用例事件
    socket.on('test_case_created', function(data) {
        showToast('新用例已添加', 'success');
        if (window.APP_STATE.currentProjectId) {
            loadTestCases(window.APP_STATE.currentProjectId);
        }
    });
    
    socket.on('test_case_deleted', function(data) {
        showToast('用例已删除', 'info');
        if (window.APP_STATE.currentProjectId) {
            loadTestCases(window.APP_STATE.currentProjectId);
        }
    });
    
    // 执行事件
    socket.on('test_run_created', function(data) {
        showToast('新执行记录已创建', 'success');
        if (window.APP_STATE.currentProjectId) {
            loadTestRuns(window.APP_STATE.currentProjectId);
        }
    });
    
    socket.on('test_run_completed', function(data) {
        showToast('测试执行完成', 'success');
        if (window.APP_STATE.currentProjectId) {
            loadTestRuns(window.APP_STATE.currentProjectId);
            updateDashboard();
        }
    });
    
    // 缺陷事件
    socket.on('defect_created', function(data) {
        showToast('新缺陷已记录', 'info');
        if (window.APP_STATE.currentProjectId) {
            loadDefects(window.APP_STATE.currentProjectId);
        }
    });
}

function updateConnectionStatus(connected) {
    const statusEl = document.getElementById('connectionStatus');
    if (!statusEl) return;
    
    if (connected) {
        statusEl.innerHTML = '<span class="w-2 h-2 bg-green-400 rounded-full animate-pulse"></span><span class="text-sm">已连接</span>';
    } else {
        statusEl.innerHTML = '<span class="w-2 h-2 bg-red-400 rounded-full"></span><span class="text-sm">已断开</span>';
    }
}

// ==================== 项目管理 ====================
async function loadProjects() {
    try {
        const response = await fetch('/api/projects');
        const data = await response.json();
        
        const selector = document.getElementById('projectSelector');
        if (!selector) return;
        
        selector.innerHTML = '<option value="">选择项目...</option>';
        
        data.data.forEach(project => {
            const option = document.createElement('option');
            option.value = project.id;
            option.textContent = project.name;
            selector.appendChild(option);
        });
        
        if (data.data.length > 0 && !window.APP_STATE.currentProjectId) {
            window.APP_STATE.currentProjectId = data.data[0].id;
            selector.value = window.APP_STATE.currentProjectId;
            loadProject(window.APP_STATE.currentProjectId);
        }
    } catch (error) {
        showToast('加载项目失败：' + error.message, 'error');
    }
}

function loadProject(projectId) {
    window.APP_STATE.currentProjectId = projectId;
    if (!projectId) return;
    
    // 根据当前页面加载对应数据
    const currentPage = window.CURRENT_PAGE || 'dashboard';
    
    if (currentPage === 'dashboard') {
        updateDashboard();
    } else if (currentPage === 'ai-generator') {
        loadTestCases(projectId);
    } else if (currentPage === 'test-runs') {
        loadTestRuns(projectId);
    } else if (currentPage === 'defects') {
        loadDefects(projectId);
    }
}

function showCreateProjectModal() {
    const modal = document.getElementById('createProjectModal');
    if (modal) modal.showModal();
}

function closeCreateProjectModal() {
    const modal = document.getElementById('createProjectModal');
    if (modal) modal.close();
    const nameInput = document.getElementById('newProjectName');
    const descInput = document.getElementById('newProjectDesc');
    if (nameInput) nameInput.value = '';
    if (descInput) descInput.value = '';
}

async function submitCreateProject() {
    const nameInput = document.getElementById('newProjectName');
    const descInput = document.getElementById('newProjectDesc');
    
    const name = nameInput ? nameInput.value.trim() : '';
    const description = descInput ? descInput.value.trim() : '';
    
    if (!name) {
        showToast('请输入项目名称', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/projects', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, description })
        });
        
        const data = await response.json();
        if (data.success) {
            showToast('项目创建成功', 'success');
            closeCreateProjectModal();
            loadProjects();
        } else {
            showToast('创建失败：' + data.error, 'error');
        }
    } catch (error) {
        showToast('请求失败：' + error.message, 'error');
    }
}

// ==================== Toast 通知 ====================
function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    if (!container) {
        console.log(`[${type.toUpperCase()}] ${message}`);
        return;
    }
    
    const toast = document.createElement('div');
    toast.className = `alert alert-${type} shadow-lg mb-2`;
    toast.innerHTML = `<span>${message}</span>`;
    container.appendChild(toast);
    
    setTimeout(() => toast.remove(), 3000);
}

// ==================== API 请求封装 ====================
async function apiRequest(url, options = {}) {
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
        },
    };
    
    const mergedOptions = {
        ...defaultOptions,
        ...options,
        headers: {
            ...defaultOptions.headers,
            ...(options.headers || {}),
        },
    };
    
    try {
        const response = await fetch(url, mergedOptions);
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || `HTTP ${response.status}`);
        }
        
        return data;
    } catch (error) {
        console.error('API Request failed:', error);
        throw error;
    }
}

// ==================== 工具函数 ====================
function formatDate(dateString) {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleString('zh-CN');
}

function formatRelativeTime(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    const now = new Date();
    const diff = now - date;
    
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);
    
    if (minutes < 1) return '刚刚';
    if (minutes < 60) return `${minutes}分钟前`;
    if (hours < 24) return `${hours}小时前`;
    if (days < 7) return `${days}天前`;
    
    return date.toLocaleDateString('zh-CN');
}

// ==================== 导航管理 ====================
function navigateToPage(endpoint, event) {
    event.preventDefault();
    
    // 更新侧边栏激活状态
    document.querySelectorAll('.sidebar-item').forEach(item => {
        item.classList.remove('active');
    });
    event.currentTarget.classList.add('active');
    
    // 使用 History API 进行无刷新导航
    const url = event.target.closest('a').href;
    history.pushState(null, null, url);
    
    // 加载对应页面内容
    loadPageContent(endpoint);
}

async function loadPageContent(endpoint) {
    try {
        // 显示加载状态
        showToast('页面加载中...', 'info');
        
        // 根据 endpoint 加载对应数据
        const projectId = window.APP_STATE.currentProjectId;
        
        switch(endpoint) {
            case 'core.dashboard':
                if (projectId) updateDashboard();
                break;
            case 'core.ai_generator':
                if (projectId) loadTestCases(projectId);
                break;
            case 'core.ui_automation':
                // UI 自动化页面有自己的初始化逻辑
                if (window.initUIAutomation) {
                    window.initUIAutomation();
                }
                break;
            case 'core.test_runs':
                if (projectId) loadTestRuns(projectId);
                break;
            case 'core.defects':
                if (projectId) loadDefects(projectId);
                break;
            case 'core.reports':
                if (window.initReports) {
                    window.initReports();
                }
                break;
        }
        
        showToast('页面加载完成', 'success');
    } catch (error) {
        showToast('页面加载失败：' + error.message, 'error');
    }
}

// 处理浏览器前进后退
window.addEventListener('popstate', function() {
    const currentPath = window.location.pathname;
    const endpoint = getEndpointFromPath(currentPath);
    if (endpoint) {
        loadPageContent(endpoint);
    }
});

function getEndpointFromPath(path) {
    // 简单的路径到 endpoint 映射
    const pathMap = {
        '/dashboard': 'core.dashboard',
        '/ai-generator': 'core.ai_generator',
        '/ui-automation': 'core.ui_automation',
        '/test-runs': 'core.test_runs',
        '/defects': 'core.defects',
        '/reports': 'core.reports'
    };
    return pathMap[path];
}

// 页面导航函数
function navigateToPage(endpoint, url, event) {
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }
    
    // 更新当前页面状态
    window.CURRENT_PAGE = endpoint.replace('core.', '');
    
    // 更新侧边栏激活状态
    document.querySelectorAll('.sidebar-item').forEach(item => {
        item.classList.remove('active');
    });
    
    const clickedItem = event.target.closest('.sidebar-item');
    if (clickedItem) {
        clickedItem.classList.add('active');
    }
    
    // 使用历史API进行无刷新导航
    history.pushState({ endpoint: endpoint }, '', url);
    
    // 加载页面内容
    loadPageContent(url);
}

function loadPageContent(url) {
    // 显示加载状态
    const mainContent = document.querySelector('main');
    if (mainContent) {
        mainContent.innerHTML = '<div class="flex justify-center items-center h-64"><div class="loading loading-spinner loading-lg text-primary"></div></div>';
    }
    
    // 使用fetch加载新页面内容
    fetch(url)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            return response.text();
        })
        .then(html => {
            // 解析HTML并提取主要内容
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            const newContent = doc.querySelector('main');
            
            if (newContent && mainContent) {
                mainContent.innerHTML = newContent.innerHTML;
                
                // 重新初始化页面特定功能
                const currentEndpoint = window.CURRENT_PAGE;
                if (currentEndpoint === 'dashboard') {
                    if (window.updateDashboard) updateDashboard();
                } else if (currentEndpoint === 'ai_generator') {
                    if (window.loadTestCases) loadTestCases(window.APP_STATE.currentProjectId);
                } else if (currentEndpoint === 'test_runs') {
                    if (window.loadTestRuns) loadTestRuns(window.APP_STATE.currentProjectId);
                } else if (currentEndpoint === 'defects') {
                    if (window.loadDefects) loadDefects(window.APP_STATE.currentProjectId);
                }
            }
        })
        .catch(error => {
            console.error('页面加载失败:', error);
            if (mainContent) {
                mainContent.innerHTML = `
                    <div class="alert alert-error">
                        <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <span>页面加载失败: ${error.message}</span>
                    </div>
                `;
            }
        });
}

// 处理浏览器前进后退
window.addEventListener('popstate', function(event) {
    if (event.state && event.state.endpoint) {
        const url = window.location.pathname;
        loadPageContent(url);
        
        // 更新侧边栏状态
        document.querySelectorAll('.sidebar-item').forEach(item => {
            item.classList.remove('active');
            if (item.dataset.endpoint === event.state.endpoint) {
                item.classList.add('active');
            }
        });
    }
});

// 导出到全局
window.showToast = showToast;
window.apiRequest = apiRequest;
window.formatDate = formatDate;
window.formatRelativeTime = formatRelativeTime;
window.navigateToPage = navigateToPage;
window.loadPageContent = loadPageContent;