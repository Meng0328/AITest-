"""
API 路由模块 - 统一处理所有业务接口
支持 AI 用例生成、UI 自动化、缺陷分析、报告导出等功能
"""

from flask import Blueprint, request, jsonify, send_file
from extensions import db, socketio
from models import TestCase, TestExecution, Defect, Project
from datetime import datetime
import json
import os

# 别名兼容
TestRun = TestExecution

api = Blueprint('api', __name__, url_prefix='/api')


# ==================== 项目管理 ====================

@api.route('/projects', methods=['GET'])
def get_projects():
    """获取所有项目"""
    projects = Project.query.all()
    return jsonify([{
        'id': p.id,
        'name': p.name,
        'description': p.description,
        'created_at': p.created_at.isoformat(),
        'updated_at': p.updated_at.isoformat()
    } for p in projects])


@api.route('/projects', methods=['POST'])
def create_project():
    """创建新项目"""
    data = request.json
    project = Project(
        name=data['name'],
        description=data.get('description', '')
    )
    db.session.add(project)
    db.session.commit()
    
    socketio.emit('project_created', {'project': project.to_dict()}, namespace='/collaboration')
    return jsonify(project.to_dict()), 201


# ==================== 测试用例管理 ====================

@api.route('/test-cases', methods=['GET'])
def get_test_cases():
    """获取测试用例列表，支持项目过滤"""
    project_id = request.args.get('project_id')
    query = TestCase.query
    
    if project_id:
        query = query.filter_by(project_id=project_id)
    
    test_cases = query.order_by(TestCase.created_at.desc()).all()
    return jsonify([tc.to_dict() for tc in test_cases])


@api.route('/test-cases', methods=['POST'])
def create_test_case():
    """创建测试用例（支持 AI 生成）"""
    data = request.json
    test_case = TestCase(
        project_id=data['project_id'],
        title=data['title'],
        description=data.get('description', ''),
        steps=json.dumps(data.get('steps', [])),
        expected_result=data.get('expected_result', ''),
        priority=data.get('priority', 'medium'),
        ai_generated=data.get('ai_generated', False),
        ai_model=data.get('ai_model', '')
    )
    db.session.add(test_case)
    db.session.commit()
    
    socketio.emit('test_case_created', {
        'test_case': test_case.to_dict(),
        'user': data.get('user', 'system')
    }, namespace='/collaboration')
    
    return jsonify(test_case.to_dict()), 201


@api.route('/test-cases/<int:case_id>', methods=['PUT'])
def update_test_case(case_id):
    """更新测试用例"""
    test_case = TestCase.query.get_or_404(case_id)
    data = request.json
    
    test_case.title = data.get('title', test_case.title)
    test_case.description = data.get('description', test_case.description)
    test_case.steps = json.dumps(data.get('steps', json.loads(test_case.steps)))
    test_case.expected_result = data.get('expected_result', test_case.expected_result)
    test_case.priority = data.get('priority', test_case.priority)
    test_case.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    socketio.emit('test_case_updated', {'test_case': test_case.to_dict()}, namespace='/collaboration')
    return jsonify(test_case.to_dict())


@api.route('/test-cases/<int:case_id>', methods=['DELETE'])
def delete_test_case(case_id):
    """删除测试用例"""
    test_case = TestCase.query.get_or_404(case_id)
    db.session.delete(test_case)
    db.session.commit()
    
    socketio.emit('test_case_deleted', {'case_id': case_id}, namespace='/collaboration')
    return jsonify({'message': '删除成功'})


# ==================== 测试执行 ====================

@api.route('/test-runs', methods=['GET'])
def get_test_runs():
    """获取执行记录"""
    project_id = request.args.get('project_id')
    query = TestRun.query
    
    if project_id:
        query = query.filter_by(project_id=project_id)
    
    executions = query.order_by(TestRun.created_at.desc()).limit(50).all()
    return jsonify([e.to_dict() for e in executions])


