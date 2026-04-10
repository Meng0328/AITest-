"""
Proxy Service - HTTP 代理 service
支持 UI 自动化测试任意站点，解决 CORS 跨域问题
"""

import requests
from typing import Dict, Any, Optional


class ProxyService:
    """代理服务类 - 统一处理所有 HTTP 代理请求"""
    
    def __init__(self):
        self.default_timeout = 30  # 默认超时 30 秒
        self.max_redirects = 5  # 最大重定向次数
    
    def forward_request(
        self, 
        method: str, 
        url: str, 
        headers: Optional[Dict[str, str]] = None,
        data: Optional[Any] = None,
        json_data: Optional[Dict] = None,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        转发 HTTP 请求
        
        Args:
            method: HTTP 方法 (GET, POST, PUT, DELETE 等)
            url: 目标 URL
            headers: 请求头
            data: 请求体 (form-data)
            json_data: 请求体 (JSON)
            timeout: 超时时间 (秒)
            
        Returns:
            {
                'status': int,
                'headers': dict,
                'body': str,
                'cookies': dict,
                'elapsed': float
            }
        """
        try:
            # 执行请求
            response = requests.request(
                method=method.upper(),
                url=url,
                headers=headers or {},
                data=data,
                json=json_data,
                timeout=timeout or self.default_timeout,
                allow_redirects=True,
                max_redirects=self.max_redirects
            )
            
            # 提取响应头（排除 hop-by-hop 头）
            excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
            response_headers = {
                name: value for name, value in response.headers.items()
                if name.lower() not in excluded_headers
            }
            
            return {
                'success': True,
                'status': response.status_code,
                'headers': dict(response_headers),
                'body': response.text,
                'cookies': dict(response.cookies),
                'elapsed': response.elapsed.total_seconds(),
                'url': response.url
            }
            
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': '请求超时',
                'status': 408,
                'message': f'请求超过 {timeout or self.default_timeout} 秒'
            }
            
        except requests.exceptions.TooManyRedirects:
            return {
                'success': False,
                'error': '重定向过多',
                'status': 418,
                'message': f'超过最大重定向次数 ({self.max_redirects})'
            }
            
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': '请求失败',
                'status': 502,
                'message': str(e)
            }
    
    def get(self, url: str, headers: Optional[Dict[str, str]] = None, **kwargs) -> Dict[str, Any]:
        """发送 GET 请求"""
        return self.forward_request('GET', url, headers=headers, **kwargs)
    
    def post(self, url: str, headers: Optional[Dict[str, str]] = None, json_data: Optional[Dict] = None, **kwargs) -> Dict[str, Any]:
        """发送 POST 请求"""
        return self.forward_request('POST', url, headers=headers, json_data=json_data, **kwargs)
    
    def put(self, url: str, headers: Optional[Dict[str, str]] = None, json_data: Optional[Dict] = None, **kwargs) -> Dict[str, Any]:
        """发送 PUT 请求"""
        return self.forward_request('PUT', url, headers=headers, json_data=json_data, **kwargs)
    
    def delete(self, url: str, headers: Optional[Dict[str, str]] = None, **kwargs) -> Dict[str, Any]:
        """发送 DELETE 请求"""
        return self.forward_request('DELETE', url, headers=headers, **kwargs)