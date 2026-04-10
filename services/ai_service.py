"""
AI Service - AI 能力服务层
封装多模型调用、用例生成、缺陷分析等智能功能
"""

import json
import requests
from datetime import datetime


class AIService:
    """AI 服务类 - 统一处理所有 AI 相关请求"""
    
    def __init__(self):
        self.CSDN_API_KEY = 'sk-ffpztriquewtxvay'
        self.CSDN_BASE_URL = 'https://models.csdn.net/v1/chat/completions'
        
        # 模型映射
        self.MODEL_MAPPING = {
            'qwen-plus': 'qwen-plus',
            'qwen-max': 'qwen-max',
            'deepseek-v3': 'deepseek-v3',
            'gpt-4o': 'gpt-4o-2024-08-06'
        }
    
    def _call_ai(self, model: str, messages: list, **kwargs) -> dict:
        """调用 AI 接口"""
        model_name = self.MODEL_MAPPING.get(model, model)
        
        payload = {
            'model': model_name,
            'messages': messages,
            'temperature': kwargs.get('temperature', 0.7),
            'top_p': kwargs.get('top_p', 0.7),
            'stream': kwargs.get('stream', False)
        }
        
        headers = {
            'Authorization': f'Bearer {self.CSDN_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.post(
                self.CSDN_BASE_URL,
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            
            return {
                'success': True,
                'content': result['choices'][0]['message']['content'],
                'model': model_name,
                'usage': result.get('usage', {})
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'model': model_name
            }
    
    def generate_test_cases(self, requirement: str, project_id: int, model: str = 'qwen-plus') -> dict:
        """
        根据需求生成测试用例
        
        Args:
            requirement: 需求描述
            project_id: 项目 ID
            model: AI 模型名称
            
        Returns:
            生成的测试用例列表
        """
        prompt = f"""
你是一个专业的测试工程师。请根据以下需求描述，生成完整的测试用例。

需求描述：
{requirement}

请按照以下 JSON 格式输出测试用例列表（仅输出 JSON，不要其他文字）：
{{
    "test_cases": [
        {{
            "title": "用例标题",
            "description": "用例描述",
            "steps": ["步骤 1", "步骤 2", "步骤 3"],
            "expected_result": "预期结果",
            "priority": "high"  // low, medium, high, critical
        }}
    ]
}}

要求：
1. 覆盖正常流程、异常流程、边界条件
2. 至少生成 5 个测试用例
3. 步骤要具体可执行
4. 优先级分配合理
"""
        
        messages = [
            {'role': 'system', 'content': '你是专业的测试工程师，擅长编写高质量的测试用例'},
            {'role': 'user', 'content': prompt}
        ]
        
        result = self._call_ai(model, messages)
        
        if result['success']:
            try:
                # 解析 AI 返回的 JSON
                content = result['content']
                # 清理可能的 markdown 标记
                if content.startswith('```json'):
                    content = content[7:]
                if content.endswith('```'):
                    content = content[:-3]
                
                test_cases_data = json.loads(content.strip())
                return {
                    'success': True,
                    'test_cases': test_cases_data.get('test_cases', []),
                    'model': result['model']
                }
            except json.JSONDecodeError as e:
                return {
                    'success': False,
                    'error': f'JSON 解析失败：{str(e)}',
                    'raw_content': result['content']
                }
        else:
            return result
    
    def analyze_defect(self, defect_description: str, logs: str = '', screenshot: str = '') -> dict:
        """
        AI 分析缺陷
        
        Args:
            defect_description: 缺陷描述
            logs: 相关日志
            screenshot: 截图描述（暂不支持图片上传）
            
        Returns:
            分析结果：严重程度、可能原因、修复建议
        """
        prompt = f"""
你是一个资深的 QA 专家。请分析以下缺陷信息：

缺陷描述：
{defect_description}

相关日志：
{logs if logs else '无'}

请按照以下 JSON 格式输出分析结果（仅输出 JSON）：
{{
    "severity": "high",  // low, medium, high, critical
    "root_cause": "可能的根本原因",
    "suggestion": "详细的修复建议",
    "similar_issues": ["类似问题 1", "类似问题 2"],
    "test_scenarios": ["需要补充的测试场景 1", "场景 2"]
}}
"""
        
        messages = [
            {'role': 'system', 'content': '你是资深的 QA 专家，擅长缺陷分析和根因定位'},
            {'role': 'user', 'content': prompt}
        ]
        
        result = self._call_ai('qwen-plus', messages)
        
        if result['success']:
            try:
                content = result['content']
                if content.startswith('```json'):
                    content = content[7:]
                if content.endswith('```'):
                    content = content[:-3]
                
                analysis = json.loads(content.strip())
                return {
                    'success': True,
                    'severity': analysis.get('severity', 'medium'),
                    'root_cause': analysis.get('root_cause', ''),
                    'suggestion': analysis.get('suggestion', ''),
                    'similar_issues': analysis.get('similar_issues', []),
                    'test_scenarios': analysis.get('test_scenarios', [])
                }
            except json.JSONDecodeError:
                return {
                    'success': True,
                    'severity': 'medium',
                    'suggestion': result['content'],
                    'raw_analysis': result['content']
                }
        else:
            return result
    
    def optimize_test_script(self, script: str, language: str = 'python') -> dict:
        """
        优化测试脚本
        
        Args:
            script: 原始脚本代码
            language: 编程语言
            
        Returns:
            优化后的脚本和建议
        """
        prompt = f"""
你是一个资深测试开发工程师。请优化以下{language}测试脚本：

原始脚本：
```{language}
{script}
```

请按照以下 JSON 格式输出优化结果：
{{
    "optimized_code": "优化后的完整代码",
    "improvements": ["改进点 1", "改进点 2"],
    "best_practices": ["最佳实践建议 1", "建议 2"],
    "potential_issues": ["潜在问题 1", "问题 2"]
}}
"""
        
        messages = [
            {'role': 'system', 'content': f'你是资深测试开发工程师，精通{language}测试框架和最佳实践'},
            {'role': 'user', 'content': prompt}
        ]
        
        result = self._call_ai('qwen-plus', messages)
        
        if result['success']:
            try:
                content = result['content']
                if content.startswith('```json'):
                    content = content[7:]
                if content.endswith('```'):
                    content = content[:-3]
                
                optimization = json.loads(content.strip())
                return {
                    'success': True,
                    'optimized_code': optimization.get('optimized_code', script),
                    'improvements': optimization.get('improvements', []),
                    'best_practices': optimization.get('best_practices', []),
                    'potential_issues': optimization.get('potential_issues', [])
                }
            except json.JSONDecodeError:
                return {
                    'success': True,
                    'optimized_code': script,
                    'suggestions': result['content']
                }
        else:
            return result