@api.route('/test-runs', methods=['POST'])
def create_test_run():
    """创建测试执行记录"""
    data = request.json
    execution = TestRun(
        project_id=data['project_id'],
        name=data.get('name', f'Test Run {datetime.now().strftime("%Y%m%d%H%M%S")}'),
        test_type=data.get('test_type', 'ui'),
        total_cases=data.get('total_cases', 0),
        status='pending'
    )
    db.session.add(execution)
    db.session.commit()
    
    socketio.emit('test_run_created', {'test_run': execution.to_dict()}, broadcast=True)
    return jsonify(execution.to_dict()), 201


@api.route('/test-runs/<int:exec_id>/status', methods=['PUT'])
def update_test_run_status(exec_id):
    """更新执行状态（用于实时进度推送）"""
    execution = TestRun.query.get_or_404(exec_id)
    data = request.json
    
    execution.status = data.get('status', execution.status)
    execution.progress = data.get('progress', execution.progress)
    execution.result = data.get('result', execution.result)
    execution.log = data.get('log', execution.log)
    
    if data.get('status') in ['passed', 'failed', 'error']:
        execution.completed_at = datetime.utcnow()
    
    db.session.commit()
    
    socketio.emit('test_run_progress', {
        'test_run_id': exec_id,
        'status': execution.status,
        'progress': execution.progress if hasattr(execution, 'progress') else 0
    }, broadcast=True)
    
    return jsonify(execution.to_dict())


# ==================== 缺陷管理 ====================

@api.route('/defects', methods=['GET'])
def get_defects():
    """获取缺陷列表"""
    project_id = request.args.get('project_id')
    status = request.args.get('status')
    query = Defect.query
    
    if project_id:
        query = query.filter_by(project_id=project_id)
    if status:
        query = query.filter_by(status=status)
    
    defects = query.order_by(Defect.created_at.desc()).all()
    return jsonify([d.to_dict() for d in defects])


@api.route('/defects', methods=['POST'])
def create_defect():
    """创建缺陷记录（支持 AI 分析生成）"""
    data = request.json
    defect = Defect(
        project_id=data['project_id'],
        title=data['title'],
        description=data.get('description', ''),
        severity=data.get('severity', 'medium'),
        status=data.get('status', 'new'),
        execution_id=data.get('execution_id'),
        test_case_id=data.get('test_case_id'),
        ai_analyzed=data.get('ai_analyzed', False),
        ai_suggestion=data.get('ai_suggestion', '')
    )
    db.session.add(defect)
    db.session.commit()
    
    socketio.emit('defect_created', {'defect': defect.to_dict()}, namespace='/collaboration')
    return jsonify(defect.to_dict()), 201


@api.route('/defects/<int:defect_id>', methods=['PUT'])
def update_defect(defect_id):
    """更新缺陷状态"""
    defect = Defect.query.get_or_404(defect_id)
    data = request.json
    
    defect.status = data.get('status', defect.status)
    defect.assignee = data.get('assignee', defect.assignee)
    defect.resolution = data.get('resolution', defect.resolution)
    defect.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    socketio.emit('defect_updated', {'defect': defect.to_dict()}, namespace='/collaboration')
    return jsonify(defect.to_dict())


# ==================== 报告导出 ====================

@api.route('/reports/export/<int:exec_id>', methods=['GET'])
def export_report(exec_id):
    """导出测试报告（支持 Excel/PDF 格式）"""
    from services.report_service import ReportService
    
    execution = TestRun.query.get_or_404(exec_id)
    format_type = request.args.get('format', 'excel')
    
    report_service = ReportService()
    
    if format_type == 'excel':
        file_path = report_service.export_to_excel(execution)
        return send_file(file_path, as_attachment=True, download_name=f'report_{exec_id}.xlsx')
    elif format_type == 'pdf':
        file_path = report_service.export_to_pdf(execution)
        return send_file(file_path, as_attachment=True, download_name=f'report_{exec_id}.pdf')
    else:
        return jsonify({'error': '不支持的格式'}), 400


