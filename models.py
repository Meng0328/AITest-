"""
数据库模型 - 定义所有业务实体
支持项目、测试用例、执行记录、缺陷、用户等核心数据
"""

from datetime import datetime
from extensions import db
import json


class Project(db.Model):
    """项目表"""
    __tablename__ = 'projects'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联
    test_cases = db.relationship('TestCase', backref='project', lazy='dynamic', cascade='all, delete-orphan')
    executions = db.relationship('TestExecution', backref='project', lazy='dynamic', cascade='all, delete-orphan')
    defects = db.relationship('Defect', backref='project', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'test_cases_count': self.test_cases.count(),
            'executions_count': self.executions.count(),
            'defects_count': self.defects.count()
        }


class User(db.Model):
    """用户表 - 支持协作功能"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100))
    role = db.Column(db.String(20), default='member')  # admin, member, viewer
    avatar = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_active = db.Column(db.DateTime)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'avatar': self.avatar,
            'last_active': self.last_active.isoformat() if self.last_active else None
        }


class TestCase(db.Model):
    """测试用例表"""
    __tablename__ = 'test_cases'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    steps = db.Column(db.Text)  # JSON 字符串存储步骤列表
    expected_result = db.Column(db.Text)
    priority = db.Column(db.String(20), default='medium')  # low, medium, high, critical
    status = db.Column(db.String(20), default='draft')  # draft, active, deprecated
    ai_generated = db.Column(db.Boolean, default=False)
    ai_model = db.Column(db.String(50))
    created_by = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联
    executions = db.relationship('TestExecution', secondary='execution_test_cases', backref='test_cases')
    defects = db.relationship('Defect', backref='test_case', lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'title': self.title,
            'description': self.description,
            'steps': json.loads(self.steps) if self.steps else [],
            'expected_result': self.expected_result,
            'priority': self.priority,
            'status': self.status,
            'ai_generated': self.ai_generated,
            'ai_model': self.ai_model,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class TestExecution(db.Model):
    """测试执行记录表"""
    __tablename__ = 'test_executions'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    test_case_ids = db.Column(db.Text)  # JSON 字符串存储用例 ID 列表
    executor = db.Column(db.String(50))
    environment = db.Column(db.String(50), default='local')  # local, staging, production
    status = db.Column(db.String(20), default='running')  # running, passed, failed, error
    progress = db.Column(db.Integer, default=0)  # 0-100
    result = db.Column(db.Text)  # JSON 字符串存储详细结果
    log = db.Column(db.Text)  # 执行日志
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'test_case_ids': json.loads(self.test_case_ids) if self.test_case_ids else [],
            'executor': self.executor,
            'environment': self.environment,
            'status': self.status,
            'progress': self.progress,
            'result': json.loads(self.result) if self.result else None,
            'log': self.log,
            'started_at': self.started_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'duration': self._calculate_duration()
        }
    
    def _calculate_duration(self):
        if self.completed_at and self.started_at:
            delta = self.completed_at - self.started_at
            return delta.total_seconds()
        return None


# 多对多关联表：执行记录 - 测试用例
execution_test_cases = db.Table('execution_test_cases',
    db.Column('execution_id', db.Integer, db.ForeignKey('test_executions.id'), primary_key=True),
    db.Column('test_case_id', db.Integer, db.ForeignKey('test_cases.id'), primary_key=True)
)


class Defect(db.Model):
    """缺陷表"""
    __tablename__ = 'defects'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    test_case_id = db.Column(db.Integer, db.ForeignKey('test_cases.id'))
    execution_id = db.Column(db.Integer, db.ForeignKey('test_executions.id'))
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    severity = db.Column(db.String(20), default='medium')  # low, medium, high, critical
    status = db.Column(db.String(20), default='new')  # new, confirmed, in_progress, resolved, closed, rejected
    assignee = db.Column(db.String(50))
    resolution = db.Column(db.Text)
    ai_analyzed = db.Column(db.Boolean, default=False)
    ai_suggestion = db.Column(db.Text)
    created_by = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'test_case_id': self.test_case_id,
            'execution_id': self.execution_id,
            'title': self.title,
            'description': self.description,
            'severity': self.severity,
            'status': self.status,
            'assignee': self.assignee,
            'resolution': self.resolution,
            'ai_analyzed': self.ai_analyzed,
            'ai_suggestion': self.ai_suggestion,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class CollaborationSession(db.Model):
    """协作文会话表 - 记录实时协作状态"""
    __tablename__ = 'collaboration_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    session_id = db.Column(db.String(100), unique=True)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_heartbeat = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    user = db.relationship('User', backref='sessions')
    
    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'joined_at': self.joined_at.isoformat(),
            'last_heartbeat': self.last_heartbeat.isoformat(),
            'is_active': self.is_active,
            'user': self.user.to_dict() if self.user else None
        }


class TestResult(db.Model):
    """测试结果表 - 记录每个测试步骤的执行结果"""
    __tablename__ = 'test_results'
    
    id = db.Column(db.Integer, primary_key=True)
    test_run_id = db.Column(db.Integer, db.ForeignKey('test_executions.id'), nullable=False)
    test_case_id = db.Column(db.Integer, db.ForeignKey('test_cases.id'))
    step_number = db.Column(db.Integer)  # 步骤序号
    action = db.Column(db.String(200))  # 操作描述
    locator = db.Column(db.Text)  # JSON 字符串存储定位器信息
    status = db.Column(db.String(20), default='pending')  # pending, passed, failed, skipped
    error_message = db.Column(db.Text)
    screenshot_path = db.Column(db.String(500))
    duration_ms = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关联
    test_run = db.relationship('TestExecution', backref='results')
    test_case = db.relationship('TestCase', backref='results')
    
    def to_dict(self):
        return {
            'id': self.id,
            'test_run_id': self.test_run_id,
            'test_case_id': self.test_case_id,
            'step_number': self.step_number,
            'action': self.action,
            'locator': json.loads(self.locator) if self.locator else None,
            'status': self.status,
            'error_message': self.error_message,
            'screenshot_path': self.screenshot_path,
            'duration_ms': self.duration_ms,
            'created_at': self.created_at.isoformat()
        }


class CaseHistory(db.Model):
    """测试用例历史版本表 - 支持 diff 与回滚"""
    __tablename__ = 'case_histories'
    
    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey('test_cases.id'), nullable=False)
    version = db.Column(db.Integer, nullable=False)  # 版本号，自增
    content = db.Column(db.Text, nullable=False)  # JSON 字符串存储完整用例内容
    prompt = db.Column(db.Text)  # 生成该版本的原始 prompt
    model = db.Column(db.String(50))  # 使用的 AI 模型
    creator = db.Column(db.String(50))  # 创建者
    change_summary = db.Column(db.Text)  # 变更摘要
    is_deleted = db.Column(db.Boolean, default=False)  # 软删除标记
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关联
    test_case = db.relationship('TestCase', backref='histories')
    
    def to_dict(self):
        return {
            'id': self.id,
            'case_id': self.case_id,
            'version': self.version,
            'content': json.loads(self.content) if self.content else {},
            'prompt': self.prompt,
            'model': self.model,
            'creator': self.creator,
            'change_summary': self.change_summary,
            'is_deleted': self.is_deleted,
            'created_at': self.created_at.isoformat()
        }


class Activity(db.Model):
    """活动记录表 - 记录所有用户操作，支持协作审计"""
    __tablename__ = 'activities'
    
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(50), nullable=False)  # 用户名
    action = db.Column(db.String(50), nullable=False)  # 操作类型：create/update/delete/execute/generate
    resource_type = db.Column(db.String(50))  # 资源类型：project/case/execution/defect
    resource_id = db.Column(db.Integer)  # 资源 ID
    details = db.Column(db.Text)  # JSON 字符串存储详细信息
    ip_address = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user': self.user,
            'action': self.action,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'details': json.loads(self.details) if self.details else {},
            'ip_address': self.ip_address,
            'created_at': self.created_at.isoformat()
        }


class AutoJob(db.Model):
    """UI 自动化执行任务表 - 支持单步调试与批量执行"""
    __tablename__ = 'auto_jobs'
    
    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey('test_cases.id'), nullable=False)
    mode = db.Column(db.String(20), default='batch')  # single/batch
    breakpoint = db.Column(db.Boolean, default=False)  # 是否断点模式
    steps = db.Column(db.Text)  # JSON 字符串存储执行步骤
    status = db.Column(db.String(20), default='pending')  # pending/running/paused/completed/failed
    current_step = db.Column(db.Integer, default=0)  # 当前执行到的步骤
    result = db.Column(db.Text)  # JSON 字符串存储执行结果
    video_path = db.Column(db.String(500))  # 录屏文件路径
    screenshot_paths = db.Column(db.Text)  # JSON 字符串存储截图路径列表
    executor = db.Column(db.String(50))
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关联
    test_case = db.relationship('TestCase', backref='auto_jobs')
    
    def to_dict(self):
        return {
            'id': self.id,
            'case_id': self.case_id,
            'mode': self.mode,
            'breakpoint': self.breakpoint,
            'steps': json.loads(self.steps) if self.steps else [],
            'status': self.status,
            'current_step': self.current_step,
            'result': json.loads(self.result) if self.result else None,
            'video_path': self.video_path,
            'screenshot_paths': json.loads(self.screenshot_paths) if self.screenshot_paths else [],
            'executor': self.executor,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'created_at': self.created_at.isoformat()
        }


class LocatorStats(db.Model):
    """元素定位器统计表 - 用于稳定性评分"""
    __tablename__ = 'locator_stats'
    
    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey('test_cases.id'), nullable=False)
    step_number = db.Column(db.Integer)  # 步骤序号
    locator = db.Column(db.Text, nullable=False)  # 定位器表达式
    total_attempts = db.Column(db.Integer, default=0)  # 总尝试次数
    success_count = db.Column(db.Integer, default=0)  # 成功次数
    avg_duration_ms = db.Column(db.Integer, default=0)  # 平均耗时
    last_used_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联
    test_case = db.relationship('TestCase', backref='locator_stats')
    
    def to_dict(self):
        score = (self.success_count + 1) / (self.total_attempts + 2) * 100 if self.total_attempts > 0 else 100
        return {
            'id': self.id,
            'case_id': self.case_id,
            'step_number': self.step_number,
            'locator': self.locator,
            'total_attempts': self.total_attempts,
            'success_count': self.success_count,
            'score': round(score, 2),
            'avg_duration_ms': self.avg_duration_ms,
            'last_used_at': self.last_used_at.isoformat() if self.last_used_at else None,
            'updated_at': self.updated_at.isoformat()
        }


class ActivityLog(db.Model):
    """活动日志表 - 记录所有用户操作，支持协作审计"""
    __tablename__ = 'activity_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(50), nullable=False)  # 用户名
    action = db.Column(db.String(50), nullable=False)  # 操作类型
    resource_type = db.Column(db.String(50))  # 资源类型：project/case/execution/defect
    resource_id = db.Column(db.Integer)  # 资源 ID
    details = db.Column(db.Text)  # JSON 字符串存储详细信息
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user': self.user,
            'action': self.action,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'details': json.loads(self.details) if self.details else {},
            'created_at': self.created_at.isoformat()
        }


class CollaborationLock(db.Model):
    """协作文锁表 - 防止多人同时编辑同一资源"""
    __tablename__ = 'collaboration_locks'
    
    id = db.Column(db.Integer, primary_key=True)
    resource_type = db.Column(db.String(50), nullable=False)  # case/defect/project
    resource_id = db.Column(db.Integer, nullable=False)  # 资源 ID
    user = db.Column(db.String(50), nullable=False)  # 锁定者
    locked_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_heartbeat = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'user': self.user,
            'locked_at': self.locked_at.isoformat(),
            'last_heartbeat': self.last_heartbeat.isoformat(),
            'is_active': self.is_active
        }