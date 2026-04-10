"""
菜单加载工具 - 从 YAML 配置文件动态加载导航菜单
"""

import os
import yaml


def load_menus():
    """
    加载菜单配置
    
    Returns:
        list: 菜单项列表，包含完整 SVG 图标
    """
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'menus.yaml')
    
    if not os.path.exists(config_path):
        return get_default_menus()
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            menus = config.get('menus', get_default_menus())
            icons = config.get('icons', {})
            
            # 为每个菜单项注入完整 SVG
            for menu in menus:
                icon_key = menu.get('icon', '')
                if icon_key in icons:
                    menu['icon'] = f'<svg class="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="{icons[icon_key]}"/></svg>'
                menu['endpoint'] = menu.get('route', '')
                
                # 使用Flask的url_for生成正确的URL
                try:
                    # 尝试动态导入flask并生成URL
                    from flask import current_app, url_for
                    with current_app.app_context():
                        menu['url'] = url_for(menu.get('route', ''))
                except Exception as e:
                    print(f"URL生成失败: {e}")
                    # 如果失败，使用备用URL生成
                    route_parts = menu.get('route', '').split('.')
                    if len(route_parts) == 2:
                        menu['url'] = f"/{route_parts[1].replace('_', '-')}"
                    else:
                        menu['url'] = f"/{menu.get('id', '')}"
            
            return menus
    except Exception as e:
        print(f'加载菜单配置失败：{e}')
        return get_default_menus()


def get_default_menus():
    """返回默认菜单配置"""
    return [
        {
            'id': 'dashboard',
            'name': '仪表盘',
            'icon': '<svg class="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/></svg>',
            'endpoint': 'core.dashboard'
        },
        {
            'id': 'ai-generator',
            'name': 'AI 用例生成',
            'icon': '<svg class="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>',
            'endpoint': 'core.ai_generator'
        },
        {
            'id': 'ui-automation',
            'name': 'UI 自动化',
            'icon': '<svg class="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2"/></svg>',
            'endpoint': 'core.ui_automation'
        },
        {
            'id': 'test-runs',
            'name': '测试执行',
            'icon': '<svg class="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2M9 5a2 2 0 012-2h2a2 2 0 012 2"/></svg>',
            'endpoint': 'core.test_runs'
        },
        {
            'id': 'defects',
            'name': '缺陷管理',
            'icon': '<svg class="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg>',
            'endpoint': 'core.defects'
        },
        {
            'id': 'reports',
            'name': '报告导出',
            'icon': '<svg class="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>',
            'endpoint': 'core.reports'
        }
    ]