# ==================== 用例版本管理 ====================

@api.route('/test-cases/<int:case_id>/history', methods=['GET'])
def get_case_history(case_id):
    """获取测试用例的历史版本列表"""
    from models import CaseHistory
    
    version = request.args.get('v', type=int)  # 可选：获取指定版本
    
    if version:
        # 获取指定版本
        history = CaseHistory.query.filter_by(
            case_id=case_id, 
            version=version,
            is_deleted=False
        ).first_or_404()
        return jsonify(history.to_dict())
    else:
        # 获取所有版本列表
        histories = CaseHistory.query.filter_by(
            case_id=case_id,
            is_deleted=False
        ).order_by(CaseHistory.version.desc()).all()
        
        return jsonify([{
            'id': h.id,
            'version': h.version,
            'creator': h.creator,
            'model': h.model,
            'change_summary': h.change_summary,
            'created_at': h.created_at.isoformat()
        } for h in histories])


@api.route('/test-cases/<int:case_id>/history', methods=['POST'])
def create_case_history(case_id):
    """创建测试用例历史版本（在生成或更新时自动调用）"""
    from models import CaseHistory, TestCase
    
    data = request.json
    test_case = TestCase.query.get_or_404(case_id)
    
    # 获取当前最大版本号
    max_version = db.session.query(db.func.max(CaseHistory.version)).filter_by(
        case_id=case_id,
        is_deleted=False
    ).scalar() or 0
    
    # 创建新版本
    history = CaseHistory(
        case_id=case_id,
        version=max_version + 1,
        content=json.dumps(test_case.to_dict()),
        prompt=data.get('prompt', ''),
        model=data.get('model', ''),
        creator=data.get('creator', 'system'),
        change_summary=data.get('change_summary', f'版本 {max_version + 1}')
    )
    
    db.session.add(history)
    db.session.commit()
    
    return jsonify(history.to_dict()), 201


# ==================== UI 自动化执行 ====================

@api.route('/auto/run', methods=['POST'])
def run_automation():
    """执行 UI 自动化任务（支持单步调试与批量执行）"""
    from services.playwright_runner import PlaywrightRunner
    from models import TestExecution, TestCase
    
    data = request.json
    case_id = data.get('case_id')
    mode = data.get('mode', 'batch')  # single/batch
    breakpoint = data.get('breakpoint', False)
    
    if not case_id:
        return jsonify({'success': False, 'error': '缺少用例 ID'}), 400
    
    # 获取测试用例
    test_case = TestCase.query.get_or_404(case_id)
    steps = json.loads(test_case.steps) if test_case.steps else []
    
    if not steps:
        return jsonify({'success': False, 'error': '用例没有定义步骤'}), 400
    
    # 创建执行记录
    execution = TestExecution(
        project_id=test_case.project_id,
        test_case_ids=json.dumps([case_id]),
        status='running',
        progress=0
    )
    db.session.add(execution)
    db.session.commit()
    
    # 准备任务配置
    job_data = {
        'mode': mode,
        'breakpoint': breakpoint,
        'steps': steps,
        'video_path': f'static/videos/{execution.id}_{datetime.now().strftime("%Y%m%d%H%M%S")}',
        'screenshot_dir': f'static/screenshots/{execution.id}'
    }
    
    # 定义回调函数（用于 WebSocket 推送）
    def on_step_callback(step_info):
        socketio.emit('auto:step', {
            'execution_id': execution.id,
            'step_number': step_info['step_number'],
            'total_steps': step_info['total_steps'],
            'result': step_info['result'],
            'progress': step_info['progress']
        }, broadcast=True)
        
        # 更新执行记录进度
        execution.progress = step_info['progress']
        db.session.commit()
    
    # 执行任务（在新线程中运行，避免阻塞）
    import threading
    
    def run_job():
        runner = PlaywrightRunner()
        result = runner.execute_job(job_data, on_step_callback=on_step_callback)
        
        # 更新执行记录状态
        execution.status = 'passed' if result['success'] else 'failed'
        execution.result = json.dumps(result)
        execution.completed_at = datetime.utcnow()
        db.session.commit()
        
        # 发送完成通知
        socketio.emit('auto:complete', {
            'execution_id': execution.id,
            'success': result['success'],
            'passed_steps': result.get('passed_steps', 0),
            'failed_steps': result.get('failed_steps', 0)
        }, broadcast=True)
    
    thread = threading.Thread(target=run_job)
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'success': True,
        'execution_id': execution.id,
        'message': '任务已启动'
    })


