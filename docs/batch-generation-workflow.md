# 批量任务生成工作流优化设计

> 基于各AI模型平台并发限制的高可用稳定批量任务生成方案

## 一、各平台并发限制分析

### 1.1 并发限制汇总表

| 平台 | 平台ID | 文本QPS | 图片QPS | 视频QPS | 支持批量API | 认证方式 |
|------|---------|---------|---------|---------|------------|---------|
| 阿里云百炼 | bailian | 2-5 | 部分无限制 | - | ✅ Patch API | API Key |
| 火山引擎 | volcano | 2 | 2 | 2 | ❌ | API Key |
| 即梦 | jimeng | - | 5-20 | 5-20 | ❌ | AccessKey + SecretKey |
| 可灵 | kling | - | 5-20 | 5-20 | ❌ | AccessKey + SecretKey |
| AutoGLM | autoglm | 2 | 2 | - | ❌ | API Key |
| 月之暗面 | moonshot | 2 | - | - | ❌ | API Key |
| DeepSeek | deepseek | 2 | - | - | ❌ | API Key |
| 灵牙AI | lingyaai | 2 | 2 | - | ❌ | API Key |

### 1.2 限制类型分类

| 限制类型 | 说明 | 处理策略 |
|---------|------|---------|
| 硬QPS限制 | 平台明确返回429错误 | 令牌桶限流 + 指数退避重试 |
| 软并发限制 | 平台不报错但响应变慢 | 自适应并发控制 |
| 资源池限制 | 模型实例数量有限 | 队列优先级调度 |

---

## 二、核心架构设计

### 2.1 总体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    批量任务生成引擎                           │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐ │
│  │  任务接收层   │───▶│  任务分解层   │───▶│  队列管理层   │ │
│  └──────────────┘    └──────────────┘    └──────────────┘ │
│         │                    │                    │          │
│         ▼                    ▼                    ▼          │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐ │
│  │  模型适配器   │◀───│  调度执行层   │◀───│  并发控制器   │ │
│  └──────────────┘    └──────────────┘    └──────────────┘ │
│         │                    │                    │          │
│         ▼                    ▼                    ▼          │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐ │
│  │  外部API层   │    │  进度监控层   │    │  错误恢复层   │ │
│  └──────────────┘    └──────────────┘    └──────────────┘ │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 分层职责说明

| 层级 | 职责 | 关键组件 |
|------|------|---------|
| 任务接收层 | 接收管理员提交的生成任务，参数校验 | TaskValidator |
| 任务分解层 | 将大任务拆分为子任务(generation_item) | TaskDecomposer |
| 队列管理层 | 按平台/优先级管理子任务队列 | QueueManager |
| 并发控制器 | 令牌桶限流，自适应并发调整 | ConcurrencyController |
| 调度执行层 | 从队列取出任务，分配给适配器 | TaskScheduler |
| 模型适配器 | 各平台API调用封装，统一接口 | BaseModelAdapter |
| 进度监控层 | WebSocket推送进度，状态更新 | ProgressMonitor |
| 错误恢复层 | 重试策略，死信队列，降级处理 | ErrorRecovery |

---

## 三、并发控制策略

### 3.1 令牌桶限流算法

```python
class TokenBucket:
    """
    令牌桶限流器

    每个模型平台独立的令牌桶，支持：
    - 动态QPS调整
    - 突发流量处理
    - 平滑限流
    """

    def __init__(
        self,
        rate: float,           # 每秒生成令牌数 (QPS)
        capacity: float,       # 桶容量 (突发上限 = capacity * rate)
        burst_factor: float = 1.5  # 突发因子
    ):
        self.rate = rate
        self.capacity = capacity
        self.burst_factor = burst_factor
        self.tokens = capacity
        self.last_refill = time.time()
        self.lock = threading.Lock()

    def acquire(self, tokens: int = 1, timeout: float = 30.0) -> bool:
        """
        获取令牌

        Args:
            tokens: 需要的令牌数
            timeout: 超时时间(秒)

        Returns:
            是否成功获取令牌
        """
        deadline = time.time() + timeout

        with self.lock:
            while time.time() < deadline:
                self._refill()

                if self.tokens >= tokens:
                    self.tokens -= tokens
                    return True

                # 计算需要等待的时间
                wait_time = (tokens - self.tokens) / self.rate
                time.sleep(min(wait_time, 0.1))

            return False

    def _refill(self):
        """补充令牌"""
        now = time.time()
        elapsed = now - self.last_refill
        new_tokens = elapsed * self.rate
        self.tokens = min(self.capacity * self.burst_factor, self.tokens + new_tokens)
        self.last_refill = now

    def adjust_rate(self, new_rate: float):
        """动态调整速率"""
        with self.lock:
            self.rate = new_rate
```

