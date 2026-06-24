# 贡献指南

感谢你考虑为 妙笔内容工场做出贡献！

## 目录

- [行为准则](#行为准则)
- [如何贡献](#如何贡献)
- [开发流程](#开发流程)
- [代码规范](#代码规范)
- [提交规范](#提交规范)
- [Pull Request 流程](#pull-request-流程)

---

## 行为准则

本项目采用 [Contributor Covenant 行为准则](CODE_OF_CONDUCT.md)。参与本项目即表示你同意遵守其条款。

---

## 如何贡献

### 报告 Bug

如果你发现了 Bug，请通过 [GitHub Issues](../../issues) 提交报告。提交前请：

1. 搜索已有的 Issues，确认该 Bug 未被报告
2. 使用 Bug 报告模板填写详细信息
3. 提供复现步骤、预期结果和实际结果

### 提出新功能

如果你有新功能建议：

1. 先在 Issues 中讨论你的想法
2. 等待维护者确认方向
3. 提交详细的实现方案

### 提交代码

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'feat: add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 提交 Pull Request

---

## 开发流程

### 环境准备

#### 后端开发

```bash
cd platform_api
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# 配置数据库、Redis 等
alembic upgrade head
uvicorn app.main:app --reload
```

#### 前端开发

```bash
cd platform_web
npm install
npm run dev
```

### 分支命名规范

- `feature/功能名` - 新功能开发
- `fix/bug名` - Bug 修复
- `docs/文档更新` - 文档改进
- `refactor/重构名` - 代码重构
- `test/测试名` - 测试相关

### 代码风格

#### Python 代码规范

- 遵循 [PEP 8](https://pep8.org/) 规范
- 使用 [Black](https://github.com/psf/black) 格式化代码
- 使用 [isort](https://github.com/PyCQA/isort) 排序导入
- 类型注解：使用 Python 3.11+ 类型提示

```bash
# 格式化代码
black platform_api/
isort platform_api/

# 类型检查
mypy platform_api/
```

#### TypeScript/Vue 代码规范

- 遵循 [Vue 官方风格指南](https://vuejs.org/style-guide/)
- 使用 ESLint + Prettier 格式化
- 组件命名：PascalCase
- 文件命名：kebab-case

```bash
# 格式化代码
npm run lint
npm run format
```

---

## 提交规范

我们使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

### 提交消息格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

### 类型（type）

- `feat` - 新功能
- `fix` - Bug 修复
- `docs` - 文档更新
- `style` - 代码格式（不影响功能）
- `refactor` - 重构
- `test` - 测试相关
- `chore` - 构建/工具链相关
- `perf` - 性能优化

### 示例

```bash
feat(api): 添加用户登录接口

- 实现账号密码登录
- 实现微信扫码登录
- 添加 JWT Token 认证

Closes #123
```

```bash
fix(web): 修复用户列表分页问题

修复当用户总数为 0 时，分页组件显示异常的问题

Fixes #456
```

---

## Pull Request 流程

### 提交前检查清单

- [ ] 代码通过所有测试
- [ ] 代码符合项目风格规范
- [ ] 提交消息符合规范
- [ ] 更新了相关文档
- [ ] 添加了必要的测试用例
- [ ] 没有引入新的警告

### PR 标题规范

使用与提交消息相同的格式：

```
feat: 添加用户管理功能
fix: 修复登录失败问题
docs: 更新部署文档
```

### 审查流程

1. 提交 PR 后，维护者会进行代码审查
2. 根据审查意见修改代码
3. 通过审查后，维护者会合并你的 PR

### 合并要求

- 至少 1 位维护者审查通过
- 所有 CI 检查通过
- 没有合并冲突
- 分支与主分支保持同步

---

## 测试规范

### 单元测试

- 为新功能添加单元测试
- 测试覆盖率不低于 80%
- 使用 pytest（后端）和 Vitest（前端）

```bash
# 后端测试
cd platform_api
pytest --cov=app

# 前端测试
cd platform_web
npm run test
```

### 集成测试

- 测试 API 接口
- 测试数据库操作
- 测试异步任务

### E2E 测试

- 使用 Playwright 进行端到端测试
- 测试关键业务流程

---

## 文档规范

### API 文档

- 使用 OpenAPI/Swagger 规范
- 添加详细的接口说明和示例

### 代码注释

- 复杂逻辑添加注释
- 公共 API 添加文档字符串
- 避免无意义的注释

### README 更新

- 新功能添加到 README
- 更新安装和配置说明
- 添加使用示例

---

## 问题反馈

如果你有任何问题：

- 📧 邮件：[项目邮箱]
- 💬 讨论：[GitHub Discussions](../../discussions)
- 🐛 Bug：[GitHub Issues](../../issues)

---

## 许可证

提交代码即表示你同意你的贡献将按照 [MIT License](LICENSE) 授权。

---

感谢你的贡献！🎉