@api.route('/auto/stop/<int:execution_id>', methods=['POST'])
def stop_automation(execution_id):
    """停止正在执行的自动化任务"""
    execution = TestExecution.query.get_or_404(execution_id)
    
    if execution.status not in ['running']:
        return jsonify({'success': False, 'error': '任务未在执行中'}), 400
    
    execution.status = 'cancelled'
    execution.completed_at = datetime.utcnow()
    db.session.commit()
    
    socketio.emit('auto:stopped', {'execution_id': execution_id}, broadcast=True)
    
    return jsonify({'success': True, 'message': '任务已停止'})


@api.route('/auto/status/<int:execution_id>', methods=['GET'])
def get_automation_status(execution_id):
    """获取自动化任务状态"""
    execution = TestExecution.query.get_or_404(execution_id)
    
    result_data = json.loads(execution.result) if execution.result else None
    
    return jsonify({
        'success': True,
        'execution_id': execution_id,
        'status': execution.status,
        'progress': execution.progress,
        'started_at': execution.started_at.isoformat(),
        'completed_at': execution.completed_at.isoformat() if execution.completed_at else None,
        'result': result_data
    })


# ==================== 元素稳定性评分 ====================

@api.route('/locator/rank', methods=['GET'])
def rank_locators():
    """获取定位器稳定性评分"""
    from models import TestResult
    from sqlalchemy import func
    
    case_id = request.args.get('case_id', type=int)
    
    query = db.session.query(
        TestResult.locator,
        func.count(TestResult.id).label('total'),
        func.sum(func.case((TestResult.status == 'passed', 1), else_=0)).label('passed')
    ).filter(
        TestResult.locator.isnot(None)
    )
    
    if case_id:
        query = query.filter(TestResult.test_case_id == case_id)
    
    query = query.group_by(TestResult.locator).having(func.count(TestResult.id) >= 1)
    
    results = query.all()
    
    rankings = []
    for locator, total, passed in results:
        score = (passed + 1) / (total + 2) * 100  # 平滑公式
        rankings.append({
            'locator': json.loads(locator) if locator else None,
            'total_executions': total,
            'passed_count': int(passed),
            'score': round(score, 2)
        })
    
    # 按分数降序排序
    rankings.sort(key=lambda x: x['score'], reverse=True)
    
    return jsonify({
        'success': True,
        'rankings': rankings
    })


@api.route('/locator/fix', methods=['POST'])
def fix_locator():
    """一键修复不稳定的定位器"""
    from services.ai_service import AIService
    from services.llm_gateway import get_llm_gateway
    
    data = request.json
    old_locator = data.get('locator', '')
    page_context = data.get('page_context', '')
    error_message = data.get('error_message', '')
    
    if not old_locator:
        return jsonify({'success': False, 'error': '缺少定位器信息'}), 400
    
    # 调用 AI 优化定位器
    llm_gateway = get_llm_gateway()
    prompt = f"""请优化以下 Selenium/Playwright 元素定位器：

当前定位器：{old_locator}
页面上下文：{page_context}
错误信息：{error_message}

请提供：
1. 更稳定的定位策略（优先 CSS，其次 text，最后 xpath）
2. 至少 2 个备选方案
3. 优化建议

请以 JSON 格式返回：{{"optimized": "", "alternatives": [], "suggestions": []}}"""
    
    result = llm_gateway.chat(prompt, model='auto')
    
    try:
        optimization = json.loads(result.get('reply', '{}'))
        return jsonify({
            'success': True,
            'optimization': optimization
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'AI 解析失败',
            'raw_response': result.get('reply')
        })


