# 测试指南

本目录包含平台 API 的所有测试。

## 测试结构

```
tests/
├── __init__.py
├── conftest.py          # 共享 fixtures
├── pytest.ini           # pytest 配置
├── unit/                # 单元测试
│   ├── test_response.py     # 响应工具测试
│   ├── test_pagination.py   # 分页工具测试
│   ├── test_security.py     # 安全工具测试
│   ├── test_exceptions.py   # 异常模块测试
│   ├── test_schemas.py      # Schema 测试
│   └── test_adapters.py     # 模型适配器测试
└── integration/         # 集成测试
```

## 运行测试

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行所有测试

```bash
pytest
```

### 运行单元测试

```bash
pytest tests/unit/
```

### 运行集成测试

```bash
pytest tests/integration/
```

### 运行特定测试文件

```bash
pytest tests/unit/test_security.py
```

### 查看覆盖率

```bash
pytest --cov=app --cov-report=term-missing
```

### 生成 HTML 覆盖率报告

```bash
pytest --cov=app --cov-report=html
open htmlcov/index.html
```

## 测试标记

- `@pytest.mark.unit` - 单元测试
- `@pytest.mark.integration` - 集成测试
- `@pytest.mark.slow` - 慢速测试
- `@pytest.mark.e2e` - 端到端测试

## Fixtures

主要的测试 fixtures 定义在 `conftest.py` 中：

- `test_settings` - 测试用配置
- `mock_settings` - Mock 配置单例
- `super_admin_token` - 超级管理员令牌
- `operator_token` - 运营管理员令牌
- `sub_user_token` - 子用户令牌
- `expired_token` - 已过期的令牌
- `mock_db_session` - Mock 数据库会话
- `sample_user_data` - 示例用户数据
- `sample_template_data` - 示例模板数据
- `sample_material_data` - 示例素材数据
- `sample_generation_task_data` - 示例生成任务数据

## 测试覆盖率目标

- 总体覆盖率：>= 80%
- 核心模块：>= 90%
  - `app.core`
  - `app.utils`
  - `app.schemas`

## 注意事项

1. 单元测试应该独立运行，不依赖外部服务
2. 使用 mock 替代数据库、Redis 等外部依赖
3. 测试应该是幂等的，可以重复运行
4. 每个测试应该只测试一个功能点
5. 使用描述性的测试名称
