"""
Playwright Runner - UI 自动化执行引擎
支持单步调试、批量执行、录屏截图、智能等待、失败重试
"""

import os
import json
import time
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from playwright.sync_api import sync_playwright, Page, Browser


class PlaywrightRunner:
    """Playwright 执行引擎 - 统一管理所有 UI 自动化任务"""
    
    def __init__(self):
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.default_timeout = 30000  # 30 秒
        self.retry_count = 3  # 失败重试次数
        self.retry_delay = 2  # 重试间隔（秒）
        
    def start_browser(self, headless: bool = True, video_path: Optional[str] = None):
        """启动浏览器"""
        self.playwright = sync_playwright().start()
        
        browser_options = {
            'headless': headless,
            'args': [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--disable-gpu'
            ]
        }
        
        if video_path:
            browser_options['record_video_dir'] = video_path
            browser_options['record_video_size'] = {'width': 1280, 'height': 720}
        
        self.browser = self.playwright.chromium.launch(**browser_options)
        return self.browser
    
    def close_browser(self):
        """关闭浏览器"""
        if self.page:
            self.page.close()
            self.page = None
        
        if self.browser:
            self.browser.close()
            self.browser = None
        
        if self.playwright:
            self.playwright.stop()
            self.playwright = None
    
    def create_page(self) -> Page:
        """创建新页面"""
        if not self.browser:
            raise RuntimeError('浏览器未启动')
        
        self.page = self.browser.new_page(
            viewport={'width': 1280, 'height': 720},
            timeout=self.default_timeout
        )
        return self.page
    
    def execute_step(self, step: Dict[str, Any], screenshot_path: Optional[str] = None) -> Dict[str, Any]:
        """
        执行单个测试步骤
        
        Args:
            step: 步骤配置，包含 action、locator、value 等
            screenshot_path: 截图保存路径（可选）
            
        Returns:
            {
                'success': bool,
                'action': str,
                'locator': str,
                'duration_ms': int,
                'error': str (optional),
                'screenshot': str (optional)
            }
        """
        start_time = time.time()
        action = step.get('action', '').lower()
        locator = step.get('locator', '')
        value = step.get('value', '')
        
        result = {
            'success': False,
            'action': action,
            'locator': locator,
            'duration_ms': 0
        }
        
        try:
            # 智能等待定位器（最多重试 3 次）
            element = None
            for attempt in range(self.retry_count):
                try:
                    element = self._find_element(locator)
                    if element:
                        break
                except Exception:
                    if attempt < self.retry_count - 1:
                        time.sleep(self.retry_delay * (attempt + 1))
                    else:
                        raise
            
            if not element and locator:
                raise Exception(f'找不到元素：{locator}')
            
            # 执行操作
            if action == 'click':
                if element:
                    element.click(timeout=5000)
                else:
                    self.page.click(locator, timeout=5000)
                    
            elif action == 'fill' or action == 'type':
                if element:
                    element.fill(value)
                else:
                    self.page.fill(locator, value)
                    
            elif action == 'press':
                self.page.keyboard.press(value)
                
            elif action == 'navigate' or action == 'goto':
                self.page.goto(value, wait_until='networkidle')
                
            elif action == 'wait':
                wait_time = float(value) if value else 1.0
                time.sleep(wait_time)
                
            elif action == 'assert_text':
                if element:
                    text = element.inner_text()
                else:
                    text = self.page.locator(locator).inner_text()
                if value not in text:
                    raise Exception(f'断言失败：期望包含 "{value}"，实际为 "{text}"')
                    
            elif action == 'assert_visible':
                if element:
                    assert element.is_visible()
                else:
                    assert self.page.locator(locator).is_visible()
                    
            elif action == 'scroll':
                self.page.evaluate(f'window.scrollBy(0, {value})')
                
            elif action == 'hover':
                if element:
                    element.hover()
                else:
                    self.page.hover(locator)
            
            result['success'] = True
            
            # 截图
            if screenshot_path:
                if element:
                    element.screenshot(path=screenshot_path)
                else:
                    self.page.screenshot(path=screenshot_path, full_page=True)
                result['screenshot'] = screenshot_path
                
        except Exception as e:
            result['error'] = str(e)
            result['success'] = False
            
            # 失败时自动截图
            if screenshot_path:
                try:
                    error_screenshot = screenshot_path.replace('.png', '_error.png')
                    self.page.screenshot(path=error_screenshot, full_page=True)
                    result['error_screenshot'] = error_screenshot
                except Exception:
                    pass
        
        result['duration_ms'] = int((time.time() - start_time) * 1000)
        return result
    
    def _find_element(self, locator: str):
        """智能查找元素，支持多种定位策略"""
        if not locator:
            return None
        
        # 尝试不同的定位策略
        strategies = [
            lambda: self.page.locator(locator).first,
            lambda: self.page.query_selector(locator),
        ]
        
        # 如果是文本定位器
        if locator.startswith('text='):
            text = locator[5:]
            strategies.insert(0, lambda: self.page.get_by_text(text).first)
        
        # 如果是角色定位器
        if locator.startswith('role='):
            role = locator[5:]
            strategies.insert(0, lambda: self.page.get_by_role(role).first)
        
        for strategy in strategies:
            try:
                element = strategy()
                if element and element.count() > 0:
                    return element.first
                elif element:
                    return element
            except Exception:
                continue
        
        return None
    
    def execute_job(self, job_data: Dict[str, Any], on_step_callback=None) -> Dict[str, Any]:
        """
        执行完整的自动化任务
        
        Args:
            job_data: 任务配置
            on_step_callback: 每步执行后的回调函数（用于 WebSocket 推送）
            
        Returns:
            {
                'success': bool,
                'total_steps': int,
                'passed_steps': int,
                'failed_steps': int,
                'results': list,
                'video_path': str,
                'screenshots': list
            }
        """
        results = []
        screenshots = []
        passed = 0
        failed = 0
        
        mode = job_data.get('mode', 'batch')
        steps = job_data.get('steps', [])
        video_path = job_data.get('video_path')
        screenshot_dir = job_data.get('screenshot_dir', 'static/screenshots')
        
        # 确保目录存在
        os.makedirs(screenshot_dir, exist_ok=True)
        
        try:
            # 启动浏览器
            self.start_browser(headless=(mode != 'single'), video_path=video_path)
            self.create_page()
            
            for idx, step in enumerate(steps):
                step_num = idx + 1
                screenshot_path = os.path.join(
                    screenshot_dir, 
                    f'step_{step_num}_{datetime.now().strftime("%Y%m%d%H%M%S")}.png'
                )
                
                # 执行步骤
                result = self.execute_step(step, screenshot_path)
                result['step_number'] = step_num
                results.append(result)
                
                if result['success']:
                    passed += 1
                    if result.get('screenshot'):
                        screenshots.append(result['screenshot'])
                else:
                    failed += 1
                
                # 回调通知（用于 WebSocket 推送）
                if on_step_callback:
                    on_step_callback({
                        'step_number': step_num,
                        'total_steps': len(steps),
                        'result': result,
                        'progress': int((step_num / len(steps)) * 100)
                    })
                
                # 单步模式：如果设置了断点，暂停等待继续指令
                if mode == 'single' and job_data.get('breakpoint', False):
                    # 这里可以通过 WebSocket 等待用户指令
                    time.sleep(0.5)  # 短暂延迟
            
            return {
                'success': failed == 0,
                'total_steps': len(steps),
                'passed_steps': passed,
                'failed_steps': failed,
                'results': results,
                'video_path': video_path,
                'screenshots': screenshots
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'total_steps': len(steps),
                'passed_steps': passed,
                'failed_steps': failed,
                'results': results,
                'screenshots': screenshots
            }
        
        finally:
            self.close_browser()


# 全局单例
_playwright_runner_instance: Optional[PlaywrightRunner] = None


def get_playwright_runner() -> PlaywrightRunner:
    """获取 PlaywrightRunner 单例"""
    global _playwright_runner_instance
    if _playwright_runner_instance is None:
        _playwright_runner_instance = PlaywrightRunner()
    return _playwright_runner_instance