# ==================== 实时协作 ====================

@api.route('/activity/log', methods=['POST'])
def log_activity():
    """记录用户操作日志"""
    from models import ActivityLog
    
    data = request.json
    
    activity = ActivityLog(
        user=data.get('user', 'anonymous'),
        action=data['action'],
        resource_type=data.get('resource_type'),
        resource_id=data.get('resource_id'),
        details=json.dumps(data.get('details', {}))
    )
    
    db.session.add(activity)
    db.session.commit()
    
    # WebSocket 广播
    socketio.emit('activity:new', {
        'user': activity.user,
        'action': activity.action,
        'timestamp': activity.created_at.isoformat()
    }, broadcast=True)
    
    return jsonify(activity.to_dict()), 201


@api.route('/activity/list', methods=['GET'])
def list_activities():
    """获取活动日志列表"""
    from models import ActivityLog
    
    limit = request.args.get('limit', 50, type=int)
    user = request.args.get('user')
    
    query = ActivityLog.query.order_by(ActivityLog.created_at.desc())
    
    if user:
        query = query.filter_by(user=user)
    
    activities = query.limit(limit).all()
    
    return jsonify([a.to_dict() for a in activities])


@api.route('/activity/export', methods=['GET'])
def export_activities():
    """导出活动日志为 CSV"""
    from models import ActivityLog
    import csv
    import io
    
    user = request.args.get('user')
    
    query = ActivityLog.query.order_by(ActivityLog.created_at.asc())
    if user:
        query = query.filter_by(user=user)
    
    activities = query.all()
    
    # 生成 CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['时间', '用户', '操作', '资源类型', '资源 ID', '详情'])
    
    for activity in activities:
        writer.writerow([
            activity.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            activity.user,
            activity.action,
            activity.resource_type,
            activity.resource_id,
            activity.details
        ])
    
    output.seek(0)
    
    from flask import make_response
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename=activities_{datetime.now().strftime("%Y%m%d")}.csv'
    
    return response


# ==================== 报告导出增强 ====================