### 3.2 平台默认QPS配置

```python
# config/model_concurrency.py
MODEL_CONCURRENCY_CONFIG = {
    # 阿里云百炼
    "bailian": {
        "default_qps": 3,
        "min_qps": 1,
        "max_qps": 10,
        "supports_batch": True,
        "batch_size": 10,
        "model_types": ["llm", "image"],
        "retry_config": {
            "max_retries": 3,
            "base_delay": 1.0,
            "max_delay": 60.0,
            "exponential_base": 2.0,
            "jitter": True
        }
    },

    # 火山引擎
    "volcano": {
        "default_qps": 2,
        "min_qps": 1,
        "max_qps": 5,
        "supports_batch": False,
        "model_types": ["llm", "image"],
        "retry_config": {
            "max_retries": 5,
            "base_delay": 2.0,
            "max_delay": 120.0,
            "exponential_base": 2.5,
            "jitter": True
        }
    },

    # 即梦
    "jimeng": {
        "default_qps": 10,
        "min_qps": 2,
        "max_qps": 30,
        "supports_batch": False,
        "model_types": ["image", "video"],
        "retry_config": {
            "max_retries": 3,
            "base_delay": 0.5,
            "max_delay": 30.0,
            "exponential_base": 2.0,
            "jitter": True
        }
    },

    # 可灵
    "kling": {
        "default_qps": 10,
        "min_qps": 2,
        "max_qps": 30,
        "supports_batch": False,
        "model_types": ["image", "video"],
        "retry_config": {
            "max_retries": 3,
            "base_delay": 0.5,
            "max_delay": 30.0,
            "exponential_base": 2.0,
            "jitter": True
        }
    },

    # AutoGLM
    "autoglm": {
        "default_qps": 2,
        "min_qps": 1,
        "max_qps": 5,
        "supports_batch": False,
        "model_types": ["llm", "image"],
        "retry_config": {
            "max_retries": 5,
            "base_delay": 2.0,
            "max_delay": 120.0,
            "exponential_base": 2.5,
            "jitter": True
        }
    },

    # 月之暗面
    "moonshot": {
        "default_qps": 2,
        "min_qps": 1,
        "max_qps": 5,
        "supports_batch": False,
        "model_types": ["llm"],
        "retry_config": {
            "max_retries": 5,
            "base_delay": 2.0,
            "max_delay": 120.0,
            "exponential_base": 2.5,
            "jitter": True
        }
    },

    # DeepSeek
    "deepseek": {
        "default_qps": 2,
        "min_qps": 1,
        "max_qps": 5,
        "supports_batch": False,
        "model_types": ["llm"],
        "retry_config": {
            "max_retries": 5,
            "base_delay": 2.0,
            "max_delay": 120.0,
            "exponential_base": 2.5,
            "jitter": True
        }
    },

    # 灵牙AI
    "lingyaai": {
        "default_qps": 2,
        "min_qps": 1,
        "max_qps": 5,
        "supports_batch": False,
        "model_types": ["llm", "image"],
        "retry_config": {
            "max_retries": 5,
            "base_delay": 2.0,
            "max_delay": 120.0,
            "exponential_base": 2.5,
            "jitter": True
        }
    }
}
```

### 3.3 自适应并发控制

