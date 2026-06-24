# 定时任务功能技术方案

## 1. 功能概述

为创作管理者设计定时任务功能，支持自动化内容生成任务调度。

### 核心特性

1. **灵活的调度配置**
   - 支持每日调度（可设置多个时间点）
   - 支持每周调度（可多选周一至周日，可设置多个时间点）
   - 任务数量不做限制

2. **任务类型支持**
   - 自定义文案任务（custom）
   - 对标文案任务（benchmark）

3. **完善的任务管理**
   - 创建、查询、更新、删除定时任务
   - 启用/禁用任务
   - 立即执行一次（测试用）
   - 执行统计和日志记录

## 2. 技术方案

### 2.1 技术选型

**推荐方案：Celery Beat + Redis Scheduler**

#### 为什么选择 Celery Beat？

| 维度 | Celery Beat | APScheduler | 选型理由 |
|------|-------------|--------------|---------|
| **架构集成** | 与现有 Celery 无缝集成 | 需要额外集成 | ✅ Celery Beat 与现有架构完美契合 |
| **分布式支持** | 原生支持分布式调度 | 单实例，需要额外实现 | ✅ 支持多实例部署，高可用 |
| **持久化** | 支持 Redis 持久化 | 需要额外配置 | ✅ Redis 持久化，重启不丢失任务 |
| **监控** | Flower 等成熟工具 | 较弱 | ✅ 完善的监控生态 |
| **重试机制** | 内置重试和错误处理 | 需要手动实现 | ✅ 成熟的重试机制 |
| **性能** | 高性能，支持大规模调度 | 性能一般 | ✅ 支持大量定时任务 |

### 2.2 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                         API Layer                                │
│  /api/v1/scheduled-tasks (CRUD + Execute)                       │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────┼──────────────────────────────────────┐
│                    Service Layer                                 │
│  ScheduledTaskService                                            │
│  - create_scheduled_task()                                       │
│  - update_scheduled_task()                                       │
│  - execute_scheduled_task()                                      │
│  - calculate_next_run_at()                                       │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────┼──────────────────────────────────────┐
│                  Scheduler Layer                                 │
│  Celery Beat (每分钟扫描一次)                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ check_and_execute_scheduled_tasks()                      │   │
│  │ - 查询 next_run_at <= now() 的任务                        │   │
│  │ - 执行任务（创建 GenerationTask）                         │   │
│  │ - 更新下次执行时间                                        │   │
│  └─────────────────────────────────────────────────────────┘   │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────┼──────────────────────────────────────┐
│                   Database Layer                                 │
│  scheduled_task 表                                               │
│  - 调度配置（schedule_type, schedule_config_json）               │
│  - 任务配置（material_id, template_ids_json, sub_user_ids_json）│
│  - 模型配置（复用 GenerationTask 配置）                          │
│  - 状态管理（is_active, status）                                 │
│  - 执行统计（total_executions, successful_executions, ...）      │
│  - 下次执行时间（next_run_at）                                    │
└─────────────────────────────────────────────────────────────────┘
```

### 2.3 数据流程

#### 2.3.1 创建定时任务流程

```
创作管理员 → API 创建请求 → Service 创建任务
  ↓
计算下次执行时间（next_run_at）
  ↓
保存到数据库（scheduled_task 表）
  ↓
返回任务详情
```

#### 2.3.2 定时任务执行流程

```
Celery Beat (每分钟)
  ↓
查询待执行任务（next_run_at <= now() AND is_active=1 AND status='active'）
  ↓
For each task:
  ├─ 创建 GenerationTask（复制配置）
  ├─ 创建关联（模板、创作者）
  ├─ 更新统计（total_executions += 1）
  └─ 计算下次执行时间（next_run_at）
  ↓
