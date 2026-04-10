# AI Test Hub - 开发快捷命令
# 使用方法：make dev / make test / make lint

.PHONY: dev test lint clean init help

# 默认目标
help:
	@echo "AI Test Hub - 可用命令:"
	@echo "  make dev     - 启动开发服务器 (热重载)"
	@echo "  make test    - 运行测试套件"
	@echo "  make lint    - 代码风格检查"
	@echo "  make clean   - 清理缓存文件"
	@echo "  make init    - 初始化数据库"
	@echo "  make install - 安装依赖"

# 启动开发服务器
dev:
	@echo "🚀 启动开发服务器..."
	python run.py

# 运行测试
test:
	@echo "🧪 运行测试..."
	pytest tests/ -v --tb=short || echo "提示：请先安装 pytest (pip install pytest)"

# 代码风格检查
lint:
	@echo "🔍 代码风格检查..."
	flake8 app.py models.py routes/ services/ --max-line-length=120 --ignore=E501,W503 || echo "提示：请先安装 flake8 (pip install flake8)"

# 清理缓存
clean:
	@echo "🧹 清理缓存文件..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	rm -rf .pytest_cache .coverage htmlcov/ 2>/dev/null || true
	@echo "✓ 清理完成"

# 初始化数据库
init:
	@echo "🗄️ 初始化数据库..."
	python -c "from app import app, db; app.app_context().push(); db.create_all(); print('✓ 数据库初始化成功')"

# 安装依赖
install:
	@echo "📦 安装依赖..."
	pip install -r requirements.txt
	@echo "✓ 依赖安装完成"

# 快速启动（首次使用）
setup: install init
	@echo "✓ 项目设置完成！运行 'make dev' 启动服务"