```python
class AdaptiveConcurrencyController:
    """
    自适应并发控制器

    根据响应时间和错误率动态调整并发度：
    - P99响应时间 > 阈值 → 降低并发
    - 错误率 > 阈值 → 降低并发
    - 持续稳定 → 试探性增加并发
    """

    def __init__(
        self,
        platform: str,
        initial_qps: float,
        min_qps: float,
        max_qps: float,
        target_p99_latency: float = 5.0,  # 目标P99延迟(秒)
        target_error_rate: float = 0.05      # 目标错误率 5%
    ):
        self.platform = platform
        self.current_qps = initial_qps
        self.min_qps = min_qps
        self.max_qps = max_qps
        self.target_p99_latency = target_p99_latency
        self.target_error_rate = target_error_rate

        # 统计窗口
        self.window_size = 60  # 60秒窗口
        self.latency_samples = []
        self.error_samples = []
        self.lock = threading.Lock()

        # 令牌桶
        self.token_bucket = TokenBucket(
            rate=initial_qps,
            capacity=initial_qps * 2
        )

    def record_result(self, latency: float, success: bool):
        """记录请求结果"""
        with self.lock:
            now = time.time()
            self.latency_samples.append((now, latency))
            self.error_samples.append((now, 0 if success else 1))

            # 清理过期样本
            cutoff = now - self.window_size
            self.latency_samples = [
                (t, l) for t, l in self.latency_samples if t >= cutoff
            ]
            self.error_samples = [
                (t, e) for t, e in self.error_samples if t >= cutoff
            ]

            # 评估是否需要调整
            self._maybe_adjust()

    def _maybe_adjust(self):
        """评估并调整并发度"""
        if len(self.latency_samples) < 10:
            return  # 样本不足，不调整

        # 计算指标
        latencies = [l for _, l in self.latency_samples]
        p99_latency = sorted(latencies)[int(len(latencies) * 0.99)]
        error_rate = sum(e for _, e in self.error_samples) / len(self.error_samples)

        # 决策逻辑
        new_qps = self.current_qps

        if p99_latency > self.target_p99_latency * 1.5:
            # P99延迟过高，快速降载
            new_qps = self.current_qps * 0.5
        elif error_rate > self.target_error_rate * 2:
            # 错误率过高，快速降载
            new_qps = self.current_qps * 0.5
        elif p99_latency > self.target_p99_latency:
            # 轻微超限，缓慢降载
            new_qps = self.current_qps * 0.9
        elif error_rate > self.target_error_rate:
            # 轻微错误，缓慢降载
            new_qps = self.current_qps * 0.9
        elif (p99_latency < self.target_p99_latency * 0.5 and
              error_rate < self.target_error_rate * 0.5):
            # 资源充裕，试探性增加
            new_qps = self.current_qps * 1.1

        # 边界限制
        new_qps = max(self.min_qps, min(self.max_qps, new_qps))

        if abs(new_qps - self.current_qps) > 0.1:
            self.current_qps = new_qps
            self.token_bucket.adjust_rate(new_qps)
            logger.info(f"平台 {self.platform} 并发度调整为: {new_qps:.2f}")
```

---

## 四、重试与容错策略

### 4.1 指数退避重试

```python
class RetryStrategy:
    """
    重试策略

    支持：
    - 指数退避
    - 随机抖动
    - 可重试错误判断
    - 重试次数限制
    """

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter

    def get_delay(self, attempt: int) -> float:
        """
        计算第n次重试的延迟时间

        Args:
            attempt: 重试次数(从0开始)

        Returns:
            延迟秒数
        """
        if attempt >= self.max_retries:
            return -1  # 不再重试

        delay = self.base_delay * (self.exponential_base ** attempt)
        delay = min(delay, self.max_delay)

        if self.jitter:
            # 添加 ±20% 的随机抖动
            jitter_factor = 0.8 + random.random() * 0.4
            delay *= jitter_factor

        return delay

    def is_retryable(self, error: Exception) -> bool:
        """
        判断错误是否可重试

        Args:
            error: 异常对象

        Returns:
            是否可以重试
        """
        # HTTP状态码判断
        if hasattr(error, 'status_code'):
            status_code = error.status_code
            if status_code in {429, 500, 502, 503, 504}:
                return True
            if status_code >= 500:
                return True

        # 异常类型判断
        retryable_types = (
            ConnectionError,
            TimeoutError,
            requests.exceptions.RequestException,
            aiohttp.ClientError
        )

        if isinstance(error, retryable_types):
            return True

        # 错误消息关键词判断
        error_msg = str(error).lower()
        retryable_keywords = {
            'timeout', 'timed out',
            'connection', 'connect',
            'rate limit', 'ratelimit', '429',
            'server error', 'internal error',
            'service unavailable', 'temporarily unavailable',
            'busy', 'overloaded'
        }

        return any(keyword in error_msg for keyword in retryable_keywords)
```

