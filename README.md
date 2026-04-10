# AI Test Hub - 智能测试工作台

> 可串联、可持久化、可协作的完整测试系统 | PyCharm 一键启动

## 🚀 快速开始

### 在 PyCharm 中运行

1. **打开项目**：用 PyCharm 打开本项目目录
2. **配置解释器**：首次打开会自动创建虚拟环境
3. **一键启动**：点击运行配置 "AI Test Hub" 或执行 `python app.py`
4. **访问应用**：浏览器打开 `http://localhost:5000`

### 命令行运行

```bash
# 安装依赖
pip install -r requirements.txt

# 启动服务
python app.py
```

## 📁 项目结构

```
ai-test-hub/
├── app.py                 # Flask 后端主程序
├── models.py              # 数据库模型定义
├── requirements.txt       # Python 依赖
├── .inscode              # 运行配置文件
├── routes/
│   └── api.py            # API 路由
├── services/
│   ├── ai_service.py     # AI 服务层
│   └── report_service.py # 报告服务层
├── templates/
│   └── index.html        # 前端页面模板
├── static/               # 静态资源（CSS/JS/图片）
├── instance/
│   └── ai_test_hub.db    # SQLite 数据库（自动生成）
└── .idea/                # PyCharm 项目配置
```

## ✨ 核心功能

### 1. AI 用例生成
- 支持需求文档/用户故事自动转化为测试用例
- 多模型智能选择（CSDN/GitCode）
- 用例优化建议与自动生成

### 2. UI 自动化测试
- 智能元素定位（同义词匹配 + 权重评分）
- 脚本录制与回放
- 实时执行监控

### 3. 缺陷分析
- 自动缺陷分类与严重程度评估
- AI 驱动的根本原因分析
- 修复建议生成

### 4. 多模接口调用
- 统一 API 网关
- 请求/响应日志记录
- 性能监控与告警

### 5. 报告导出
- Excel/PDF/HTML 多格式支持
- 自定义报告模板
- 一键分享与协作

### 6. 实时协作
- WebSocket 实时通信
- 多用户在线编辑
- 操作历史追溯

## 🗄️ 数据持久化

所有数据自动保存到 SQLite 数据库（`instance/ai_test_hub.db`），包括：

- **项目信息**：项目名称、描述、成员
- **测试用例**：用例内容、优先级、状态
- **执行记录**：执行时间、结果、日志
- **缺陷跟踪**：缺陷描述、严重程度、修复状态
- **用户会话**：在线用户、协作记录

数据库文件随项目走，PyCharm 打开即可运行，零配置。

## 🔌 API 接口

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/projects` | GET/POST | 项目管理 |
| `/api/test-cases` | GET/POST | 用例管理 |
| `/api/generate-cases` | POST | AI 生成用例 |
| `/api/execute` | POST | 执行测试 |
| `/api/defects` | GET/POST | 缺陷管理 |
| `/api/analyze-defect` | POST | AI 缺陷分析 |
| `/api/reports/export` | POST | 导出报告 |
| `/api/upload` | POST | 文件上传 |
| `/ws/collaboration` | WebSocket | 实时协作 |

## 👥 协作功能

1. **登录系统**：右上角输入用户名即可加入协作
2. **实时同步**：用例编辑、执行状态实时广播
3. **在线用户列表**：查看当前协作者
4. **操作历史**：追溯所有变更记录

## 🛠️ 开发指南

### 添加新功能

1. 在 `routes/api.py` 中添加 API 路由
2. 在 `services/` 中实现业务逻辑
3. 在 `models.py` 中添加数据模型（如需要）
4. 在前端 `templates/index.html` 中调用新 API

### 调试技巧

- 开启 debug 模式：`app.py` 中 `debug=True`
- 查看 SQL 日志：设置 `SQLALCHEMY_ECHO = True`
- WebSocket 调试：浏览器控制台查看 Socket.IO 日志

## 📝 版本历史

- **v3.0** (当前)：Flask 后端一体化，支持持久化与协作
- **v2.1**：纯前端版本，localStorage 存储
- **v2.0**：AI 用例生成 + UI 自动化基础功能

## 📄 许可证

MIT License

---

**PyCharm 一键启动 → 完整闭环测试体验**