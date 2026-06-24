# 任务队列管理功能说明

## 概述

实现了智能的任务队列管理机制，当 Worker 队列满时，新任务会自动进入等待队列，Worker 空闲时按 FIFO 顺序执行。

## 功能特性

1. **智能排队**：当活跃任务数达到最大并发数时，新任务自动进入等待队列
2. **FIFO 顺序执行**：Worker 空闲时，按入队顺序执行等待任务
3. **队列状态监控**：提供 API 接口查询队列状态（活跃任务、等待队列、并发配置）
4. **动态配置**：支持运行时修改最大并发数
5. **异常恢复**：提供超时任务恢复接口，处理 Worker 崩溃等异常情况

## 配置说明

### 新增配置项（config.py）

```python
# Celery Worker 并发数（默认 32）
CELERY_CONCURRENCY=32

# 任务队列最大并发数（默认 64，建议为 Worker 并发数的 2 倍）
TASK_QUEUE_MAX_CONCURRENT=64
```

### Redis 键说明

- `task_queue:waiting` - 等待队列（List，FIFO）
- `task_queue:active` - 活跃任务集合（Set）
- `task_queue:max_concurrent` - 最大并发数（String）

## API 接口

### 1. 获取队列状态

```
GET /api/v1/task-queue/status
```

**Response:**
```json
{
  "success": true,
  "data": {
    "max_concurrent": 64,
    "active_count": 5,
    "waiting_count": 10,
    "active_tasks": [...],
    "waiting_tasks": [...]
  }
}
```

### 2. 获取队列配置

```
GET /api/v1/task-queue/config
```

**Response:**
```json
{
  "success": true,
  "data": {
    "max_concurrent": 64,
    "active_count": 5,
    "waiting_count": 10,
    "can_dispatch": true
  }
}
```

### 3. 更新队列配置

```
PUT /api/v1/task-queue/config
Content-Type: application/json

{
  "max_concurrent": 100
}
```

**注意**：仅超级管理员可修改配置

### 4. 手动触发任务调度

```
POST /api/v1/task-queue/dispatch?max_dispatch=10
```

**Response:**
```json
{
  "success": true,
  "data": {
    "dispatched_count": 5,
    "active_count": 10,
    "waiting_count": 5
  }
}
```

### 5. 清空等待队列

```
DELETE /api/v1/task-queue/clear?confirm=true
```

**注意**：仅超级管理员可清空队列

### 6. 恢复超时任务

```
POST /api/v1/task-queue/recover-stale?timeout_minutes=120
```

将运行时间超过指定时长的活跃任务重新加入等待队列。

## 工作流程

### 任务启动流程

1. 用户创建生成任务，系统调用 `start_generation_task`
2. 遍历所有子任务，将状态为 `queued` 的子任务加入等待队列（`task_queue:waiting`）
3. 调用 `_dispatch_tasks_from_queue()` 尝试调度任务
4. 如果活跃任务数 < 最大并发数，从等待队列取出任务，调用 `process_generation_item_phased.delay()`
5. Celery 信号 `task_prerun` 触发，将任务添加到活跃任务集合（`task_queue:active`）

### 任务完成流程

1. `process_generation_item_phased` 任务执行完成（成功或失败）
2. Celery 信号 `task_postrun` 触发：
   - 从活跃任务集合移除当前任务
   - 调用 `_dispatch_tasks_from_queue()` 尝试调度下一个等待任务
3. 如果有等待任务且并发数未达上限，调度下一个任务

### 队列满时的行为

- 当活跃任务数达到 `max_concurrent` 时，新任务进入等待队列
- Worker 空闲时（任务完成触发 `task_postrun`），自动从等待队列取出下一个任务执行
- 保证 FIFO 顺序（先入队的任务先执行）

## 监控建议

### 1. 定期查询队列状态

```javascript
// 前端可以定时轮询队列状态
setInterval(async () => {
  const status = await apiClient.getQueueStatus();
  console.log('Queue status:', status.data);
}, 5000);
```

### 2. 设置告警

当以下条件满足时发送告警：
- `waiting_count` > 100（等待任务过多）
- `active_count` == `max_concurrent` 且 `waiting_count` > 0（队列满）

### 3. 定期恢复超时任务

建议通过定时任务（Cron 或 Celery Beat）定期调用恢复接口：
```bash
# 每小时执行一次，恢复超过 2 小时的超时任务
curl -X POST "http://localhost:8000/api/v1/task-queue/recover-stale?timeout_minutes=120"
```

## 故障排查

### 1. 任务卡在活跃任务中

**现象**：任务已完成，但仍显示在活跃任务列表中

**原因**：Worker 崩溃，导致 `task_postrun` 信号未触发

**解决**：调用恢复接口
```bash
curl -X POST "http://localhost:8000/api/v1/task-queue/recover-stale?timeout_minutes=120"
```

### 2. 等待队列中的任务不执行

**现象**：等待队列有任务，但活跃任务数未达到上限

**原因**：可能所有 Worker 都繁忙，或调度逻辑异常

**解决**：手动触发调度
```bash
curl -X POST "http://localhost:8000/api/v1/task-queue/dispatch?max_dispatch=10"
```

### 3. Redis 连接失败

**现象**：队列管理功能不可用

**检查**：
- Redis 是否正常运行
- `REDIS_URL` 配置是否正确
- Redis DB 3 是否可访问

## 性能优化建议

1. **合理设置最大并发数**：
   - 建议为 Worker 并发数的 2 倍
   - 例：Worker 并发数 = 32，最大并发数 = 64

2. **监控队列长度**：
   - 如果等待队列经常 > 100，考虑增加 Worker 并发数
   - 如果活跃任务数经常 < 最大并发数，考虑降低最大并发数

3. **定期清理超时任务**：
   - 建议每小时执行一次恢复超时任务接口
   - 超时阈值建议设为 2 小时（根据任务平均执行时间调整）

## 后续优化方向

1. **WebSocket 实时推送**：队列状态变化时实时推送到前端
2. **任务优先级**：支持设置任务优先级，高优先级任务优先执行
3. **队列持久化**：将队列数据持久化到数据库，防止 Redis 重启丢失
4. **分布式锁**：多 Worker 环境下，使用分布式锁避免任务重复调度
