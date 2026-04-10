# AI Test Platform v2.0 发布说明

## 🚀 重大更新概览

本次更新将 AI 赋能软件测试平台从 v1.0 升级到 v2.0，核心增强了多模型接口支持、测试设计模板库、历史记录管理、多语言支持和错误处理系统。

---

## ✨ 新增功能

### 1. 多模型接口集成 🔄

**新增 GitCode AI 接口支持**
- 创建独立 `aiProxy.js` 模块，统一封装 CSDN 与 GitCode 双端点
- AI 助手抽屉新增「模型源」下拉框，支持一键切换 CSDN / GitCode
- 实现失败自动降级：当 GitCode 接口失败时自动切换到 CSDN
- 温度/top_p 参数记忆化保存，下次打开自动恢复

**Prompt 优化开关**
- 新增开关可自动追加准确率提升指令
- 优化后的 Prompt 会自动包含测试场景、步骤、预期结果等结构化要求

### 2. 规则模板库扩展 📋

**新增 6 套高级测试设计模板**

| 模板名称 | 图标 | 适用场景 |
|---------|------|---------|
| 状态迁移测试 | 🔄 | 测试状态转换逻辑 |
| 组合测试 | 🔀 | 全配对/多因素组合覆盖 |
| Fuzzing 模糊测试 | 🎲 | 随机/半随机输入发现漏洞 |
| API 契约测试 | 📜 | 验证接口符合 OpenAPI/Swagger 规范 |
| BDD 行为驱动 | ✅ | Given-When-Then 格式用例 |
| 异常注入测试 | 💉 | 主动注入异常验证系统健壮性 |

**混合模板拼接**
- 支持同时选择多个模板进行拼接
- 一键生成综合型测试策略 Prompt

### 3. 历史记录功能增强 📊

**准确率标注**
- 每条历史记录支持手动标注准确率（0-100%）
- 高准确率样本可用于后续模型微调

**差异对比**
- 可同时选择多条记录进行对比
- 并排展示不同模型/不同时间的生成结果

**回滚生成**
- 一键将历史 Prompt 重新投递到 AI 助手
- 支持更换模型或调整参数后重新生成

**批量打标签**
- 支持自定义标签（如：regression, smoke, high-quality）
- 批量应用于选中的历史记录

**导出 HuggingFace 格式**
- 过滤准确率≥80% 的高质量样本
- 导出兼容 HuggingFace JSON Lines 格式
- 可直接用于 DeepSeek/Qwen 等模型微调

### 4. 多语言支持升级 🌍

**新增语言**
- fr-FR（法语）
- de-DE（德语）

**运行时插值 + 缺省回退**
- 支持动态参数替换：`t('welcome', { name: 'User' })`
- 缺省回退机制：当前语言缺失时自动回退到中文或英文

**全量翻译覆盖**
- 所有 UI 文案
- 所有模板名称与描述
- 所有错误码与提示信息

### 5. 错误处理系统强化 🛠️

**错误分类细化**
- 用户输入级：空需求、过长输入、格式错误
- 网络级：API 超时、连接失败、HTTP 错误
- AI 返回级：解析失败、内容为空、模型错误

**日志面板增强**
- 按类型筛选错误日志
- 统计卡片显示各类错误数量
- Sentry-style 相似错误合并

**报告功能**
- 一键复制错误报告 JSON
- 下载日志包含分类统计信息

---

## 📁 文件结构

```
/root/o90D5yf1gb9RGl1hxBnb/
├── index.html          # 主页面（含全部前端逻辑）
├── aiProxy.js          # AI 代理模块（v2.0 新增）
├── TODO.md             # 任务跟踪
├── RELEASE_NOTES_v2.0.md # 本文件
└── .inscode            # 项目配置
```

---

## 🔧 技术细节

### aiProxy.js 核心功能

```javascript
// 统一调用接口
aiProxy.call(model, messages, {
    provider: 'csdn' | 'gitcode',
    stream: true,
    temperature: 0.7,
    topP: 0.7,
    fallback: true  // 启用失败降级
});

// 模型映射
const MODEL_MAPPING = {
    csdn: { 'Deepseek-V3': 'deepseek-v3', 'qwen-vl-plus': 'qwen-vl-plus' },
    gitcode: { 'Deepseek-V3': 'deepseek-v3', 'glm-4': 'glm-4' }
};
```

### localStorage 数据结构

```javascript
// aiHistory - 历史记录
{
    id: 1234567890,
    timestamp: '2026-04-10T11:00:00Z',
    model: 'Deepseek-V3',
    provider: 'csdn',
    requirement: '为登录功能生成测试用例...',
    fullRequirement: '完整需求内容...',
    result: '生成的测试结果...',
    success: true,
    runStatus: 'pending',
    accuracy: 95,
    tags: ['high-quality', 'regression'],
    promptOptimized: true
}

// errorLogs - 错误日志
{
    timestamp: '2026-04-10T11:00:00Z',
    source: 'user_input' | 'network' | 'ai_response' | 'browser',
    message: '错误信息',
    details: '详细信息'
}
```

---

## 📊 统计数据

- **模板总数**: 12 套（原有 6 套 + 新增 6 套）
- **支持语言**: 5 种（zh-CN, en-US, es-ES, fr-FR, de-DE）
- **错误分类**: 4 类（用户输入、网络、AI 返回、浏览器）
- **历史记录字段**: 10+ 个（含准确率、标签、优化标记等）

---

## 🎯 使用建议

### 提高生成准确率
1. 开启「Prompt 优化」开关
2. 使用混合模板拼接功能
3. 生成后及时标注准确率
4. 定期导出高质量样本用于微调

### 多模型切换策略
- 默认使用 CSDN（稳定性高）
- 需要特定模型时切换到 GitCode
- 遇到错误时自动降级无需手动干预

### 数据管理
- 每周导出一次 HuggingFace 格式数据集
- 定期清理低质量历史记录
- 使用标签功能标记重要样本

---

## 🔮 后续规划

- [ ] 接入更多 AI 提供商（豆包、文心一言、ChatGPT）
- [ ] 支持图片输入生成测试用例
- [ ] 增加测试用例执行和结果验证
- [ ] 团队协作和多用户支持
- [ ] 云端同步和备份

---

## 📞 技术支持

如有问题或建议，请查看错误日志并导出 JSON 反馈。

**版本**: v2.0  
**发布日期**: 2026-04-10  
**技术栈**: HTML + TailwindCSS + 原生 JavaScript  
**数据存储**: localStorage（纯前端，零后端）