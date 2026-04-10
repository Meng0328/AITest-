"""
Proxy API - HTTP 代理接口
支持 UI 自动化测试任意站点，解决 CORS 跨域问题
"""

from flask import Blueprint, request, jsonify
from services.proxy_service import ProxyService

proxy = Blueprint('proxy', __name__, url_prefix='/api/proxy')
proxy_service = ProxyService()


@proxy.route('/request', methods=['POST'])
def proxy_request():
    """
    通用 HTTP 代理接口
    
    Request JSON:
    {
        "method": "GET",
        "url": "https://example.com/api",
        "headers": {"Content-Type": "application/json"},
        "data": null,
        "json": {"key": "value"},
        "timeout": 30
    }
    
    Response JSON:
    {
        "success": true,
        "status": 200,
        "headers": {...},
        "body": "...",
        "cookies": {...},
        "elapsed": 0.5
    }
    """
    data = request.json
    
    if not data or not data.get('url'):
        return jsonify({
            'success': False,
            'error': '缺少必要参数：url'
        }), 400
    
    method = data.get('method', 'GET')
    url = data['url']
    headers = data.get('headers', {})
    timeout = data.get('timeout')
    
    # 验证 URL 格式
    if not url.startswith(('http://', 'https://')):
        return jsonify({
            'success': False,
            'error': 'URL 必须以 http:// 或 https:// 开头'
        }), 400
    
    # 执行代理请求
    result = proxy_service.forward_request(
        method=method,
        url=url,
        headers=headers,
        data=data.get('data'),
        json_data=data.get('json'),
        timeout=timeout
    )
    
    if result.get('success'):
        return jsonify(result), result.get('status', 200)
    else:
        return jsonify(result), result.get('status', 500)


@proxy.route('/get', methods=['POST'])
def proxy_get():
    """简化版 GET 代理接口"""
    data = request.json
    
    if not data or not data.get('url'):
        return jsonify({'success': False, 'error': '缺少 URL 参数'}), 400
    
    result = proxy_service.get(
        url=data['url'],
        headers=data.get('headers', {}),
        timeout=data.get('timeout')
    )
    
    return jsonify(result)


@proxy.route('/post', methods=['POST'])
def proxy_post():
    """简化版 POST 代理接口"""
    data = request.json
    
    if not data or not data.get('url'):
        return jsonify({'success': False, 'error': '缺少 URL 参数'}), 400
    
    result = proxy_service.post(
        url=data['url'],
        headers=data.get('headers', {}),
        json_data=data.get('json'),
        timeout=data.get('timeout')
    )
    
    return jsonify(result)


@proxy.route('/health', methods=['GET'])
def health_check():
    """代理服务健康检查"""
    return jsonify({
        'success': True,
        'status': 'healthy',
        'service': 'proxy'
    })