异步执行 GenerationTask（现有流程）
```

## 3. 数据库设计

### 3.1 表结构

```sql
CREATE TABLE scheduled_task (
    -- 主键
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    
    -- 基本信息
    name VARCHAR(200) NOT NULL COMMENT '定时任务名称',
    
    -- 调度配置
    schedule_type ENUM('daily', 'weekly') NOT NULL COMMENT '调度类型',
    schedule_config_json JSON NOT NULL COMMENT '调度配置JSON',
    
    -- 任务类型
    task_type ENUM('custom', 'benchmark') NOT NULL DEFAULT 'custom' COMMENT '任务类型',
    
    -- 素材和模板配置
    material_id BIGINT COMMENT '素材ID',
    template_ids_json JSON COMMENT '模板ID列表',
    sub_user_ids_json JSON NOT NULL COMMENT '目标创作者ID列表',
    
    -- 模型配置（复用 GenerationTask）
    model_platform VARCHAR(100) COMMENT '文本模型平台',
    model_id VARCHAR(100) COMMENT '文本模型ID',
    image_model_platform VARCHAR(100) COMMENT '图片模型平台',
    image_model_id VARCHAR(100) COMMENT '图片模型ID',
    model_selection_mode ENUM('auto', 'manual') NOT NULL DEFAULT 'auto',
    max_concurrency INT NOT NULL DEFAULT 5,
    image_count INT DEFAULT 4,
    
    -- 去重配置
    dedup_enabled BOOLEAN DEFAULT FALSE COMMENT '文案去重开关',
    dedup_threshold INT DEFAULT 90 COMMENT '文案去重阈值',
    dedup_retry_count INT DEFAULT 3 COMMENT '文案去重重试次数',
    dedup_scope JSON COMMENT '文案去重范围',
    
    image_dedup_enabled BOOLEAN DEFAULT FALSE COMMENT '图片去重开关',
    image_dedup_threshold INT DEFAULT 90 COMMENT '图片去重阈值',
    image_dedup_retry_count INT DEFAULT 3 COMMENT '图片去重重试次数',
    image_dedup_scope JSON COMMENT '图片去重范围',
    
    -- 对标配置
    benchmark_text_enabled BOOLEAN DEFAULT FALSE COMMENT '文案对标开关',
    benchmark_image_enabled BOOLEAN DEFAULT FALSE COMMENT '图片对标开关',
    benchmark_image_reference_options JSON COMMENT '图片参考选项',
    benchmark_image_roles_json JSON COMMENT '对标图角色配置',
    template_product_mapping_json JSON COMMENT '模板产品映射',
    
    -- 状态管理
    is_active BOOLEAN NOT NULL DEFAULT TRUE COMMENT '是否启用',
    status ENUM('active', 'paused', 'disabled') NOT NULL DEFAULT 'active',
    
    -- 执行统计
    total_executions INT NOT NULL DEFAULT 0 COMMENT '总执行次数',
    successful_executions INT NOT NULL DEFAULT 0 COMMENT '成功执行次数',
    failed_executions INT NOT NULL DEFAULT 0 COMMENT '失败执行次数',
    last_execution_at DATETIME COMMENT '最后执行时间',
    last_execution_status VARCHAR(50) COMMENT '最后执行状态',
    
    -- 下次执行时间
    next_run_at DATETIME COMMENT '下次执行时间',
    
    -- 多租户
    owner_operator_id BIGINT NOT NULL COMMENT '所属创作管理员ID',
    created_by BIGINT COMMENT '创建者ID',
    
    -- 时间戳
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- 外键
    FOREIGN KEY (material_id) REFERENCES material(id),
    FOREIGN KEY (owner_operator_id) REFERENCES operator(id),
    FOREIGN KEY (created_by) REFERENCES operator(id),
    
    -- 索引
    INDEX idx_owner_operator_id (owner_operator_id),
    INDEX idx_next_run_at (next_run_at),
    INDEX idx_status_active (is_active, status, next_run_at)
);
```

### 3.2 调度配置 JSON 格式

#### 每日调度（daily）

```json
{
    "times": ["09:00", "18:00"]
}
```

#### 每周调度（weekly）

```json
{
    "days": [1, 3, 5],  // 1=周一, 2=周二, ..., 7=周日
    "times": ["09:00"]
}
```

## 4. API 接口设计

### 4.1 创建定时任务

**POST** `/api/v1/scheduled-tasks`

请求体：
```json
{
    "name": "每日早间生成任务",
    "task_type": "custom",
    "schedule_type": "daily",
    "schedule_config_json": {
        "times": ["09:00"]
    },
    "material_id": 123,
    "template_ids_json": [1, 2, 3],
    "sub_user_ids_json": [10, 20, 30],
    "model_platform": "bailian",
    "model_id": "qwen-max",
    "image_model_platform": "bailian",
    "image_model_id": "wanx-v1",
    "model_selection_mode": "auto",
    "max_concurrency": 5,
    "image_count": 4,
    "dedup_enabled": true,
    "dedup_threshold": 90
}
```

响应：
```json
{
    "code": 200,
    "message": "创建成功",
    "data": {
        "id": 1,
        "name": "每日早间生成任务",
        "task_type": "custom",
        "schedule_type": "daily",
        "schedule_config_json": {"times": ["09:00"]},
        "next_run_at": "2026-05-16T09:00:00Z",
        "is_active": true,
        "status": "active",
        "total_executions": 0,
        "created_at": "2026-05-15T10:30:00Z"
    }
}
```

### 4.2 获取定时任务列表

**GET** `/api/v1/scheduled-tasks?page=1&limit=20&status=active`

响应：
```json
{
    "code": 200,
    "message": "获取成功",
    "data": {
        "items": [...],
        "total": 10,
        "page": 1,
        "limit": 20,
        "total_pages": 1
    }
}
```

### 4.3 获取定时任务详情

**GET** `/api/v1/scheduled-tasks/{task_id}`

### 4.4 更新定时任务

**PUT** `/api/v1/scheduled-tasks/{task_id}`

### 4.5 删除定时任务

**DELETE** `/api/v1/scheduled-tasks/{task_id}`

### 4.6 启用/禁用定时任务

**POST** `/api/v1/scheduled-tasks/{task_id}/toggle?is_active=true`

### 4.7 立即执行定时任务

**POST** `/api/v1/scheduled-tasks/{task_id}/execute`

## 5. 核心算法

### 5.1 下次执行时间计算

```python
def calculate_next_run_at(schedule_type: str, schedule_config: dict) -> datetime:
    """
    计算下次执行时间
    
    Args:
        schedule_type: 'daily' 或 'weekly'
        schedule_config: 调度配置
        
    Returns:
        下次执行时间（UTC）
    """
    now = datetime.utcnow()
    
    if schedule_type == "daily":
        # 找到下一个执行时间
        times = schedule_config.get("times", ["09:00"])
        next_times = []
        for time_str in times:
            hour, minute = map(int, time_str.split(":"))
            next_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_time <= now:
                next_time += timedelta(days=1)
            next_times.append(next_time)
        return min(next_times)
    
    elif schedule_type == "weekly":
        days = schedule_config.get("days", [1])  # 1=周一, 7=周日
        times = schedule_config.get("times", ["09:00"])
        
        next_times = []
        for day in days:
            for time_str in times:
                hour, minute = map(int, time_str.split(":"))
                target_weekday = day - 1  # 转换为 0=周一
                current_weekday = now.weekday()
                
                # 计算天数差
                days_ahead = target_weekday - current_weekday
                if days_ahead < 0:
                    days_ahead += 7
                elif days_ahead == 0:
                    # 同一天，检查时间
                    next_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                    if next_time <= now:
                        days_ahead = 7
                
                next_time = now + timedelta(days=days_ahead)
                next_time = next_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
                next_times.append(next_time)
        
        return min(next_times)