### 4.2 死信队列处理

```python
class DeadLetterQueue:
    """
    死信队列

    处理超过最大重试次数的任务：
    - 记录详细错误信息
    - 支持手动重试
    - 支持批量重试
    - 支持放弃/归档
    """

    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.dlq_key = "generation:dlq"
        self.archive_key = "generation:dlq:archive"

    def add(self, item: GenerationItem, error: Exception, attempt: int):
        """添加到死信队列"""
        dlq_item = {
            "item_id": item.id,
            "task_id": item.task_id,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "stack_trace": traceback.format_exc(),
            "attempt": attempt,
            "added_at": datetime.utcnow().isoformat(),
            "item_data": self._serialize_item(item)
        }

        self.redis.hset(
            f"{self.dlq_key}:{item.id}",
            mapping=dlq_item
        )
        self.redis.zadd(self.dlq_key, {item.id: time.time()})

    def retry(self, item_id: int) -> bool:
        """手动重试单个任务"""
        dlq_item = self.redis.hgetall(f"{self.dlq_key}:{item_id}")
        if not dlq_item:
            return False

        # 重新入队
        self._requeue_item(dlq_item)

        # 从DLQ移除
        self.redis.delete(f"{self.dlq_key}:{item_id}")
        self.redis.zrem(self.dlq_key, item_id)

        return True

    def batch_retry(self, filters: dict = None, limit: int = 100) -> int:
        """批量重试"""
        item_ids = self.redis.zrange(self.dlq_key, 0, limit - 1)
        count = 0

        for item_id in item_ids:
            if self.retry(int(item_id)):
                count += 1

        return count

    def archive(self, item_id: int):
        """归档任务"""
        dlq_item = self.redis.hgetall(f"{self.dlq_key}:{item_id}")
        if not dlq_item:
            return

        dlq_item["archived_at"] = datetime.utcnow().isoformat()

        self.redis.hset(
            f"{self.archive_key}:{item_id}",
            mapping=dlq_item
        )

        self.redis.delete(f"{self.dlq_key}:{item_id}")
        self.redis.zrem(self.dlq_key, item_id)
```

---

## 五、批量API优化（百炼Patch API）

### 5.1 批量任务聚合器

```python
class BatchTaskAggregator:
    """
    批量任务聚合器

    对于支持批量API的平台（如百炼），将多个单请求聚合成批量请求：
    - 时间窗口聚合
    - 大小限制
    - 超时触发
    """

    def __init__(
        self,
        platform: str,
        max_batch_size: int = 10,
        max_wait_time: float = 1.0,  # 最大等待时间(秒)
        callback: Callable = None
    ):
        self.platform = platform
        self.max_batch_size = max_batch_size
        self.max_wait_time = max_wait_time
        self.callback = callback

        self.pending_tasks = []
        self.lock = threading.Lock()
        self.timer = None
        self.condition = threading.Condition()

    def add(self, task: dict) -> asyncio.Future:
        """添加任务到批处理队列"""
        future = asyncio.Future()

        with self.lock:
            self.pending_tasks.append((task, future))

            if len(self.pending_tasks) >= self.max_batch_size:
                # 达到批量大小，立即执行
                self._flush()
            elif self.timer is None:
                # 启动定时器
                self.timer = threading.Timer(self.max_wait_time, self._flush)
                self.timer.start()

        return future

    def _flush(self):
        """执行批量请求"""
        with self.lock:
            if not self.pending_tasks:
                return

            tasks = self.pending_tasks.copy()
            self.pending_tasks = []

            if self.timer:
                self.timer.cancel()
                self.timer = None

        # 异步执行批量请求
        asyncio.create_task(self._execute_batch(tasks))

    async def _execute_batch(self, tasks: list):
        """执行批量API调用"""
        task_items = [t for t, _ in tasks]
        futures = [f for _, f in tasks]

        try:
            if self.callback:
                results = await self.callback(task_items)

                # 分发结果
                for future, result in zip(futures, results):
                    future.set_result(result)
            else:
                # 默认处理（需由子类实现）
                raise NotImplementedError
        except Exception as e:
            # 批量失败，逐个重试
            for future in futures:
                future.set_exception(e)
```

