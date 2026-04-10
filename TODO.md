# AI-Test-Hub 后端一体化改造 · 继续完成

**目标：** 让 AI 用例生成、UI 自动化、缺陷分析、报告导出等所有模块真正跑通，解决菜单失灵、跨域、存储、协作等遗留问题，PyCharm 一键启动即可全链路调试。  
**技术栈：** Flask 3 + SQLAlchemy + SQLite + Jinja2 + Playwright(CPU) + Flask-SocketIO + WeasyPrint

---

## Task 1: 修复导航与菜单交互

> 解决“左侧模块无法点击、菜单无法切换”等前端遗留 Bug，全部走后端路由统一渲染

**文件：**  
- `templates/base.html`  
- `templates/partials/sidebar.html`  
- `core/routes.py`

- [ ] 把原硬编码 `<a href="#xxx">` 全部改为 `{{ url_for('core.page', name='xxx') }}`  
- [ ] 在 `base.html` 里用 `request.endpoint` 高亮当前菜单，避免刷新后丢失状态  
- [ ]  sidebar 动态加载可配置菜单项（从 `config/menus.yaml` 读取），后续新增页面无需改模板  
- [ ]  所有静态 JS 走 `{{ url_for('static', filename='js/...') }}`，解决缓存 404 问题  

---

## Task 2: 跨域代理脚本后端化

> 原 `cors-proxy.html` 仅前端 hack，需改为后端统一代理，支持 UI 自动化测试任意站点

**文件：**  
- `api/proxy.py`  
- `services/proxy_service.py`

- [ ] `/api/proxy/request` 接收 JSON：{"method":"GET","url":"...","headers":{}}  
- [ ] 后端使用 `requests` 转发，自动处理 cookie、重定向、超时（30s）  
- [ ] 响应体统一封装：{"status":200,"headers":{},"body":"..."}  
- [ ] 前端 `uiAutomation.js` 把原 `fetch(target)` 改为调用本代理，解决 CORS 阻塞  
- [ ] 提供开关 `PROXY_ENABLE=true/false`（`.env`），本地开发可直连  

---

## Task 3: 多模 AI 接口统一网关

> 一次接入 DeepSeek / 豆包 / 文心一言 / ChatGPT / gitcode 模型广场，支持轮询与失败重试

**文件：**  
- `services/llm_gateway.py`  
- `api/ai_gateway.py`  
- `config/llm.yaml`

- [ ] 在 `llm.yaml` 里配置多组 API key、base_url、模型别名、RPM 限额  
- [ ] 网关内部维护令牌桶限流，按权重轮询调用，失败自动降级  
- [ ] `/api/ai/chat` 统一入口：{"prompt":"...","model":"auto"}，返回 {"reply":"...","model":"deepseek"}  
- [ ] 所有调用记录写入 `AiCall` 表（prompt、response、耗时、模型、是否异常），方便后续微调数据收集  
- [ ] 前端“生成用例”按钮只调本接口，零改动即可切换模型  

---

## Task 4: 需求文档导入与解析

> 支持 Word/Excel/PDF/图片 一键上传，自动提取文本 → 生成测试用例

**文件：**  
- `services/doc_parser.py`  
- `api/doc_import.py`

- [ ] 上传接口 `/api/doc/upload` 支持多文件，后缀白名单：docx/xlsx/pdf/png/jpg  
- [ ] 文本提取：  
   - Word → python-docx  
   - Excel → pandas 读取所有 sheet  
   - PDF → pdfplumber  
   - 图片 → pytesseract OCR（CPU）  
- [ ] 提取后统一生成 `raw_text` 字段，调用 `llm_gateway` 做需求摘要 & 拆解  
- [ ] 摘要结果回显到前端“AI 用例生成”页面，用户可二次编辑再提交生成  
- [ ] 原始文件与解析结果按 `uploads/{user_id}/docs/{uuid}/` 落盘，数据库只存路径  

---

## Task 5: 用例生成历史 & 版本管理

> 每次生成记录完整快照，支持 diff 与回滚

**文件：**  
- `models/case_history.py`  
- `api/case_version.py`

