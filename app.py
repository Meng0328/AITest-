"""
AI Test Hub - 一体化测试平台后端
Flask + SQLAlchemy + SocketIO 实现可串联、可持久化、可协作的完整系统
"""

import os
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory, send_file, redirect, url_for
from werkzeug.utils import secure_filename
from extensions import db, socketio, init_extensions


def create_app():
    """应用工厂函数 - 创建并配置 Flask 应用"""
    
    # 初始化 Flask 应用
    app = Flask(__name__, static_folder='static', template_folder='templates')
    app.config['SECRET_KEY'] = 'ai-test-hub-secret-key-2024'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ai_test_hub.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = 'uploads'
    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB 限制
    
    # 确保上传目录存在
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs('static', exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    
    # 初始化扩展
    init_extensions(app)
    
    # 注册蓝图（延迟导入，避免循环依赖）
    from core.routes import core as core_blueprint
    from routes.api import api as api_blueprint
    app.register_blueprint(core_blueprint)
    app.register_blueprint(api_blueprint)
    
    # 注册页面路由和 API
    register_routes(app)
    
    return app


def register_routes(app):
    """注册所有路由"""
    
    # 延迟导入模型和服务（避免循环依赖）
    from models import Project, TestCase, TestExecution, Defect, CollaborationSession, User, TestResult
    from services.ai_service import AIService
    from services.report_service import ReportService
    
    ai_service = AIService()
    report_service = ReportService()
    
    # ==================== 路由 - 页面服务 ====================
    
    @app.route('/')
    def index():
        """主页 - 重定向到仪表盘"""
        return redirect(url_for('core.dashboard'))
    
    @app.route('/<path:filename>')
    def serve_static(filename):
        """提供静态文件"""
        return send_from_directory('static', filename)
    
    # ==================== API - 项目管理 ====================
    
    @app.route('/api/projects', methods=['GET'])
    def get_projects():
        """获取所有项目"""
        projects = Project.query.order_by(Project.updated_at.desc()).all()
        return jsonify({'success': True, 'data': [p.to_dict() for p in projects]})
    
    @app.route('/api/projects', methods=['POST'])
    def create_project():
        """创建新项目"""
        data = request.json
        if not data.get('name'):
            return jsonify({'success': False, 'error': '项目名称不能为空'}), 400
        
        project = Project(
            name=data['name'],
            description=data.get('description', '')
        )
        db.session.add(project)
        db.session.commit()
        
        socketio.emit('project_created', {'project': project.to_dict()}, broadcast=True)
        return jsonify({'success': True, 'data': project.to_dict()})
    
    @app.route('/api/projects/<int:project_id>', methods=['GET'])
    def get_project(project_id):
        """获取项目详情"""
        project = Project.query.get_or_404(project_id)
        return jsonify({'success': True, 'data': project.to_dict()})
    
    @app.route('/api/projects/<int:project_id>', methods=['PUT'])
    def update_project(project_id):
        """更新项目"""
        project = Project.query.get_or_404(project_id)
        data = request.json
        
        if data.get('name'):
            project.name = data['name']
        if data.get('description') is not None:
            project.description = data['description']
        
        db.session.commit()
        return jsonify({'success': True, 'data': project.to_dict()})
    
    @app.route('/api/projects/<int:project_id>', methods=['DELETE'])
    def delete_project(project_id):
        """删除项目"""
        project = Project.query.get_or_404(project_id)
        db.session.delete(project)
        db.session.commit()
        
        socketio.emit('project_deleted', {'project_id': project_id}, broadcast=True)
        return jsonify({'success': True, 'message': '项目已删除'})
    
    # ==================== API - 测试用例管理 ====================
    
    @app.route('/api/projects/<int:project_id>/test-cases', methods=['GET'])
    def get_test_cases(project_id):
        """获取项目下的所有测试用例"""
        Project.query.get_or_404(project_id)
        test_cases = TestCase.query.filter_by(project_id=project_id).order_by(TestCase.created_at.desc()).all()
        return jsonify({'success': True, 'data': [tc.to_dict() for tc in test_cases]})
    
    @app.route('/api/projects/<int:project_id>/test-cases', methods=['POST'])
    def create_test_case(project_id):
        """创建测试用例"""
        Project.query.get_or_404(project_id)
        data = request.json
        
        if not data.get('title'):
            return jsonify({'success': False, 'error': '用例标题不能为空'}), 400
        
        test_case = TestCase(
            project_id=project_id,
            title=data['title'],
            description=data.get('description', ''),
            steps=json.dumps(data.get('steps', [])),
            expected_result=data.get('expected_result', ''),
            priority=data.get('priority', 'medium'),
            ai_model=data.get('ai_model'),
            source_doc=data.get('source_doc')
        )
        db.session.add(test_case)
        db.session.commit()
        
        socketio.emit('test_case_created', {'test_case': test_case.to_dict()}, broadcast=True)
        return jsonify({'success': True, 'data': test_case.to_dict()})
    
    @app.route('/api/test-cases/<int:test_case_id>', methods=['PUT'])
    def update_test_case(test_case_id):
        """更新测试用例"""
        test_case = TestCase.query.get_or_404(test_case_id)
        data = request.json
        
        if data.get('title'):
            test_case.title = data['title']
        if data.get('description') is not None:
            test_case.description = data['description']
        if data.get('steps') is not None:
            test_case.steps = json.dumps(data['steps'])
        if data.get('expected_result') is not None:
            test_case.expected_result = data['expected_result']
        if data.get('priority'):
            test_case.priority = data['priority']
        if data.get('status'):
            test_case.status = data['status']
        
        db.session.commit()
        return jsonify({'success': True, 'data': test_case.to_dict()})
    
    @app.route('/api/test-cases/<int:test_case_id>', methods=['DELETE'])
    def delete_test_case(test_case_id):
        """删除测试用例"""
        test_case = TestCase.query.get_or_404(test_case_id)
        db.session.delete(test_case)
        db.session.commit()
        
        socketio.emit('test_case_deleted', {'test_case_id': test_case_id}, broadcast=True)
        return jsonify({'success': True, 'message': '用例已删除'})
    
    # ==================== API - 测试执行 ====================
    
    @app.route('/api/projects/<int:project_id>/test-runs', methods=['GET'])
    def get_test_runs(project_id):
        """获取项目下的所有测试执行记录"""
        Project.query.get_or_404(project_id)
        test_runs = TestExecution.query.filter_by(project_id=project_id).order_by(TestExecution.created_at.desc()).all()
        return jsonify({'success': True, 'data': [tr.to_dict() for tr in test_runs]})
    
    @app.route('/api/projects/<int:project_id>/test-runs', methods=['POST'])
    def create_test_run(project_id):
        """创建测试执行记录"""
        Project.query.get_or_404(project_id)
        data = request.json
        
        test_run = TestExecution(
            project_id=project_id,
            name=data.get('name', f'Test Run {datetime.now().strftime("%Y%m%d%H%M%S")}'),
            test_type=data.get('test_type', 'ui'),
            total_cases=data.get('total_cases', 0),
            status='pending'
        )
        db.session.add(test_run)
        db.session.commit()
        
        socketio.emit('test_run_created', {'test_run': test_run.to_dict()}, broadcast=True)
        return jsonify({'success': True, 'data': test_run.to_dict()})
    
    @app.route('/api/test-runs/<int:test_run_id>/start', methods=['POST'])
    def start_test_run(test_run_id):
        """开始测试执行"""
        test_run = TestExecution.query.get_or_404(test_run_id)
        test_run.status = 'running'
        test_run.started_at = datetime.utcnow()
        db.session.commit()
        
        socketio.emit('test_run_started', {'test_run_id': test_run_id}, broadcast=True)
        return jsonify({'success': True, 'data': test_run.to_dict()})
    
    @app.route('/api/test-runs/<int:test_run_id>/complete', methods=['POST'])
    def complete_test_run(test_run_id):
        """完成测试执行"""
        test_run = TestExecution.query.get_or_404(test_run_id)
        data = request.json
        
        test_run.status = data.get('status', 'completed')
        test_run.passed_cases = data.get('passed_cases', 0)
        test_run.failed_cases = data.get('failed_cases', 0)
        test_run.completed_at = datetime.utcnow()
        test_run.report_path = data.get('report_path')
        db.session.commit()
        
        socketio.emit('test_run_completed', {'test_run': test_run.to_dict()}, broadcast=True)
        return jsonify({'success': True, 'data': test_run.to_dict()})
    
    @app.route('/api/test-runs/<int:test_run_id>/results', methods=['POST'])
    def add_test_result(test_run_id):
        """添加测试结果"""
        test_run = TestExecution.query.get_or_404(test_run_id)
        data = request.json
        
        result = TestResult(
            test_run_id=test_run_id,
            test_case_id=data['test_case_id'],
            step_number=data.get('step_number'),
            action=data.get('action'),
            locator=json.dumps(data.get('locator')) if data.get('locator') else None,
            status=data['status'],
            error_message=data.get('error_message'),
            screenshot_path=data.get('screenshot_path'),
            duration_ms=data.get('duration_ms', 0)
        )
        db.session.add(result)
        db.session.commit()
        
        socketio.emit('test_result_added', {'result': result.to_dict()}, broadcast=True)
        return jsonify({'success': True, 'data': result.to_dict()})
    
    # ==================== API - 缺陷管理 ====================
    
    @app.route('/api/projects/<int:project_id>/defects', methods=['GET'])
    def get_defects(project_id):
        """获取项目下的所有缺陷"""
        Project.query.get_or_404(project_id)
        defects = Defect.query.filter_by(project_id=project_id).order_by(Defect.created_at.desc()).all()
        return jsonify({'success': True, 'data': [d.to_dict() for d in defects]})
    
    @app.route('/api/projects/<int:project_id>/defects', methods=['POST'])
    def create_defect(project_id):
        """创建缺陷记录"""
        Project.query.get_or_404(project_id)
        data = request.json
        
        if not data.get('title'):
            return jsonify({'success': False, 'error': '缺陷标题不能为空'}), 400
        
        defect = Defect(
            project_id=project_id,
            title=data['title'],
            description=data.get('description', ''),
            severity=data.get('severity', 'major'),
            test_run_id=data.get('test_run_id'),
            test_result_id=data.get('test_result_id'),
            assigned_to=data.get('assigned_to')
        )
        db.session.add(defect)
        db.session.commit()
        
        socketio.emit('defect_created', {'defect': defect.to_dict()}, broadcast=True)
        return jsonify({'success': True, 'data': defect.to_dict()})
    
    @app.route('/api/defects/<int:defect_id>', methods=['PUT'])
    def update_defect(defect_id):
        """更新缺陷"""
        defect = Defect.query.get_or_404(defect_id)
        data = request.json
        
        if data.get('title'):
            defect.title = data['title']
        if data.get('description') is not None:
            defect.description = data['description']
        if data.get('severity'):
            defect.severity = data['severity']
        if data.get('status'):
            defect.status = data['status']
        if data.get('assigned_to') is not None:
            defect.assigned_to = data['assigned_to']
        
        db.session.commit()
        return jsonify({'success': True, 'data': defect.to_dict()})
    
    # ==================== API - 协作会话 ====================
    
    @app.route('/api/projects/<int:project_id>/sessions', methods=['GET'])
    def get_collaboration_sessions(project_id):
        """获取项目下的协作会话"""
        Project.query.get_or_404(project_id)
        sessions = CollaborationSession.query.filter_by(project_id=project_id).order_by(CollaborationSession.created_at.desc()).all()
        return jsonify({'success': True, 'data': [s.to_dict() for s in sessions]})
    
    @app.route('/api/projects/<int:project_id>/sessions', methods=['POST'])
    def create_collaboration_session(project_id):
        """创建协作会话"""
        Project.query.get_or_404(project_id)
        data = request.json
        
        session = CollaborationSession(
            project_id=project_id,
            session_name=data.get('session_name', f'Session {datetime.now().strftime("%Y%m%d%H%M%S")}'),
            host_user=data.get('host_user', 'anonymous'),
            participants=json.dumps([data.get('host_user', 'anonymous')])
        )
        db.session.add(session)
        db.session.commit()
        
        socketio.emit('session_created', {'session': session.to_dict()}, broadcast=True)
        return jsonify({'success': True, 'data': session.to_dict()})
    
    # ==================== WebSocket - 实时协作 ====================
    
    @socketio.on('connect')
    def handle_connect():
        """处理客户端连接"""
        print(f'Client connected: {request.sid}')
        emit('connected', {'sid': request.sid})
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """处理客户端断开"""
        print(f'Client disconnected: {request.sid}')
    
    @socketio.on('join_session')
    def handle_join_session(data):
        """加入协作会话"""
        session_id = data.get('session_id')
        user = data.get('user')
        
        session = CollaborationSession.query.get(session_id)
        if session and session.is_active:
            participants = json.loads(session.participants) if session.participants else []
            if user not in participants:
                participants.append(user)
                session.participants = json.dumps(participants)
                db.session.commit()
            
            emit('user_joined', {'session_id': session_id, 'user': user}, broadcast=True)
            return {'success': True, 'participants': participants}
        
        return {'success': False, 'error': '会话不存在或已结束'}
    
    @socketio.on('leave_session')
    def handle_leave_session(data):
        """离开协作会话"""
        session_id = data.get('session_id')
        user = data.get('user')
        
        session = CollaborationSession.query.get(session_id)
        if session:
            participants = json.loads(session.participants) if session.participants else []
            if user in participants:
                participants.remove(user)
                session.participants = json.dumps(participants)
                db.session.commit()
            
            emit('user_left', {'session_id': session_id, 'user': user}, broadcast=True)
            return {'success': True}
        
        return {'success': False, 'error': '会话不存在'}
    
    @socketio.on('sync_action')
    def handle_sync_action(data):
        """同步操作（用于实时协作）"""
        session_id = data.get('session_id')
        action = data.get('action')
        payload = data.get('payload')
        user = data.get('user')
        
        # 广播给同一会话的其他用户
        emit('action_synced', {
            'session_id': session_id,
            'action': action,
            'payload': payload,
            'user': user,
            'timestamp': datetime.utcnow().isoformat()
        }, broadcast=True, include_self=False)
        
        return {'success': True}
    
    @socketio.on('chat_message')
    def handle_chat_message(data):
        """协作聊天消息"""
        session_id = data.get('session_id')
        message = data.get('message')
        user = data.get('user')
        
        emit('chat_message_received', {
            'session_id': session_id,
            'message': message,
            'user': user,
            'timestamp': datetime.utcnow().isoformat()
        }, broadcast=True)
        
        return {'success': True}
    
    # ==================== AI 能力接口 ====================
    
    @app.route('/api/ai/generate-test-cases', methods=['POST'])
    def ai_generate_test_cases():
        """AI 生成测试用例"""
        data = request.json
        project_id = data.get('project_id')
        requirement = data.get('requirement', '')
        model = data.get('model', 'qwen-plus')
        
        if not project_id or not requirement:
            return jsonify({'success': False, 'error': '缺少必要参数'}), 400
        
        # 调用 AI 服务生成用例
        result = ai_service.generate_test_cases(requirement, model)
        
        if result.get('success'):
            # 批量保存到数据库
            project = Project.query.get_or_404(project_id)
            created_cases = []
            
            for case_data in result.get('test_cases', []):
                test_case = TestCase(
                    project_id=project_id,
                    title=case_data.get('title', ''),
                    description=case_data.get('description', ''),
                    steps=json.dumps(case_data.get('steps', [])),
                    expected_result=case_data.get('expected_result', ''),
                    priority=case_data.get('priority', 'medium'),
                    ai_model=model,
                    status='active'
                )
                db.session.add(test_case)
                created_cases.append(test_case.to_dict())
            
            db.session.commit()
            
            # 广播通知
            socketio.emit('test_cases_generated', {
                'project_id': project_id,
                'count': len(created_cases),
                'cases': created_cases
            }, broadcast=True)
            
            result['created_cases'] = created_cases
        
        return jsonify(result)
    
    @app.route('/api/ai/analyze-defect', methods=['POST'])
    def ai_analyze_defect():
        """AI 分析缺陷"""
        data = request.json
        defect_id = data.get('defect_id')
        model = data.get('model', 'qwen-plus')
        
        if not defect_id:
            return jsonify({'success': False, 'error': '缺少缺陷 ID'}), 400
        
        defect = Defect.query.get_or_404(defect_id)
        
        # 构建分析提示
        prompt = f"""请分析以下软件缺陷：

标题：{defect.title}
描述：{defect.description}

请提供：
1. 根本原因分析
2. 严重程度评估（critical/high/medium/low）
3. 修复建议
4. 预防措施

请以 JSON 格式返回：{{"root_cause": "", "severity": "", "suggestion": "", "prevention": ""}}"""
        
        result = ai_service.call_ai(model, [{'role': 'user', 'content': prompt}])
        
        if result.get('success'):
            # 更新缺陷记录
            try:
                analysis = json.loads(result['content']) if isinstance(result.get('content'), str) else result.get('content')
                defect.severity = analysis.get('severity', defect.severity)
                db.session.commit()
                
                result['analysis'] = analysis
                result['defect_id'] = defect_id
            except Exception as e:
                result['raw_analysis'] = result.get('content')
        
        return jsonify(result)
    
    @app.route('/api/ai/optimize-locator', methods=['POST'])
    def ai_optimize_locator():
        """AI 优化元素定位器"""
        data = request.json
        locator = data.get('locator', '')
        page_context = data.get('page_context', '')
        model = data.get('model', 'qwen-plus')
        
        if not locator:
            return jsonify({'success': False, 'error': '缺少定位器信息'}), 400
        
        prompt = f"""请优化以下 Selenium 元素定位器：

当前定位器：{locator}
页面上下文：{page_context}

请提供：
1. 更稳定的定位策略
2. 备选定位方案
3. 优化建议

请以 JSON 格式返回：{{"optimized_locator": "", "alternatives": [], "suggestions": []}}"""
        
        result = ai_service.call_ai(model, [{'role': 'user', 'content': prompt}])
        
        if result.get('success'):
            try:
                optimization = json.loads(result['content']) if isinstance(result.get('content'), str) else result.get('content')
                result['optimization'] = optimization
            except Exception as e:
                result['raw_suggestion'] = result.get('content')
        
        return jsonify(result)
    
    # ==================== 报告导出接口 ====================
    
    @app.route('/api/reports/export', methods=['POST'])
    def export_report():
        """导出测试报告"""
        data = request.json
        project_id = data.get('project_id')
        format_type = data.get('format', 'excel')  # excel/word/html
        include_cases = data.get('include_cases', True)
        include_executions = data.get('include_executions', True)
        include_defects = data.get('include_defects', True)
        
        if not project_id:
            return jsonify({'success': False, 'error': '缺少项目 ID'}), 400
        
        project = Project.query.get_or_404(project_id)
        
        # 获取数据
        test_cases = [tc.to_dict() for tc in project.test_cases.all()] if include_cases else []
        executions = [tr.to_dict() for tr in project.test_runs.all()] if include_executions else []
        defects = [d.to_dict() for d in project.defects.all()] if include_defects else []
        
        # 计算汇总
        summary = {
            'total_cases': len(test_cases),
            'total_executions': len(executions),
            'total_defects': len(defects),
            'pass_rate': sum(ex.get('pass_rate', 0) for ex in executions) / len(executions) if executions else 0
        }
        
        # 生成报告
        try:
            if format_type == 'excel':
                filepath = report_service.generate_excel_report(project.name, test_cases, executions, defects)
            elif format_type == 'word':
                filepath = report_service.generate_word_report(project.name, test_cases, executions, defects, summary)
            elif format_type == 'html':
                filepath = report_service.generate_html_report(project.name, test_cases, executions, defects, summary)
            else:
                return jsonify({'success': False, 'error': '不支持的报告格式'}), 400
            
            return jsonify({
                'success': True,
                'data': {
                    'filepath': filepath,
                    'download_url': f'/api/reports/download/{os.path.basename(filepath)}'
                }
            })
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/reports/download/<filename>')
    def download_report(filename):
        """下载报告文件"""
        filepath = os.path.join(report_service.export_dir, filename)
        if os.path.exists(filepath):
            return send_file(filepath, as_attachment=True)
        return jsonify({'success': False, 'error': '文件不存在'}), 404
    
    # ==================== 工具 API ====================
    
    @app.route('/api/upload', methods=['POST'])
    def upload_file():
        """上传文件（需求文档、截图等）"""
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': '没有文件'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': '文件名为空'}), 400
        
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        save_name = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], save_name)
        file.save(filepath)
        
        return jsonify({
            'success': True,
            'data': {
                'filename': save_name,
                'original_filename': filename,
                'path': filepath,
                'url': f'/uploads/{save_name}'
            }
        })
    
    @app.route('/uploads/<filename>')
    def serve_upload(filename):
        """提供上传的文件"""
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    
    @app.route('/api/health')
    def health_check():
        """健康检查"""
        return jsonify({
            'success': True,
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'database': 'connected' if db.engine else 'disconnected'
        })


# ==================== 初始化数据库 ====================

def init_db(app_instance=None):
    """初始化数据库"""
    if app_instance is None:
        from flask import current_app
        app_instance = current_app
    
    with app_instance.app_context():
        db.create_all()
        print('Database initialized successfully!')


if __name__ == '__main__':
    app = create_app()
    init_db(app)
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)