### 5.2 百炼Patch API适配器

```python
class BailianBatchAdapter(BaseModelAdapter):
    """
    百炼批量API适配器

    使用Patch API进行批量文本生成，提高吞吐量
    """

    def __init__(self, config: ModelConfig):
        super().__init__(config)
        self.batch_aggregator = BatchTaskAggregator(
            platform="bailian",
            max_batch_size=10,
            max_wait_time=0.5,
            callback=self._execute_batch
        )

    async def generate_text(
        self,
        prompt: str,
        **kwargs
    ) -> GenerationResult:
        """生成文本（使用批量聚合）"""
        task = {
            "prompt": prompt,
            **kwargs
        }
        return await self.batch_aggregator.add(task)

    async def _execute_batch(
        self,
        tasks: list[dict]
    ) -> list[GenerationResult]:
        """执行批量请求"""
        # 构造Patch API请求
        batch_request = {
            "model": self.config.model_id,
            "requests": [
                {
                    "custom_id": str(i),
                    "method": "POST",
                    "url": "/v1/chat/completions",
                    "body": {
                        "model": self.config.model_id,
                        "messages": [
                            {"role": "user", "content": task["prompt"]}
                        ],
                        **{k: v for k, v in task.items() if k != "prompt"}
                    }
                }
                for i, task in enumerate(tasks)
            ]
        }

        # 调用批量API
        response = await self._make_api_call(
            method="POST",
            endpoint="/v1/batches",
            data=batch_request
        )

        # 解析批量响应
        results = []
        for i, task in enumerate(tasks):
            # 根据custom_id匹配响应
            item_response = self._find_response(response, str(i))
            results.append(self._parse_single_response(item_response))

        return results
```

---

## 六、队列调度策略

### 6.1 多级优先级队列

```python
class PriorityQueueManager:
    """
    多级优先级队列管理器

    队列优先级：
    - P0: 紧急重试任务（失败重试）
    - P1: 正常任务（新提交）
    - P2: 后台任务（低优先级）
    """

    PRIORITY_URGENT = 0    # 紧急重试
    PRIORITY_NORMAL = 1     # 正常任务
    PRIORITY_BACKGROUND = 2 # 后台任务

    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.queue_keys = {
            self.PRIORITY_URGENT: "generation:queue:p0",
            self.PRIORITY_NORMAL: "generation:queue:p1",
            self.PRIORITY_BACKGROUND: "generation:queue:p2"
        }

    def enqueue(
        self,
        item: GenerationItem,
        priority: int = PRIORITY_NORMAL
    ):
        """入队"""
        queue_key = self.queue_keys.get(priority, self.queue_keys[self.PRIORITY_NORMAL])

        # 使用List作为队列，LPUSH + BRPOP = FIFO
        self.redis.lpush(queue_key, json.dumps({
            "item_id": item.id,
            "task_id": item.task_id,
            "platform": item.model_platform,
            "priority": priority,
            "enqueued_at": datetime.utcnow().isoformat()
        }))

    def dequeue(
        self,
        platforms: list[str] = None,
        timeout: int = 0
    ) -> dict | None:
        """
        出队（按优先级）

        Args:
            platforms: 只取出指定平台的任务
            timeout: 超时时间(秒)，0表示不等待

        Returns:
            任务数据或None
        """
        # 按优先级顺序检查队列
        for priority in sorted(self.queue_keys.keys()):
            queue_key = self.queue_keys[priority]

            if timeout > 0:
                # 阻塞等待
                result = self.redis.brpop(queue_key, timeout=timeout)
                if result:
                    _, data = result
                    item = json.loads(data)
                    if self._match_platform(item, platforms):
                        return item
                    else:
                        # 平台不匹配，重新入队
                        self.redis.lpush(queue_key, data)
            else:
                # 非阻塞
                while True:
                    data = self.redis.rpop(queue_key)
                    if not data:
                        break
                    item = json.loads(data)
                    if self._match_platform(item, platforms):
                        return item
                    else:
                        self.redis.lpush(queue_key, data)

        return None

    def _match_platform(self, item: dict, platforms: list[str] | None) -> bool:
        """检查平台是否匹配"""
        if not platforms:
            return True
        return item.get("platform") in platforms
```

