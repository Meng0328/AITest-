"""
核心路由模块 - 处理页面导航与布局
解决菜单无法切换、左侧模块点不动等问题，全部走后端路由统一渲染
"""

from flask import Blueprint, render_template, request, url_for, g
from extensions import db
from models import Project
from utils.menu_loader import load_menus

core = Blueprint('core', __name__)


def get_common_context():
    """获取所有页面共用的上下文数据"""
    # 优先使用 g.current_endpoint（用于/page/<name> 动态路由）
    current_endpoint = getattr(g, 'current_endpoint', None) or request.endpoint
    return {
        'projects': Project.query.all(),
        'current_endpoint': current_endpoint,
        'menus': load_menus()
    }


@core.route('/')
def index():
    """主页 - 重定向到仪表盘"""
    return redirect(url_for('core.dashboard'))


@core.route('/dashboard')
def dashboard():
    """仪表盘页面"""
    context = get_common_context()
    return render_template('pages/dashboard.html', **context)


@core.route('/ai-generator')
def ai_generator():
    """AI 用例生成页面"""
    context = get_common_context()
    return render_template('pages/ai_generator.html', **context)


@core.route('/ui-automation')
def ui_automation():
    """UI 自动化页面"""
    context = get_common_context()
    return render_template('pages/ui_automation.html', **context)


@core.route('/test-runs')
def test_runs():
    """测试执行页面"""
    context = get_common_context()
    return render_template('pages/test_runs.html', **context)


@core.route('/defects')
def defects():
    """缺陷管理页面"""
    context = get_common_context()
    return render_template('pages/defects.html', **context)


@core.route('/reports')
def reports():
    """报告导出页面"""
    context = get_common_context()
    return render_template('pages/reports.html', **context)


@core.route('/page/<name>')
def page(name):
    """通用页面路由 - 支持动态加载"""
    page_map = {
        'dashboard': ('pages/dashboard.html', 'core.dashboard'),
        'ai-generator': ('pages/ai_generator.html', 'core.ai_generator'),
        'ui-automation': ('pages/ui_automation.html', 'core.ui_automation'),
        'test-runs': ('pages/test_runs.html', 'core.test_runs'),
        'defects': ('pages/defects.html', 'core.defects'),
        'reports': ('pages/reports.html', 'core.reports')
    }
    
    template_info = page_map.get(name)
    if not template_info:
        return redirect(url_for('core.dashboard'))
    
    template_name, endpoint = template_info
    # 临时设置 endpoint 以便 get_common_context 使用
    from flask import g
    g.current_endpoint = endpoint
    
    context = get_common_context()
    return render_template(template_name, **context)