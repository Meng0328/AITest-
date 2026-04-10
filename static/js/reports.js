/**
 * 报告导出页面脚本
 * 负责选择测试执行、选择格式、生成和下载报告等功能
 */

window.CURRENT_PAGE = 'reports';

// ==================== 初始化 ====================
document.addEventListener('DOMContentLoaded', function() {
    loadTestRunsForReport(window.APP_STATE?.currentProjectId);
});

// ==================== 加载测试执行列表 ====================
async function loadTestRunsForReport(projectId) {
    if (!projectId) {
        const select = document.getElementById('reportTestRunSelect');
        if (select) {
            select.innerHTML = '<option value="">请先选择项目</option>';
        }
        return;
    }
    
    try {
        const response = await fetch(`/api/projects/${projectId}/test-runs`);
        const data = await response.json();
        
        const select = document.getElementById('reportTestRunSelect');
        if (!select) return;
        
        const runs = data.data || [];
        
        if (runs.length === 0) {
            select.innerHTML = '<option value="">暂无执行记录</option>';
            return;
        }
        
        select.innerHTML = runs.map(run => 
            `<option value="${run.id}">${run.name} (${run.status}) - ${formatDate(run.created_at)}</option>`
        ).join('');
        
    } catch (error) {
        console.error('Load test runs for report failed:', error);
        showToast('加载执行记录失败', 'error');
    }
}

// ==================== 导出报告 ====================
async function exportReport() {
    const testRunSelect = document.getElementById('reportTestRunSelect');
    const formatSelect = document.getElementById('reportFormat');
    
    const testRunId = testRunSelect ? testRunSelect.value : '';
    const format = formatSelect ? formatSelect.value : 'html';
    
    if (!testRunId) {
        showToast('请选择测试执行记录', 'error');
        return;
    }
    
    showToast('正在生成报告...', 'info');
    
    try {
        const response = await fetch('/api/reports/export', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                test_run_id: parseInt(testRunId),
                format: format
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('报告生成成功', 'success');
            
            // 显示预览或下载
            const preview = document.getElementById('reportPreview');
            if (preview) {
                preview.innerHTML = `
                    <div class="prose max-w-none">
                        <h3 class="text-lg font-bold mb-4">测试报告</h3>
                        <p><strong>格式：</strong>${format.toUpperCase()}</p>
                        <p><strong>生成时间：</strong>${new Date().toLocaleString()}</p>
                        <a href="${data.data.download_url}" class="btn btn-primary mt-4">
                            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/>
                            </svg>
                            下载报告
                        </a>
                    </div>
                `;
            }
            
            // 自动下载
            if (data.data.download_url) {
                window.location.href = data.data.download_url;
            }
        } else {
            showToast('生成失败：' + data.error, 'error');
        }
        
    } catch (error) {
        showToast('请求失败：' + error.message, 'error');
    }
}

// ==================== 预览报告 ====================
async function previewReport() {
    const testRunId = document.getElementById('reportTestRunSelect')?.value;
    
    if (!testRunId) {
        showToast('请选择测试执行记录', 'error');
        return;
    }
    
    showToast('正在加载预览...', 'info');
    
    // TODO: 调用 API 获取报告预览内容
    setTimeout(() => {
        const preview = document.getElementById('reportPreview');
        if (preview) {
            preview.innerHTML = `
                <div class="prose max-w-none">
                    <h3 class="text-lg font-bold mb-4">测试报告预览</h3>
                    <div class="bg-gray-50 p-4 rounded">
                        <p class="text-gray-500">报告预览功能开发中...</p>
                    </div>
                </div>
            `;
        }
        showToast('预览已加载', 'success');
    }, 1000);
}

// ==================== 导出到全局 ====================
window.loadTestRunsForReport = loadTestRunsForReport;
window.exportReport = exportReport;
window.previewReport = previewReport;