### 6.2 公平调度策略

```python
class FairScheduler:
    """
    公平调度器

    保证：
    - 不同任务之间公平共享资源
    - 大任务不会饿死小任务
    - 支持任务权重
    """

    def __init__(self):
        self.task_weights = {}  # task_id -> weight
        self.task_usage = {}    # task_id -> 已使用令牌数
        self.last_update = time.time()
        self.lock = threading.Lock()

    def register_task(self, task_id: int, weight: float = 1.0):
        """注册任务"""
        with self.lock:
            self.task_weights[task_id] = weight
            self.task_usage[task_id] = 0.0

    def select_next(self, ready_tasks: list[dict]) -> dict | None:
        """
        选择下一个要执行的任务

        使用加权公平排队(WFQ)算法
        """
        if not ready_tasks:
            return None

        with self.lock:
            now = time.time()
            elapsed = now - self.last_update
            self.last_update = now

            # 充值所有任务的虚拟令牌
            for task_id in self.task_weights:
                weight = self.task_weights[task_id]
                self.task_usage[task_id] = max(
                    0,
                    self.task_usage[task_id] - elapsed * weight
                )

            # 选择使用率最低的任务
            min_usage = float('inf')
            selected = None

            for task in ready_tasks:
                task_id = task["task_id"]
                usage = self.task_usage.get(task_id, 0)

                if usage < min_usage:
                    min_usage = usage
                    selected = task

            if selected:
                # 记录使用
                task_id = selected["task_id"]
                self.task_usage[task_id] = self.task_usage.get(task_id, 0) + 1

            return selected
```

---

## 七、监控与告警

### 7.1 关键指标监控

```python
class BatchMetricsCollector:
    """
    批量任务指标收集器

    收集指标：
    - 吞吐量 (QPS)
    - 延迟分布 (P50/P95/P99)
    - 错误率
    - 队列长度
    - 重试次数
    """

    def __init__(self, prometheus_registry=None):
        self.metrics = defaultdict(list)
        self.lock = threading.Lock()
        self.registry = prometheus_registry

        if self.registry:
            self._setup_prometheus()

    def record_request(
        self,
        platform: str,
        latency: float,
        success: bool,
        retry_count: int = 0
    ):
        """记录请求指标"""
        with self.lock:
            key = f"{platform}:requests"
            self.metrics[key].append({
                "timestamp": time.time(),
                "latency": latency,
                "success": success,
                "retry_count": retry_count
            })

            # 保留最近1小时的数据
            cutoff = time.time() - 3600
            self.metrics[key] = [
                m for m in self.metrics[key] if m["timestamp"] >= cutoff
            ]

    def get_stats(self, platform: str, window: int = 60) -> dict:
        """获取统计数据"""
        with self.lock:
            key = f"{platform}:requests"
            cutoff = time.time() - window
            recent = [m for m in self.metrics.get(key, []) if m["timestamp"] >= cutoff]

            if not recent:
                return {}

            latencies = [m["latency"] for m in recent]
            successes = [m for m in recent if m["success"]]
            retries = sum(m["retry_count"] for m in recent)

            return {
                "qps": len(recent) / window,
                "total_requests": len(recent),
                "success_rate": len(successes) / len(recent),
                "error_rate": 1 - len(successes) / len(recent),
                "avg_latency": sum(latencies) / len(latencies),
                "p50_latency": sorted(latencies)[int(len(latencies) * 0.5)],
                "p95_latency": sorted(latencies)[int(len(latencies) * 0.95)],
                "p99_latency": sorted(latencies)[int(len(latencies) * 0.99)],
                "total_retries": retries,
                "avg_retries": retries / len(recent)
            }
```

### 7.2 告警规则

