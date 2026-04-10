/**
 * AI 用例生成页面脚本
 * 负责需求输入、AI 模型选择、用例生成与展示
 */

window.CURRENT_PAGE = 'ai-generator';

// ==================== 初始化 ====================
document.addEventListener('DOMContentLoaded', function() {
    loadTestCases(window.APP_STATE?.currentProjectId);
});

// ==================== 测试用例加载 ====================
async function loadTestCases(projectId) {
    if (!projectId) {
        const container = document.getElementById('generatedCases');
        if (container) {
            container.innerHTML = '<p class="text-gray-400 text-center py-8">请先选择或创建项目</p>';
        }
        return;
    }
    
    try {
        const response = await fetch(`/api/projects/${projectId}/test-cases`);
        const data = await response.json();
        
        const container = document.getElementById('generatedCases');
        if (!container) return;
        
        const cases = data.data || [];
        
        if (cases.length === 0) {
            container.innerHTML = '<p class="text-gray-400 text-center py-8">暂无用例，请在下方输入需求生成</p>';
            return;
        }
        
        container.innerHTML = cases.map(tc => `
            <div class="card bg-base-100 shadow-sm">
                <div class="card-body p-4">
                    <div class="flex justify-between items-start">
                        <h3 class="font-semibold">${tc.title}</h3>
                        <span class="badge badge-${tc.priority === 'high' ? 'error' : tc.priority === 'medium' ? 'warning' : 'info'} badge-sm">
                            ${tc.priority}
                        </span>
                    </div>
                    <p class="text-sm text-gray-600 mt-2">${tc.description || ''}</p>
                    <div class="text-xs text-gray-400 mt-2 flex gap-4">
                        <span>模型：${tc.ai_model || '-'}</span>
                        <span>创建：${formatRelativeTime(tc.created_at)}</span>
                    </div>
                    <div class="mt-3 flex gap-2">
                        <button onclick="editTestCase(${tc.id})" class="btn btn-xs btn-ghost">编辑</button>
                        <button onclick="deleteTestCase(${tc.id})" class="btn btn-xs btn-ghost text-error">删除</button>
                    </div>
                </div>
            </div>
        `).join('');
        
    } catch (error) {
        console.error('Load test cases failed:', error);
        showToast('加载用例失败', 'error');
    }
}

// ==================== AI 生成用例 ====================
async function generateTestCases() {
    const requirementInput = document.getElementById('requirementInput');
    const aiModelSelect = document.getElementById('aiModelSelect');
    const prioritySelect = document.getElementById('prioritySelect');
    
    const requirement = requirementInput ? requirementInput.value.trim() : '';
    const model = aiModelSelect ? aiModelSelect.value : 'qwen-plus';
    const priority = prioritySelect ? prioritySelect.value : 'medium';
    
    if (!requirement) {
        showToast('请输入需求描述', 'error');
        return;
    }
    
    const projectId = window.APP_STATE?.currentProjectId;
    if (!projectId) {
        showToast('请先选择或创建项目', 'error');
        return;
    }
    
    showToast('正在生成测试用例...', 'info');
    
    try {
        const response = await fetch('/api/ai/generate-test-cases', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                project_id: projectId,
                requirement,
                model,
                priority
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            const count = data.created_cases?.length || data.test_cases?.length || 0;
            showToast(`成功生成 ${count} 个用例`, 'success');
            
            // 清空输入框
            if (requirementInput) requirementInput.value = '';
            
            // 重新加载用例列表
            loadTestCases(projectId);
            
            // 更新仪表盘
            if (window.updateDashboard) {
                window.updateDashboard();
            }
        } else {
            showToast('生成失败：' + (data.error || '未知错误'), 'error');
        }
        
    } catch (error) {
        console.error('Generate test cases failed:', error);
        showToast('请求失败：' + error.message, 'error');
    }
}

// ==================== 用例操作 ====================
async function editTestCase(caseId) {
    showToast('编辑功能开发中...', 'info');
    // TODO: 打开编辑模态框
}

async function deleteTestCase(caseId) {
    if (!confirm('确定要删除这个用例吗？')) return;
    
    try {
        const response = await fetch(`/api/test-cases/${caseId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('用例已删除', 'success');
            loadTestCases(window.APP_STATE?.currentProjectId);
        } else {
            showToast('删除失败：' + data.error, 'error');
        }
        
    } catch (error) {
        showToast('请求失败：' + error.message, 'error');
    }
}

// ==================== 导出到全局 ====================
window.loadTestCases = loadTestCases;
window.generateTestCases = generateTestCases;
window.editTestCase = editTestCase;
window.deleteTestCase = deleteTestCase;