- [ ] `CaseHistory` 表：case_id、version、content(json)、prompt、model、creator、created_at  
- [ ] 生成用例成功后再写一条历史，version 自增  
- [ ] `/api/case/{id}/history` 返回列表，支持 `?v=2` 获取指定版本  
- [ ] 前端“历史”按钮打开抽屉，展示 diff（ augusta-editor 只读模式），一键还原  
- [ ] 删除 Case 时软删除，历史记录保留，方便审计  

---

## Task 6: UI 自动化执行引擎强化

> 把原 `uiAutomation.js` 单线程改为后端 Playwright 集群任务，支持“单步调试”与“批量执行”

**文件：**  
- `services/playwright_runner.py`  
- `api/auto_job.py`

- [ ] Job 表新增字段：mode（single/batch）、breakpoint（bool）、steps（jsonb）  
- [ ] `/api/auto/run` 接收：{"case_id":1,"mode":"single","breakpoint":true}  
- [ ] 后端为每个 Job 启动独立线程，Playwright 录屏（mp4）+ 截图链路  
- [ ] 单步模式：每执行完一步推送 WebSocket 事件 `auto:step`，前端可“继续”或“停止”  
- [ ] 失败自动重试定位器（智能等待 3 次，每次 +2s），仍失败则写 Defect 并标记不稳定元素  

---

## Task 7: 元素稳定性评分与一键修复

> 根据历史执行数据给定位器打分，低于阈值自动推荐新定位器

**文件：**  
- `services/locator_ranker.py`  
- `api/locator_fix.py`

- [ ] 收集过去 30 天 Job 步骤：定位器、是否成功、耗时  
- [ ] 评分公式：score = (成功次数 + 1) / (总次数 + 2) * 100  
- [ ] `/api/locator/rank?case_id=1` 返回列表：{"locator":"text=登录","score":98}  
- [ ] 一键修复按钮：调用 Playwright 重新探测页面，推荐 css >> text >> xpath 优先级  
- [ ] 用户确认后自动更新 Case 表并生成新版本历史  

---

## Task 8: 实时协作与操作记录

> 多人同时编辑/执行时，锁定+广播，避免冲突

**文件：**  
- `services/collab_lock.py`  
- `api/activity.py`

- [ ] WebSocket 事件：`collab:lock{"case_id":1,"user":"tom"}`，30s 心跳自动解锁  
- [ ] 所有“生成/编辑/执行/删除”操作写 `Activity` 表，并通过 Socket 广播 feed  
- [ ] 前端右上角小铃铛实时推送，点击可跳转到对应模块  
- [ ] 提供 `/api/activity/export` 导出 CSV，方便复盘  

---

## Task 9: 报告导出（PDF + HTML + Markdown）

> 一键生成含截图、统计、缺陷列表的正式测试报告

**文件：**  
- `services/report_builder.py`  
- `api/report_export.py`  
- `templates/report_pdf.html`

- [ ] 报告模板使用 Tailwind 打印样式，支持分页、页眉页脚  
- [ ] 图表用 Chart.js CDN 离线渲染（Playwright 打印前 `page.pdf()`）  
- [ ] 提供三种格式：  
   - PDF → WeasyPrint  
   - HTML → 直接打包 zip  
   - Markdown → 供代码仓库归档  
- [ ] 报告文件命名：`{project}_{yyMMdd}_{hash}.pdf`，存 `reports/` 目录并写入 Report 表  
- [ ] 下载链接带一次性 `token=uuid`，10 分钟内有效  

---

## Task 10: PyCharm 一键启动与 E2E 自测

> 让任何同事拉代码后，3 秒内能跑起来，并有一条自动化脚本验证全链路

**文件：**  
- `run.py`  
- `tests/e2e/test_full_flow.py`  
- `Makefile`

- [ ] `run.py` 自动检测缺失 `.env` 并提示模板，调用 `flask run --reload`  
- [ ] Makefile：  
   - `make install` 一键装依赖  
   - `make test` 跑 pytest  
   - `make lint` ruff 检查  
- [ ] E2E 脚本：上传 PDF → 生成 3 条用例 → 执行 UI Job → 生成报告 → 断言报告存在  
- [ ] README 新增“PyCharm 运行截图”+“30 秒 GIF 演示”，降低 onboarding 成本