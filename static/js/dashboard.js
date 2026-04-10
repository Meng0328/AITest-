/**
 * 仪表盘页面脚本
 * 负责加载和展示项目统计、最近执行、缺陷分布等数据
 */

window.CURRENT_PAGE = 'dashboard';

// ==================== 初始化 ====================
document.addEventListener('DOMContentLoaded', function() {
    loadDashboardData();
});

// ==================== 仪表盘数据加载 ====================
async function loadDashboardData() {
    const projectId = window.APP_STATE?.currentProjectId;
    if (!projectId) {
        renderEmptyDashboard();
        return;
    }
    
    try {
        const [casesRes, runsRes, defectsRes] = await Promise.all([
            fetch(`/api/projects/${projectId}/test-cases`),
            fetch(`/api/projects/${projectId}/test-runs`),
            fetch(`/api/projects/${projectId}/defects`)
        ]);
        
        const casesData = await casesRes.json();
        const runsData = await runsRes.json();
        const defectsData = await defectsRes.json();
        
        updateStats(casesData, runsData, defectsData);
        updateRecentRuns(runsData);
        updateDefectChart(defectsData);
        
    } catch (error) {
        console.error('Dashboard data load failed:', error);
        showToast('加载仪表盘数据失败', 'error');
    }
}

function renderEmptyDashboard() {
    document.getElementById('statTotalCases').textContent = '0';
    document.getElementById('statPassRate').textContent = '0%';
    document.getElementById('statDefects').textContent = '0';
    document.getElementById('statLastRun').textContent = '-';
    document.getElementById('recentTestRuns').innerHTML = '<tr><td colspan="5" class="text-center text-gray-400">请先选择或创建项目</td></tr>';
}

function updateStats(casesData, runsData, defectsData) {
    const totalCases = casesData.data?.length || 0;
    const lastRun = runsData.data?.[0];
    const passRate = lastRun ? lastRun.pass_rate : 0;
    const totalDefects = defectsData.data?.length || 0;
    
    document.getElementById('statTotalCases').textContent = totalCases;
    document.getElementById('statPassRate').textContent = passRate.toFixed(1) + '%';
    document.getElementById('statDefects').textContent = totalDefects;
    document.getElementById('statLastRun').textContent = lastRun ? 
        formatRelativeTime(lastRun.created_at) : '-';
}

function updateRecentRuns(runsData) {
    const tbody = document.getElementById('recentTestRuns');
    if (!tbody) return;
    
    const runs = runsData.data?.slice(0, 5) || [];
    
    if (runs.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center text-gray-400">暂无数据</td></tr>';
        return;
    }
    
    tbody.innerHTML = runs.map(run => `
        <tr>
            <td class="font-medium">${run.name}</td>
            <td><span class="badge badge-sm badge-neutral">${run.test_type}</span></td>
            <td><span class="status-badge status-${run.status}">${run.status}</span></td>
            <td>${run.pass_rate}%</td>
            <td class="text-sm text-gray-500">${formatRelativeTime(run.created_at)}</td>
        </tr>
    `).join('');
}

function updateDefectChart(defectsData) {
    const chartContainer = document.getElementById('defectChart');
    if (!chartContainer) return;
    
    const defects = defectsData.data || [];
    
    if (defects.length === 0) {
        chartContainer.innerHTML = '<p class="text-gray-400">暂无缺陷数据</p>';
        return;
    }
    
    // 按严重程度统计
    const severityCount = {
        critical: 0,
        major: 0,
        minor: 0,
        trivial: 0
    };
    
    defects.forEach(d => {
        const sev = d.severity || 'minor';
        severityCount[sev] = (severityCount[sev] || 0) + 1;
    });
    
    // 简单柱状图
    const maxCount = Math.max(...Object.values(severityCount), 1);
    
    chartContainer.innerHTML = `
        <div class="w-full h-full flex items-end justify-around px-4">
            ${Object.entries(severityCount).map(([severity, count]) => {
                const height = (count / maxCount) * 100;
                const colors = {
                    critical: 'bg-red-500',
                    major: 'bg-orange-500',
                    minor: 'bg-yellow-500',
                    trivial: 'bg-blue-500'
                };
                const labels = {
                    critical: '严重',
                    major: '主要',
                    minor: '次要',
                    trivial: '轻微'
                };
                
                return `
                    <div class="flex flex-col items-center">
                        <div class="text-sm font-bold mb-2">${count}</div>
                        <div class="${colors[severity]} w-12 rounded-t" style="height: ${Math.max(height, 10)}%"></div>
                        <div class="text-xs mt-2 text-gray-600">${labels[severity]}</div>
                    </div>
                `;
            }).join('')}
        </div>
    `;
}

// ==================== 导出到全局 ====================
window.updateDashboard = loadDashboardData;
window.loadDashboardData = loadDashboardData;