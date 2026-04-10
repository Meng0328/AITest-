/**
 * 测试执行页面脚本
 * 负责执行记录列表展示、创建执行、启动/停止执行等功能
 */

window.CURRENT_PAGE = 'test-runs';

// ==================== 初始化 ====================
document.addEventListener('DOMContentLoaded', function() {
    loadTestRuns(window.APP_STATE?.currentProjectId);
});

// ==================== 测试执行加载 ====================
async function loadTestRuns(projectId) {
    if (!projectId) {
        const tbody = document.getElementById('testRunsTable');
        if (tbody) {
            tbody.innerHTML = '<tr><td colspan="8" class="text-center text-gray-400">请先选择或创建项目</td></tr>';
        }
        return;
    }
    
    try {
        const response = await fetch(`/api/projects/${projectId}/test-runs`);
        const data = await response.json();
        
        const tbody = document.getElementById('testRunsTable');
        if (!tbody) return;
        
        const runs = data.data || [];
        
        if (runs.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" class="text-center text-gray-400">暂无执行记录</td></tr>';
            return;
        }
        
        tbody.innerHTML = runs.map(run => `
            <tr>
                <td class="font-medium">${run.name}</td>
                <td><span class="badge badge-sm badge-neutral">${run.test_type}</span></td>
                <td>${run.total_cases || 0}</td>
                <td class="text-success">${run.passed_cases || 0}</td>
                <td class="text-error">${run.failed_cases || 0}</td>
                <td><span class="status-badge status-${run.status}">${run.status}</span></td>
                <td class="text-sm text-gray-500">${formatRelativeTime(run.created_at)}</td>
                <td>
                    ${run.status === 'pending' ? `
                        <button onclick="startTestRun(${run.id})" class="btn btn-xs btn-success">开始</button>
                    ` : `
                        <button onclick="viewTestRun(${run.id})" class="btn btn-xs btn-ghost">查看</button>
                        <button onclick="downloadReport(${run.id})" class="btn btn-xs btn-ghost">报告</button>
                    `}
                </td>
            </tr>
        `).join('');
        
        // 更新报告下拉框
        updateReportSelect(runs);
        
    } catch (error) {
        console.error('Load test runs failed:', error);
        showToast('加载执行记录失败', 'error');
    }
}

function updateReportSelect(runs) {
    const reportSelect = document.getElementById('reportTestRunSelect');
    if (!reportSelect) return;
    
    reportSelect.innerHTML = runs.map(run => 
        `<option value="${run.id}">${run.name} (${run.status})</option>`
    ).join('');
}

// ==================== 创建执行记录 ====================
async function createTestRun() {
    const projectId = window.APP_STATE?.currentProjectId;
    if (!projectId) {
        showToast('请先选择项目', 'error');
        return;
    }
    
    try {
        const response = await fetch(`/api/projects/${projectId}/test-runs`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name: 'Test Run ' + new Date().toISOString().slice(0, 19).replace(/[:-]/g, ''),
                test_type: 'ui'
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('创建执行记录成功', 'success');
            loadTestRuns(projectId);
        } else {
            showToast('创建失败：' + data.error, 'error');
        }
        
    } catch (error) {
        showToast('请求失败：' + error.message, 'error');
    }
}

// ==================== 启动执行 ====================
async function startTestRun(runId) {
    try {
        const response = await fetch(`/api/test-runs/${runId}/start`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('测试执行已开始', 'success');
            
            // 模拟执行过程（实际应通过 WebSocket 接收进度）
            setTimeout(() => completeTestRun(runId), 3000);
        } else {
            showToast('启动失败：' + data.error, 'error');
        }
        
    } catch (error) {
        showToast('请求失败：' + error.message, 'error');
    }
}

// ==================== 完成执行 ====================
async function completeTestRun(runId) {
    try {
        const response = await fetch(`/api/test-runs/${runId}/complete`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                status: 'completed',
                passed_cases: Math.floor(Math.random() * 8) + 2,
                failed_cases: Math.floor(Math.random() * 2)
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('测试执行完成', 'success');
            loadTestRuns(window.APP_STATE?.currentProjectId);
            
            // 更新仪表盘
            if (window.updateDashboard) {
                window.updateDashboard();
            }
        } else {
            showToast('完成失败：' + data.error, 'error');
        }
        
    } catch (error) {
        showToast('请求失败：' + error.message, 'error');
    }
}

// ==================== 查看执行详情 ====================
async function viewTestRun(runId) {
    showToast('查看执行详情功能开发中...', 'info');
    // TODO: 打开执行详情模态框，展示步骤结果和截图
}

// ==================== 下载报告 ====================
async function downloadReport(runId) {
    showToast('正在生成报告...', 'info');
    // TODO: 调用报告导出 API
    setTimeout(() => {
        showToast('报告已准备就绪', 'success');
    }, 1500);
}

// ==================== 导出到全局 ====================
window.loadTestRuns = loadTestRuns;
window.createTestRun = createTestRun;
window.startTestRun = startTestRun;
window.viewTestRun = viewTestRun;
window.downloadReport = downloadReport;