@api.route('/reports/generate', methods=['POST'])
def generate_report():
    """生成测试报告（支持 PDF/HTML/Markdown）"""
    from services.report_service import ReportService
    
    data = request.json
    execution_id = data.get('execution_id')
    format_type = data.get('format', 'pdf')  # pdf/html/md
    
    if not execution_id:
        return jsonify({'success': False, 'error': '缺少执行记录 ID'}), 400
    
    execution = TestExecution.query.get_or_404(execution_id)
    report_service = ReportService()
    
    try:
        if format_type == 'pdf':
            filepath = report_service.export_to_pdf(execution)
        elif format_type == 'html':
            filepath = report_service.export_to_html(execution)
        elif format_type == 'md':
            filepath = report_service.export_to_markdown(execution)
        else:
            return jsonify({'success': False, 'error': '不支持的格式'}), 400
        
        filename = os.path.basename(filepath)
        
        return jsonify({
            'success': True,
            'filepath': filepath,
            'download_url': f'/api/reports/download/{filename}',
            'format': format_type
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api.route('/reports/download/<filename>', methods=['GET'])
def download_report(filename):
    """下载报告文件"""
    from services.report_service import ReportService
    
    report_service = ReportService()
    filepath = os.path.join(report_service.export_dir, filename)
    
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True)
    
    return jsonify({'success': False, 'error': '文件不存在'}), 404


# ==================== 协作文会话管理 ====================

@api.route('/collab/lock', methods=['POST'])
def acquire_lock():
    """获取资源锁（用于协作编辑）"""
    from models import CollaborationLock
    
    data = request.json
    resource_type = data.get('resource_type')  # case/defect/project
    resource_id = data.get('resource_id')
    user = data.get('user')
    
    if not all([resource_type, resource_id, user]):
        return jsonify({'success': False, 'error': '缺少必要参数'}), 400
    
    # 检查是否已有锁
    existing_lock = CollaborationLock.query.filter_by(
        resource_type=resource_type,
        resource_id=resource_id,
        is_active=True
    ).first()
    
    if existing_lock:
        # 检查是否过期（30 秒）
        from datetime import timedelta
        if datetime.utcnow() - existing_lock.locked_at > timedelta(seconds=30):
            # 锁已过期，释放并重新获取
            existing_lock.is_active = False
            db.session.commit()
        else:
            return jsonify({
                'success': False,
                'locked_by': existing_lock.user,
                'message': '资源已被锁定'
            }), 409
    
    # 创建新锁
    lock = CollaborationLock(
        resource_type=resource_type,
        resource_id=resource_id,
        user=user
    )
    db.session.add(lock)
    db.session.commit()
    
    # WebSocket 广播
    socketio.emit('collab:lock', {
        'resource_type': resource_type,
        'resource_id': resource_id,
        'user': user
    }, broadcast=True)
    
    return jsonify({
        'success': True,
        'lock_id': lock.id,
        'expires_in': 30
    })


@api.route('/collab/unlock', methods=['POST'])
def release_lock():
    """释放资源锁"""
    from models import CollaborationLock
    
    data = request.json
    lock_id = data.get('lock_id')
    user = data.get('user')
    
    if not lock_id:
        return jsonify({'success': False, 'error': '缺少锁 ID'}), 400
    
    lock = CollaborationLock.query.get_or_404(lock_id)
    
    if lock.user != user:
        return jsonify({'success': False, 'error': '无权释放他人的锁'}), 403
    
    lock.is_active = False
    db.session.commit()
    
    # WebSocket 广播
    socketio.emit('collab:unlock', {
        'resource_type': lock.resource_type,
        'resource_id': lock.resource_id,
        'user': user
    }, broadcast=True)
    
    return jsonify({'success': True})


@api.route('/collab/heartbeat', methods=['POST'])
def heartbeat():
    """心跳保活（延长锁有效期）"""
    from models import CollaborationLock
    
    data = request.json
    lock_id = data.get('lock_id')
    
    if not lock_id:
        return jsonify({'success': False, 'error': '缺少锁 ID'}), 400
    
    lock = CollaborationLock.query.get_or_404(lock_id)
    lock.last_heartbeat = datetime.utcnow()
    db.session.commit()
    
    return jsonify({'success': True, 'expires_in': 30})


# ==================== 用例版本管理 ====================

@api.route('/test-cases/<int:case_id>/history', methods=['GET'])
def get_case_history(case_id):
    """还原到指定历史版本"""
    from models import CaseHistory, TestCase
    
    test_case = TestCase.query.get_or_404(case_id)
    history = CaseHistory.query.filter_by(
        case_id=case_id,
        version=version,
        is_deleted=False
    ).first_or_404()
    
    # 从历史记录中恢复内容
    content = history.content
    case_data = json.loads(content)
    
    test_case.title = case_data.get('title', test_case.title)
    test_case.description = case_data.get('description', test_case.description)
    test_case.steps = json.dumps(case_data.get('steps', []))
    test_case.expected_result = case_data.get('expected_result', '')
    test_case.priority = case_data.get('priority', 'medium')
    test_case.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    socketio.emit('test_case_restored', {
        'case_id': case_id,
        'restored_version': version
    }, namespace='/collaboration')
    
    return jsonify({
        'success': True,
        'message': f'已还原到版本 {version}'
    })


# ==================== AI 服务集成 ====================

@api.route('/ai/generate-test-cases', methods=['POST'])
def ai_generate_test_cases():
    """AI 生成测试用例"""
    from services.ai_service import AIService
    
    data = request.json
    ai_service = AIService()
    
    result = ai_service.generate_test_cases(
        requirement=data['requirement'],
        project_id=data['project_id'],
        model=data.get('model', 'qwen-plus')
    )
    
    # 批量保存到数据库
    created_cases = []
    for case_data in result['test_cases']:
        test_case = TestCase(
            project_id=data['project_id'],
            title=case_data['title'],
            description=case_data.get('description', ''),
            steps=json.dumps(case_data.get('steps', [])),
            expected_result=case_data.get('expected_result', ''),
            priority=case_data.get('priority', 'medium'),
            ai_generated=True,
            ai_model=data.get('model', 'qwen-plus')
        )
        db.session.add(test_case)
        created_cases.append(test_case.to_dict())
    
    db.session.commit()
    
    socketio.emit('ai_generation_complete', {
        'test_cases': created_cases,
        'count': len(created_cases)
    }, namespace='/collaboration')
    
    return jsonify({
        'success': True,
        'test_cases': created_cases,
        'message': f'成功生成 {len(created_cases)} 个测试用例'
    })


@api.route('/ai/analyze-defect', methods=['POST'])
def ai_analyze_defect():
    """AI 分析缺陷"""
    from services.ai_service import AIService
    
    data = request.json
    ai_service = AIService()
    
    result = ai_service.analyze_defect(
        defect_description=data['description'],
        logs=data.get('logs', ''),
        screenshot=data.get('screenshot', '')
    )
    
    # 更新缺陷记录
    if 'defect_id' in data:
        defect = Defect.query.get_or_404(data['defect_id'])
        defect.ai_analyzed = True
        defect.ai_suggestion = result.get('suggestion', '')
        defect.severity = result.get('severity', defect.severity)
        db.session.commit()
    
    return jsonify(result)


@api.route('/ai/chat', methods=['POST'])
def ai_chat():
    """
    统一 AI 聊天接口 - 支持多模型网关
    
    Request JSON:
    {
        "prompt": "请生成测试用例...",
        "model": "auto",  // auto/deepseek/doubao/ernie/chatgpt/gitcode
        "system_prompt": "你是一个测试专家...",
        "temperature": 0.7,
        "max_tokens": 2048
    }
    
    Response JSON:
    {
        "success": true,
        "reply": "...",
        "model": "deepseek",
        "usage": {...},
        "latency": 1.23,
        "is_fallback": false
    }
    """
    from services.llm_gateway import get_llm_gateway
    
    data = request.json
    
    if not data or not data.get('prompt'):
        return jsonify({
            'success': False,
            'error': '缺少必要参数：prompt'
        }), 400
    
    llm_gateway = get_llm_gateway()
    
    result = llm_gateway.chat(
        prompt=data['prompt'],
        model_id=data.get('model', 'auto'),
        system_prompt=data.get('system_prompt'),
        temperature=data.get('temperature', 0.7),
        max_tokens=data.get('max_tokens', 2048)
    )
    
    if result.get('success'):
        return jsonify(result)
    else:
        return jsonify(result), 500


@api.route('/ai/models', methods=['GET'])
def get_available_models():
    """获取所有可用的 AI 模型列表"""
    from services.llm_gateway import get_llm_gateway
    
    llm_gateway = get_llm_gateway()
    models = llm_gateway.get_available_models()
    
    return jsonify({
        'success': True,
        'models': models
    })


@api.route('/ai/statistics', methods=['GET'])
def get_ai_statistics():
    """获取 AI 调用统计信息"""
    from services.llm_gateway import get_llm_gateway
    
    llm_gateway = get_llm_gateway()
    stats = llm_gateway.get_call_statistics()
    
    return jsonify({
        'success': True,
        'statistics': stats
    })


# ==================== 文档导入与解析 ====================

@api.route('/doc/upload', methods=['POST'])
def upload_document():
    """
    上传需求文档并自动解析
    
    支持格式：docx/xlsx/pdf/png/jpg
    
    Response:
    {
        'success': true,
        'data': {
            'filepath': str,
            'filename': str,
            'file_type': str,
            'uuid': str,
            'raw_text': str,
            'summary': str  // AI 生成的摘要
        }
    }
    """
    from services.doc_parser import get_doc_parser
    from services.llm_gateway import get_llm_gateway
    
    if 'file' not in request.files:
        return jsonify({
            'success': False,
            'error': '没有上传文件'
        }), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({
            'success': False,
            'error': '文件名为空'
        }), 400
    
    doc_parser = get_doc_parser()
    
    # 检查文件格式
    if not doc_parser.is_allowed_file(file.filename):
        return jsonify({
            'success': False,
            'error': '不支持的文件格式，仅支持 docx/xlsx/pdf/png/jpg'
        }), 400
    
    # 保存文件
    user_id = request.form.get('user_id', 'default')
    save_result = doc_parser.save_uploaded_file(file, user_id)
    
    if not save_result.get('success'):
        return jsonify(save_result), 400
    
    # 提取文本
    extract_result = doc_parser.extract_text(save_result['filepath'])
    
    if not extract_result.get('success'):
        return jsonify(extract_result), 500
    
    # 调用 AI 生成摘要（可选）
    summary = ''
    if request.form.get('auto_summary', 'true').lower() == 'true':
        llm_gateway = get_llm_gateway()
        prompt = f"请为以下需求文档生成简洁的摘要（200 字以内），提取核心功能点和测试重点：\n\n{extract_result['raw_text'][:3000]}"
        
        ai_result = llm_gateway.chat(prompt=prompt, model_id='auto')
        if ai_result.get('success'):
            summary = ai_result.get('reply', '')
    
    return jsonify({
        'success': True,
        'data': {
            **save_result,
            'raw_text': extract_result['raw_text'],
            'pages': extract_result['pages'],
            'metadata': extract_result['metadata'],
            'summary': summary
        }
    })


@api.route('/doc/parse', methods=['POST'])
def parse_document():
    """
    解析已上传的文档
    
    Request JSON:
    {
        "filepath": "uploads/user1/docs/xxx/req.docx",
        "file_type": "word"  // 可选，自动检测
    }
    """
    from services.doc_parser import get_doc_parser
    
    data = request.json
    
    if not data or not data.get('filepath'):
        return jsonify({
            'success': False,
            'error': '缺少文件路径'
        }), 400
    
    doc_parser = get_doc_parser()
    result = doc_parser.extract_text(data['filepath'], data.get('file_type'))
    
    if result.get('success'):
        return jsonify(result)
    else:
        return jsonify(result), 500


@api.route('/doc/list', methods=['GET'])
def list_documents():
    """列出用户上传的文档历史"""
    import os
    from services.doc_parser import get_doc_parser
    
    user_id = request.args.get('user_id', 'default')
    docs_dir = os.path.join(get_doc_parser().upload_folder, user_id, 'docs')
    
    if not os.path.exists(docs_dir):
        return jsonify({
            'success': True,
            'documents': []
        })
    
    documents = []
    for root, dirs, files in os.walk(docs_dir):
        for uuid_dir in dirs:
            uuid_path = os.path.join(root, uuid_dir)
            for filename in os.listdir(uuid_path):
                filepath = os.path.join(uuid_path, filename)
                file_type = get_doc_parser().get_file_type(filename)
                
                documents.append({
                    'uuid': uuid_dir,
                    'filename': filename,
                    'file_type': file_type,
                    'filepath': filepath,
                    'uploaded_at': datetime.fromtimestamp(os.path.getctime(filepath)).isoformat()
                })
    
    # 按上传时间倒序
    documents.sort(key=lambda x: x['uploaded_at'], reverse=True)
    
    return jsonify({
        'success': True,
        'documents': documents
    })