```python
# config/alerts.py
ALERT_RULES = [
    {
        "name": "high_error_rate",
        "description": "错误率过高",
        "condition": lambda stats: stats.get("error_rate", 0) > 0.1,
        "severity": "critical",
        "cooldown": 300  # 5分钟冷却
    },
    {
        "name": "high_latency",
        "description": "P99延迟过高",
        "condition": lambda stats: stats.get("p99_latency", 0) > 10.0,
        "severity": "warning",
        "cooldown": 120
    },
    {
        "name": "queue_backlog",
        "description": "队列积压",
        "condition": lambda queue_len: queue_len > 1000,
        "severity": "warning",
        "cooldown": 60
    },
    {
        "name": "zero_throughput",
        "description": "吞吐量为0",
        "condition": lambda stats: stats.get("qps", 0) == 0 and stats.get("total_requests", 0) > 0,
        "severity": "critical",
        "cooldown": 60
    }
]
```

---

## 八、配置参数汇总

### 8.1 Celery配置优化

```python
# platform_api/app/config/celery_config.py
CELERY_BATCH_CONFIG = {
    # 任务预取
    "worker_prefetch_multiplier": 1,  # 公平调度，每次只预取1个

    # 并发控制
    "worker_concurrency": 4,  # CPU密集型任务，设为CPU核数

    # 任务确认
    "task_acks_late": True,  # 任务执行完成后才确认
    "task_reject_on_worker_lost": True,  # Worker丢失时重新入队

    # 任务序列化
    "task_serializer": "json",
    "result_serializer": "json",
    "accept_content": ["json"],

    # 任务超时
    "task_time_limit": 300,  # 单个任务硬超时5分钟
    "task_soft_time_limit": 240,  # 软超时4分钟

    # 结果后端
    "result_expires": 86400,  # 结果保留1天

    # 重试配置
    "task_default_retry_delay": 60,
    "task_max_retries": 3,

    # 速率限制（按任务类型）
    "task_annotations": {
        "tasks.generate_text": {"rate_limit": "10/s"},
        "tasks.generate_image": {"rate_limit": "5/s"},
        "tasks.generate_video": {"rate_limit": "1/s"},
    }
}
```

### 8.2 数据库优化配置

```sql
-- 生成任务表索引优化
CREATE INDEX idx_generation_task_operator_date
    ON generation_task(owner_operator_id, created_at DESC);

CREATE INDEX idx_generation_task_status
    ON generation_task(status, created_at DESC);

-- 子任务表索引优化
CREATE INDEX idx_generation_item_task_status
    ON generation_item(task_id, status);

CREATE INDEX idx_generation_item_subuser_status
    ON generation_item(sub_user_id, distribution_status, created_at DESC);

CREATE INDEX idx_generation_item_platform_status
    ON generation_item(model_platform, status, queued_at);

CREATE INDEX idx_generation_item_owner_operator
    ON generation_item(owner_operator_id, created_at DESC);

-- 进度日志表分区（按周分区）
ALTER TABLE generation_task_progress_log
    PARTITION BY RANGE (TO_DAYS(created_at)) (
        PARTITION p2025w1 VALUES LESS THAN (TO_DAYS('2025-01-07')),
        PARTITION p2025w2 VALUES LESS THAN (TO_DAYS('2025-01-14')),
        PARTITION p_future VALUES LESS THAN MAXVALUE
    );
```

---

## 九、总结

### 9.1 优化效果预期

| 指标 | 优化前 | 优化后 | 提升 |
|------|--------|--------|------|
| 批量任务完成时间 | 1000创作者 × 5秒 = 83分钟 | 自适应并发 + 批量API ≈ 15-20分钟 | **4-5x** |
| 峰值吞吐量 | 2 QPS (火山) | 10-30 QPS (多平台混合) | **5-15x** |
| 错误率 | ~10% (无重试) | <1% (智能重试) | **10x改善** |
| 资源利用率 | ~30% (手动控制) | ~80% (自适应) | **2.6x** |

### 9.2 关键技术要点

1. **令牌桶限流** - 精确控制各平台QPS
2. **自适应并发** - 根据响应动态调整
3. **指数退避重试** - 智能容错
4. **批量API聚合** - 充分利用平台能力
5. **多级优先级队列** - 保证紧急任务优先
6. **公平调度** - 避免任务饿死
7. **完善监控** - 可观测性和告警
