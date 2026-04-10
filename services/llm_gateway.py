"""
LLM Gateway - 多模态 AI 接口统一网关
支持 DeepSeek / 豆包 / 文心一言 / ChatGPT / gitcode 模型广场
实现权重轮询、失败重试、自动降级、令牌桶限流
"""

import os
import time
import random
import requests
from typing import Dict, Any, Optional, List
from datetime import datetime
import yaml


class TokenBucket:
    """令牌桶限流器"""
    
    def __init__(self, bucket_size: int = 100, refill_rate: float = 10.0):
        self.bucket_size = bucket_size
        self.refill_rate = refill_rate  # 每秒补充的令牌数
        self.tokens = bucket_size
        self.last_refill = time.time()
    
    def consume(self, tokens: int = 1) -> bool:
        """尝试消耗令牌"""
        self._refill()
        
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False
    
    def _refill(self):
        """补充令牌"""
        now = time.time()
        elapsed = now - self.last_refill
        new_tokens = elapsed * self.refill_rate
        
        self.tokens = min(self.bucket_size, self.tokens + new_tokens)
        self.last_refill = now


class LLMGateway:
    """多模态 LLM 统一网关"""
    
    def __init__(self, config_path: str = None):
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                'config', 'llm.yaml'
            )
        
        self.config = self._load_config(config_path)
        self.models = self.config.get('models', [])
        self.global_config = self.config.get('global', {})
        self.fallback_config = self.config.get('fallback', {})
        self.rate_limit_config = self.config.get('rate_limit', {})
        
        # 初始化令牌桶
        self.token_bucket = TokenBucket(
            bucket_size=self.rate_limit_config.get('bucket_size', 100),
            refill_rate=self.rate_limit_config.get('refill_rate', 10.0)
        )
        
        # 调用记录（用于统计和审计）
        self.call_history = []
    
    def _load_config(self, config_path: str) -> Dict:
        """加载 YAML 配置"""
        if not os.path.exists(config_path):
            return self._get_default_config()
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f'加载 LLM 配置失败：{e}')
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """返回默认配置"""
        return {
            'global': {
                'default_model': 'auto',
                'max_retries': 2,
                'timeout': 60
            },
            'models': [
                {
                    'id': 'deepseek',
                    'name': 'DeepSeek V3',
                    'base_url': 'https://api.deepseek.com/v1',
                    'api_key_env': 'DEEPSEEK_API_KEY',
                    'model_name': 'deepseek-chat',
                    'weight': 30,
                    'enabled': True
                }
            ],
            'fallback': {
                'order': ['deepseek'],
                'log_fallback': True
            }
        }
    
    def _get_api_key(self, env_var: str) -> Optional[str]:
        """从环境变量获取 API Key"""
        return os.environ.get(env_var)
    
    def _select_model(self, model_id: str = 'auto') -> Optional[Dict]:
        """根据策略选择模型"""
        enabled_models = [m for m in self.models if m.get('enabled', True)]
        
        if not enabled_models:
            return None
        
        # 指定模型 ID
        if model_id != 'auto':
            for model in enabled_models:
                if model['id'] == model_id:
                    return model
            # 指定的模型不可用，返回第一个可用模型
            return enabled_models[0] if enabled_models else None
        
        # 自动选择：按权重随机
        weights = [m.get('weight', 10) for m in enabled_models]
        total_weight = sum(weights)
        
        if total_weight == 0:
            return random.choice(enabled_models)
        
        rand = random.uniform(0, total_weight)
        cumulative = 0
        
        for i, model in enumerate(enabled_models):
            cumulative += weights[i]
            if rand <= cumulative:
                return model
        
        return enabled_models[-1]
    
    def _call_llm(
        self,
        model: Dict,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2048
    ) -> Dict[str, Any]:
        """调用单个 LLM 模型"""
        api_key = self._get_api_key(model['api_key_env'])
        
        if not api_key:
            return {
                'success': False,
                'error': f'API Key 未配置：{model["api_key_env"]}',
                'model': model['id']
            }
        
        base_url = model['base_url']
        model_name = model.get('model_name', 'default')
        
        # 构建请求头
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}'
        }
        
        # 特殊处理百度文心一言
        if model['id'] == 'ernie':
            return self._call_ernie(model, messages, temperature, max_tokens)
        
        # 标准 OpenAI 格式调用
        payload = {
            'model': model_name,
            'messages': messages,
            'temperature': temperature,
            'max_tokens': max_tokens
        }
        
        timeout = self.global_config.get('timeout', 60)
        
        try:
            response = requests.post(
                f'{base_url}/chat/completions',
                headers=headers,
                json=payload,
                timeout=timeout
            )
            
            if response.status_code != 200:
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}: {response.text}',
                    'model': model['id']
                }
            
            result = response.json()
            content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
            
            return {
                'success': True,
                'reply': content,
                'model': model['id'],
                'usage': result.get('usage', {}),
                'latency': response.elapsed.total_seconds()
            }
            
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': '请求超时',
                'model': model['id']
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e),
                'model': model['id']
            }
    
    def _call_ernie(
        self,
        model: Dict,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2048
    ) -> Dict[str, Any]:
        """调用百度文心一言（特殊格式）"""
        api_key = self._get_api_key(model['api_key_env'])
        
        if not api_key:
            return {
                'success': False,
                'error': f'API Key 未配置：{model["api_key_env"]}',
                'model': model['id']
            }
        
        # 文心一言使用不同的认证方式
        headers = {
            'Content-Type': 'application/json'
        }
        
        # 简单处理：将消息合并为 prompt
        prompt = '\n'.join([m.get('content', '') for m in messages])
        
        payload = {
            'messages': messages,
            'temperature': temperature,
            'max_output_tokens': max_tokens
        }
        
        timeout = self.global_config.get('timeout', 60)
        
        try:
            # 文心一言 endpoint 可能需要调整
            response = requests.post(
                f"{model['base_url']}/chat/completions",
                headers=headers,
                json=payload,
                timeout=timeout
            )
            
            if response.status_code != 200:
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}: {response.text}',
                    'model': model['id']
                }
            
            result = response.json()
            content = result.get('result', '') or result.get('choices', [{}])[0].get('message', {}).get('content', '')
            
            return {
                'success': True,
                'reply': content,
                'model': model['id'],
                'usage': result.get('usage', {}),
                'latency': response.elapsed.total_seconds()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'model': model['id']
            }
    
    def chat(
        self,
        prompt: str,
        model_id: str = 'auto',
        system_prompt: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        max_retries: int = None
    ) -> Dict[str, Any]:
        """
        统一聊天接口
        
        Args:
            prompt: 用户输入
            model_id: 模型 ID（'auto' 表示自动选择）
            system_prompt: 系统提示词
            temperature: 温度参数
            max_tokens: 最大生成长度
            max_retries: 最大重试次数
            
        Returns:
            {
                'success': bool,
                'reply': str,
                'model': str,
                'usage': dict,
                'latency': float,
                'is_fallback': bool
            }
        """
        start_time = time.time()
        
        # 限流检查
        if self.global_config.get('enable_rate_limit', True):
            if not self.token_bucket.consume():
                return {
                    'success': False,
                    'error': '请求频率过高，请稍后重试',
                    'model': 'rate_limited'
                }
        
        # 构建消息列表
        messages = []
        if system_prompt:
            messages.append({'role': 'system', 'content': system_prompt})
        messages.append({'role': 'user', 'content': prompt})
        
        # 选择初始模型
        current_model = self._select_model(model_id)
        
        if not current_model:
            return {
                'success': False,
                'error': '没有可用的模型',
                'model': 'none'
            }
        
        # 重试配置
        retries = max_retries or self.global_config.get('max_retries', 2)
        fallback_order = self.fallback_config.get('order', [])
        is_fallback = False
        attempted_models = []
        
        # 尝试调用（含重试和降级）
        for attempt in range(retries + 1):
            attempted_models.append(current_model['id'])
            
            result = self._call_llm(
                model=current_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            if result.get('success'):
                result['is_fallback'] = is_fallback
                result['attempted_models'] = attempted_models
                result['total_latency'] = time.time() - start_time
                
                # 记录调用历史
                self._record_call(prompt, result, current_model['id'])
                
                return result
            
            # 失败处理
            if attempt < retries and fallback_order:
                # 尝试降级到下一个模型
                next_model_id = None
                for mid in fallback_order:
                    if mid not in attempted_models:
                        next_model_id = mid
                        break
                
                if next_model_id:
                    current_model = self._select_model(next_model_id)
                    is_fallback = True
                    
                    if self.fallback_config.get('log_fallback', True):
                        print(f'模型降级：{current_model["id"]} -> {next_model_id}')
                else:
                    # 没有更多可降级的模型，重试当前模型
                    time.sleep(0.5 * (attempt + 1))  # 指数退避
            else:
                # 最后一次尝试或没有降级策略
                if attempt < retries:
                    time.sleep(0.5 * (attempt + 1))
        
        # 所有尝试都失败
        return {
            'success': False,
            'error': f'所有模型调用失败：{attempted_models}',
            'model': 'all_failed',
            'attempted_models': attempted_models,
            'total_latency': time.time() - start_time
        }
    
    def _record_call(self, prompt: str, result: Dict, model_id: str):
        """记录调用历史"""
        record = {
            'timestamp': datetime.utcnow().isoformat(),
            'prompt': prompt[:500],  # 截断避免过长
            'model': model_id,
            'success': result.get('success', False),
            'latency': result.get('latency', 0),
            'is_fallback': result.get('is_fallback', False)
        }
        
        self.call_history.append(record)
        
        # 保留最近 1000 条记录
        if len(self.call_history) > 1000:
            self.call_history = self.call_history[-1000:]
    
    def get_available_models(self) -> List[Dict]:
        """获取所有可用模型列表"""
        return [
            {
                'id': m['id'],
                'name': m['name'],
                'description': m.get('description', ''),
                'enabled': m.get('enabled', True)
            }
            for m in self.models
            if m.get('enabled', True)
        ]
    
    def get_call_statistics(self) -> Dict:
        """获取调用统计"""
        if not self.call_history:
            return {
                'total_calls': 0,
                'success_rate': 0,
                'avg_latency': 0,
                'model_distribution': {}
            }
        
        total = len(self.call_history)
        success = sum(1 for c in self.call_history if c['success'])
        avg_latency = sum(c['latency'] for c in self.call_history) / total if total > 0 else 0
        
        model_dist = {}
        for call in self.call_history:
            model = call['model']
            model_dist[model] = model_dist.get(model, 0) + 1
        
        return {
            'total_calls': total,
            'success_rate': success / total if total > 0 else 0,
            'avg_latency': avg_latency,
            'model_distribution': model_dist
        }


# 全局单例
_llm_gateway_instance = None


def get_llm_gateway() -> LLMGateway:
    """获取 LLMGateway 单例"""
    global _llm_gateway_instance
    if _llm_gateway_instance is None:
        _llm_gateway_instance = LLMGateway()
    return _llm_gateway_instance