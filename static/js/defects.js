/**
 * 缺陷管理页面脚本
 * 负责缺陷列表展示、创建缺陷、编辑缺陷状态等功能
 */

window.CURRENT_PAGE = 'defects';

// ==================== 初始化 ====================
document.addEventListener('DOMContentLoaded', function() {
    loadDefects(window.APP_STATE?.currentProjectId);
});

// ==================== 缺陷加载 ====================
async function loadDefects(projectId) {
    if (!projectId) {
        const tbody = document.getElementById('defectsTable');
        if (tbody) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center text-gray-400">请先选择或创建项目</td></tr>';
        }
        return;
    }
    
    try {
        const response = await fetch(`/api/projects/${projectId}/defects`);
        const data = await response.json();
        
        const tbody = document.getElementById('defectsTable');
        if (!tbody) return;
        
        const defects = data.data || [];
        
        if (defects.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center text-gray-400">暂无缺陷记录</td></tr>';
            return;
        }
        
        tbody.innerHTML = defects.map(defect => `
            <tr>
                <td class="font-medium">#${defect.id}</td>
                <td class="max-w-xs truncate" title="${defect.title}">${defect.title}</td>
                <td>
                    <span class="badge badge-${getSeverityBadge(defect.severity)} badge-sm">
                        ${defect.severity}
                    </span>
                </td>
                <td>
                    <span class="status-badge status-${defect.status === 'open' ? 'fail' : 'pass'}">
                        ${defect.status}
                    </span>
                </td>
                <td>${defect.assigned_to || '-'}</td>
                <td class="text-sm text-gray-500">${formatRelativeTime(defect.created_at)}</td>
                <td>
                    <button onclick="editDefect(${defect.id})" class="btn btn-xs btn-ghost">编辑</button>
                    <button onclick="analyzeDefectWithAI(${defect.id})" class="btn btn-xs btn-primary">AI 分析</button>
                </td>
            </tr>
        `).join('');
        
    } catch (error) {
        console.error('Load defects failed:', error);
        showToast('加载缺陷记录失败', 'error');
    }
}

function getSeverityBadge(severity) {
    const map = {
        'critical': 'error',
        'major': 'warning',
        'minor': 'info',
        'trivial': 'ghost'
    };
    return map[severity] || 'ghost';
}

// ==================== 创建缺陷 ====================
async function createDefect() {
    const titleInput = document.getElementById('newDefectTitle');
    const descInput = document.getElementById('newDefectDesc');
    const severitySelect = document.getElementById('newDefectSeverity');
    const assigneeInput = document.getElementById('newDefectAssignee');
    
    const title = titleInput ? titleInput.value.trim() : '';
    const description = descInput ? descInput.value.trim() : '';
    const severity = severitySelect ? severitySelect.value : 'major';
    const assigned_to = assigneeInput ? assigneeInput.value.trim() : '';
    
    if (!title) {
        showToast('请输入缺陷标题', 'error');
        return;
    }
    
    const projectId = window.APP_STATE?.currentProjectId;
    if (!projectId) {
        showToast('请先选择项目', 'error');
        return;
    }
    
    try {
        const response = await fetch(`/api/projects/${projectId}/defects`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title, description, severity, assigned_to })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('缺陷创建成功', 'success');
            closeCreateDefectModal();
            loadDefects(projectId);
            
            // 更新仪表盘
            if (window.updateDashboard) {
                window.updateDashboard();
            }
        } else {
            showToast('创建失败：' + data.error, 'error');
        }
        
    } catch (error) {
        showToast('请求失败：' + error.message, 'error');
    }
}

// ==================== 编辑缺陷 ====================
async function editDefect(defectId) {
    showToast('编辑缺陷功能开发中...', 'info');
    // TODO: 打开编辑模态框，加载缺陷详情
}

// ==================== AI 分析缺陷 ====================
async function analyzeDefectWithAI(defectId) {
    showToast('正在调用 AI 分析缺陷...', 'info');
    
    try {
        const response = await fetch('/api/ai/analyze-defect', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                defect_id: defectId,
                model: 'qwen-plus'
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            const analysis = data.analysis;
            showToast('AI 分析完成', 'success');
            
            // TODO: 显示分析结果模态框
            console.log('AI Analysis:', analysis);
        } else {
            showToast('分析失败：' + data.error, 'error');
        }
        
    } catch (error) {
        showToast('请求失败：' + error.message, 'error');
    }
}

// ==================== 模态框控制 ====================
function showCreateDefectModal() {
    const modal = document.getElementById('createDefectModal');
    if (modal) {
        modal.showModal();
    }
}

function closeCreateDefectModal() {
    const modal = document.getElementById('createDefectModal');
    if (modal) {
        modal.close();
    }
    
    // 清空表单
    const titleInput = document.getElementById('newDefectTitle');
    const descInput = document.getElementById('newDefectDesc');
    const assigneeInput = document.getElementById('newDefectAssignee');
    
    if (titleInput) titleInput.value = '';
    if (descInput) descInput.value = '';
    if (assigneeInput) assigneeInput.value = '';
}

// ==================== 导出到全局 ====================
window.loadDefects = loadDefects;
window.createDefect = createDefect;
window.editDefect = editDefect;
window.analyzeDefectWithAI = analyzeDefectWithAI;
window.showCreateDefectModal = showCreateDefectModal;
window.closeCreateDefectModal = closeCreateDefectModal;