```

## 6. 失败处理和重试

### 6.1 任务执行失败处理

```python
@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def check_and_execute_scheduled_tasks(self):
    """Celery Beat 定时任务，每分钟执行一次"""
    try:
        # 执行任务
        ...
    except Exception as e:
        logger.error(f"执行失败: {e}")
        # 自动重试
        raise self.retry(exc=e)
```

### 6.2 失败通知

- 记录到日志（structured logging）
- 更新失败统计（failed_executions += 1）
- 可选：发送告警通知（邮件、钉钉等）

## 7. 性能优化

### 7.1 数据库查询优化

- 使用复合索引：`(is_active, status, next_run_at)`
- 查询时限制数量：`LIMIT 100`
- 使用 `selectinload` 预加载关联对象

### 7.2 并发控制

- 每分钟最多处理 100 个任务
- 使用分布式锁防止重复执行
- 支持多实例部署（Celery Beat 集群模式）

## 8. 监控和运维

### 8.1 监控指标

- 待执行任务数量
- 执行成功率
- 执行耗时
- 失败原因分布

### 8.2 运维工具

- Flower 监控 Celery 任务
- 自定义仪表盘展示定时任务状态
- 日志聚合和分析（ELK）

## 9. 安全考虑

### 9.1 权限控制

- 创作管理员只能管理自己的定时任务
- 超级管理员可以查看所有任务（但不能创建/修改）
- API 接口使用 JWT Token 认证

### 9.2 数据隔离

- 使用 `owner_operator_id` 实现多租户隔离
- 查询时强制添加租户过滤条件

## 10. 扩展性设计

### 10.1 未来扩展

- 支持更复杂的调度规则（每月、cron 表达式）
- 支持任务依赖和编排
- 支持任务执行历史查询
- 支持任务执行通知（微信、邮件）

### 10.2 插件化

- 任务执行器可以插件化
- 支持自定义任务类型
- 支持自定义通知渠道

## 11. 部署说明

### 11.1 启动 Celery Beat

```bash
# 启动 Celery Worker（处理异步任务）
celery -A app.tasks.celery_app worker --loglevel=info

# 启动 Celery Beat（定时调度）
celery -A app.tasks.celery_app beat --loglevel=info

# 或使用 celery multi 同时启动
celery -A app.tasks.celery_app multi start worker beat --loglevel=info
```

### 11.2 数据库迁移

```bash
# 执行数据库迁移
alembic upgrade head
```

## 12. 总结

本方案设计了一个完整的定时任务系统：

✅ **技术选型合理**：Celery Beat 与现有架构无缝集成
✅ **数据模型完善**：支持灵活的调度配置和任务管理
✅ **API 设计规范**：RESTful 风格，易于使用
✅ **性能优化到位**：索引优化、查询优化、并发控制
✅ **可扩展性强**：支持未来功能扩展
✅ **运维友好**：完善的监控和日志

该方案能够满足创作管理者对定时任务的核心需求，同时具备良好的可维护性和可扩展性。
