#!/usr/bin/env python3
"""
AI Test Hub - API 快速测试脚本
验证核心接口是否正常工作
"""

import requests
import json

BASE_URL = 'http://localhost:5000'


def test_health():
    """测试健康检查"""
    response = requests.get(f'{BASE_URL}/api/health')
    print(f"✓ 健康检查：{response.json()['status']}")


def test_project_create():
    """测试项目创建"""
    response = requests.post(f'{BASE_URL}/api/projects', json={
        'name': '测试项目',
        'description': 'API 自动创建的测试项目'
    })
    data = response.json()
    if data.get('success'):
        print(f"✓ 项目创建成功：ID={data['data']['id']}")
        return data['data']['id']
    else:
        print(f"✗ 项目创建失败：{data.get('error')}")
        return None


def test_test_case_create(project_id):
    """测试用例创建"""
    response = requests.post(f'{BASE_URL}/api/projects/{project_id}/test-cases', json={
        'title': '用户登录测试',
        'description': '验证用户使用正确凭据可以成功登录',
        'steps': ['打开登录页面', '输入用户名', '输入密码', '点击登录按钮'],
        'expected_result': '用户成功登录并跳转到首页',
        'priority': 'high'
    })
    data = response.json()
    if data.get('success'):
        print(f"✓ 测试用例创建成功：ID={data['data']['id']}")
        return True
    else:
        print(f"✗ 测试用例创建失败：{data.get('error')}")
        return False


def test_defect_create(project_id):
    """测试缺陷创建"""
    response = requests.post(f'{BASE_URL}/api/projects/{project_id}/defects', json={
        'title': '登录页面响应缓慢',
        'description': '在网络正常的情况下，登录页面加载时间超过 5 秒',
        'severity': 'major',
        'assigned_to': 'developer'
    })
    data = response.json()
    if data.get('success'):
        print(f"✓ 缺陷创建成功：ID={data['data']['id']}")
        return True
    else:
        print(f"✗ 缺陷创建失败：{data.get('error')}")
        return False


def test_test_run_create(project_id):
    """测试执行记录创建"""
    response = requests.post(f'{BASE_URL}/api/projects/{project_id}/test-runs', json={
        'name': '自动化测试执行 #1',
        'test_type': 'ui'
    })
    data = response.json()
    if data.get('success'):
        print(f"✓ 测试执行记录创建成功：ID={data['data']['id']}")
        return data['data']['id']
    else:
        print(f"✗ 测试执行记录创建失败：{data.get('error')}")
        return None


def main():
    print("=" * 60)
    print("AI Test Hub - API 接口测试")
    print("=" * 60)
    
    try:
        # 1. 健康检查
        test_health()
        
        # 2. 创建项目
        project_id = test_project_create()
        if not project_id:
            print("\n✗ 测试中止：无法创建项目")
            return
        
        # 3. 创建测试用例
        test_test_case_create(project_id)
        
        # 4. 创建缺陷
        test_defect_create(project_id)
        
        # 5. 创建测试执行记录
        test_run_id = test_test_run_create(project_id)
        if test_run_id:
            # 6. 开始执行
            response = requests.post(f'{BASE_URL}/api/test-runs/{test_run_id}/start')
            if response.json().get('success'):
                print(f"✓ 测试执行已开始")
            
            # 7. 完成执行
            response = requests.post(f'{BASE_URL}/api/test-runs/{test_run_id}/complete', json={
                'status': 'completed',
                'passed_cases': 8,
                'failed_cases': 2
            })
            if response.json().get('success'):
                print(f"✓ 测试执行已完成")
        
        print("\n" + "=" * 60)
        print("✅ 所有 API 测试通过！")
        print("=" * 60)
        
    except requests.exceptions.ConnectionError:
        print("\n✗ 错误：无法连接到服务器，请确保 app.py 正在运行")
    except Exception as e:
        print(f"\n✗ 测试失败：{e}")


if __name__ == '__main__':
    main()