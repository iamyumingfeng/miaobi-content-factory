-- MySQL 数据库锁和连接池配置优化
--
-- 执行说明：
-- 1. 登录 MySQL: mysql -u root -p
-- 2. 选择数据库: USE aigc_platform;
-- 3. 执行此脚本: SOURCE /path/to/mysql_lock_optimization.sql;
--
-- 注意：部分参数需要修改 my.cnf 配置文件并重启 MySQL 生效

-- ============================================
-- 一、会话级配置（立即生效，无需重启）
-- ============================================

-- 查看当前锁等待超时设置（默认 50 秒）
SHOW VARIABLES LIKE 'innodb_lock_wait_timeout';

-- 设置锁等待超时为 30 秒（减少锁等待时间，快速失败）
-- 注意：这只是会话级设置，全局设置需要在 my.cnf 中配置
SET SESSION innodb_lock_wait_timeout = 30;

-- 查看当前事务隔离级别
SHOW VARIABLES LIKE 'transaction_isolation';

-- 确认使用 READ-COMMITTED（推荐，减少锁持有时间）
-- 注意：通常默认就是 READ-COMMITTED，无需修改

-- ============================================
-- 二、全局配置（需要修改 my.cnf 并重启）
-- ============================================

-- 查看当前连接数配置
SHOW VARIABLES LIKE 'max_connections';
SHOW VARIABLES LIKE 'max_user_connections';

-- 查看连接池相关配置
SHOW VARIABLES LIKE 'innodb_buffer_pool_size';
SHOW VARIABLES LIKE 'innodb_buffer_pool_instances';

-- ============================================
-- 三、推荐的 my.cnf 配置修改
-- ============================================
--
-- 应用层连接池配置（已更新）：
-- - pool_size = 50（核心连接）
-- - max_overflow = 30（溢出连接）
-- - 总计最大 80 个连接
--
-- 因此 MySQL max_connections 需要设置为 >= 100

--[mysqld]
--
-- 连接数配置（必须修改，支持应用连接池）
-- 公式：max_connections >= 应用pool_size + 应用max_overflow + 预留(20+)
--max_connections = 150
--max_user_connections = 140
--
-- InnoDB 缓冲池配置
-- 建议设置为物理内存的 60%-80%
--innodb_buffer_pool_size = 2G
--innodb_buffer_pool_instances = 4
--
-- 锁等待超时配置（秒）
-- 适当缩短超时时间，快速失败并重试
--innodb_lock_wait_timeout = 30
--
-- 事务隔离级别
--transaction_isolation = READ-COMMITTED
--
-- 连接超时配置
--wait_timeout = 28800
--interactive_timeout = 28800
--
-- InnoDB 并发配置
--innodb_thread_concurrency = 0  -- 0 表示自动调整
--innodb_locks_unsafe_for_binlog = 1  -- 减少锁持有时间（MySQL 8.0 已移除此参数）
--
-- 慢查询日志（用于排查问题）
--slow_query_log = 1
--slow_query_log_file = /var/log/mysql/slow.log
--long_query_time = 2

-- ============================================
-- 四、诊断查询（用于排查锁问题）
-- ============================================

-- 查看当前正在等待的锁
SELECT
    r.trx_id AS waiting_trx_id,
    r.trx_mysql_thread_id AS waiting_thread,
    r.trx_query AS waiting_query,
    b.trx_id AS blocking_trx_id,
    b.trx_mysql_thread_id AS blocking_thread,
    b.trx_query AS blocking_query
FROM information_schema.innodb_lock_waits w
JOIN information_schema.innodb_trx b ON b.trx_id = w.blocking_trx_id
JOIN information_schema.innodb_trx r ON r.trx_id = w.requesting_trx_id;

-- 查看当前活跃事务
SELECT
    trx_id,
    trx_state,
    trx_started,
    trx_mysql_thread_id,
    trx_query,
    TIMESTAMPDIFF(SECOND, trx_started, NOW()) AS duration_seconds
FROM information_schema.innodb_trx
ORDER BY trx_started;

-- 查看当前进程列表
SHOW FULL PROCESSLIST;

-- 查看 InnoDB 锁状态
SHOW ENGINE INNODB STATUS\G

-- ============================================
-- 五、定期清理和优化
-- ============================================

-- 查看表锁等待情况
SELECT
    OBJECT_SCHEMA,
    OBJECT_NAME,
    COUNT_LOCKS,
    COUNT_READ_LOCKS,
    COUNT_WRITE_LOCKS
FROM performance_schema.table_handles
WHERE OBJECT_SCHEMA = 'aigc_platform';

-- 查看元数据锁等待
SELECT
    OBJECT_TYPE,
    OBJECT_SCHEMA,
    OBJECT_NAME,
    LOCK_TYPE,
    LOCK_DURATION,
    LOCK_STATUS,
    OWNER_THREAD_ID
FROM performance_schema.metadata_locks
WHERE OBJECT_SCHEMA = 'aigc_platform';

-- ============================================
-- 六、应用层建议（代码层面）
-- ============================================

-- 1. 使用短事务：避免在事务中执行耗时操作（如 AI 模型调用）
-- 2. 批量插入时使用小批次：每批 10-20 条记录
-- 3. 外键关系：考虑是否真的需要外键约束（可改用应用层校验）
-- 4. 索引优化：确保查询使用索引，避免全表扫描
-- 5. 读写分离：高并发场景可考虑读写分离
-- 6. 连接池：应用层使用连接池（SQLAlchemy pool_size=20, max_overflow=10）

-- ============================================
-- 七、监控查询（定期执行）
-- ============================================

-- 查看连接使用情况
SELECT
    user,
    host,
    db,
    command,
    time,
    state,
    info
FROM information_schema.processlist
WHERE command != 'Sleep'
ORDER BY time DESC;

-- 查看 InnoDB 缓冲池命中率
SHOW STATUS LIKE 'Innodb_buffer_pool%';

-- 计算命中率：Innodb_buffer_pool_read_requests /
--            (Innodb_buffer_pool_read_requests + Innodb_buffer_pool_reads)
