"""
平台表架构拆分：统一架构 → 独立架构

将 CategoryPlatform 统一平台表拆分为 MaterialPlatform + TemplatePlatform。

Revision ID: 20250120_1000
Revises: 20260416_1501
Create Date: 2025-01-20 10:00:00

迁移策略：
  1. 创建 material_platform 表（如果不存在）
  2. 扩展 template_platform 表（添加字段，如果不存在）
  3. 迁移数据（category_platform → 两个独立平台表）
  4. 为分类表添加新外键列，迁移数据
  5. 删除旧的外键列
  6. 删除旧的统一平台表
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text

# revision identifiers
revision = '20250120_1000'
down_revision = '20260416_1501'
branch_labels = None
depends_on = None


def table_exists(conn, table_name):
    """检查表是否存在"""
    result = conn.execute(text("""
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = DATABASE() AND table_name = :table_name
    """), {'table_name': table_name}).fetchone()
    return result is not None


def column_exists(conn, table_name, column_name):
    """检查列是否存在"""
    result = conn.execute(text("""
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = DATABASE() 
        AND table_name = :table_name 
        AND column_name = :column_name
    """), {'table_name': table_name, 'column_name': column_name}).fetchone()
    return result is not None


def constraint_exists(conn, table_name, constraint_name):
    """检查约束是否存在"""
    result = conn.execute(text("""
        SELECT 1 FROM information_schema.table_constraints 
        WHERE table_schema = DATABASE() 
        AND table_name = :table_name 
        AND constraint_name = :constraint_name
    """), {'table_name': table_name, 'constraint_name': constraint_name}).fetchone()
    return result is not None


def index_exists(conn, table_name, index_name):
    """检查索引是否存在"""
    result = conn.execute(text("""
        SELECT 1 FROM information_schema.statistics 
        WHERE table_schema = DATABASE() 
        AND table_name = :table_name 
        AND index_name = :index_name
    """), {'table_name': table_name, 'index_name': index_name}).fetchone()
    return result is not None


def upgrade():
    conn = op.get_bind()
    
    # ================================================================
    # 阶段1: 创建 material_platform 表
    # ================================================================
    if not table_exists(conn, 'material_platform'):
        op.create_table(
            'material_platform',
            sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
            sa.Column('name', sa.String(100), nullable=False, comment='平台名称'),
            sa.Column('description', sa.String(500), nullable=True, comment='平台描述'),
            sa.Column('color', sa.String(20), nullable=True, comment='平台颜色'),
            sa.Column('platform_code', sa.String(50), nullable=True, comment='平台代码（如 xhs, dy）'),
            sa.Column('config_json', sa.JSON(), nullable=True, comment='平台配置JSON（预留扩展）'),
            sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0', comment='排序权重'),
            sa.Column('created_by', sa.BigInteger(), sa.ForeignKey('operator.id'), nullable=True, comment='创建者运营管理员ID'),
            sa.Column('owner_operator_id', sa.BigInteger(), sa.ForeignKey('operator.id'), nullable=False, comment='所属运营管理员ID'),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('owner_operator_id', 'name', name='uq_material_platform_owner_name')
        )
        op.create_index('ix_material_platform_owner', 'material_platform', ['owner_operator_id'])

    # ================================================================
    # 阶段2: 扩展 template_platform 表
    # ================================================================
    # 添加扩展字段（如果不存在）
    if not column_exists(conn, 'template_platform', 'platform_code'):
        op.add_column('template_platform', sa.Column('platform_code', sa.String(50), nullable=True, comment='平台代码'))
    
    if not column_exists(conn, 'template_platform', 'rules_config_json'):
        op.add_column('template_platform', sa.Column('rules_config_json', sa.JSON(), nullable=True, comment='平台规则配置JSON'))

    if not column_exists(conn, 'template_platform', 'config_json'):
        op.add_column('template_platform', sa.Column('config_json', sa.JSON(), nullable=True, comment='平台配置JSON（预留扩展）'))

    # 添加唯一约束（如果不存在）
    if not constraint_exists(conn, 'template_platform', 'uq_template_platform_owner_name'):
        try:
            op.create_unique_constraint(
                'uq_template_platform_owner_name',
                'template_platform',
                ['owner_operator_id', 'name']
            )
        except Exception:
            pass  # 约束可能已存在但名称不同

    # ================================================================
    # 阶段3: 迁移平台数据
    # ================================================================
    
    # 只有在 category_platform 表存在且有数据时才迁移
    if table_exists(conn, 'category_platform'):
        # 3a. 迁移素材平台数据
        material_platform_id_map = {}  # old_id -> new_id
        
        if table_exists(conn, 'material_category') and column_exists(conn, 'material_category', 'platform_id'):
            material_platform_rows = conn.execute(text("""
                SELECT DISTINCT cp.*
                FROM category_platform cp
                INNER JOIN material_category mc ON cp.id = mc.platform_id
            """)).fetchall()

            for row in material_platform_rows:
                # 检查是否已存在同名平台
                existing = conn.execute(
                    text("SELECT id FROM material_platform WHERE owner_operator_id = :owner_id AND name = :name"),
                    {'owner_id': row.owner_operator_id, 'name': row.name}
                ).fetchone()

                if existing:
                    material_platform_id_map[row.id] = existing.id
                else:
                    result = conn.execute(text("""
                        INSERT INTO material_platform
                        (name, description, color, platform_code, sort_order, created_by, owner_operator_id, created_at, updated_at)
                        VALUES (:name, :description, :color, :code, :sort_order, :created_by, :owner_operator_id, :created_at, :updated_at)
                    """), {
                        'name': row.name,
                        'description': row.description,
                        'color': row.color,
                        'code': row.name.lower().replace(' ', '_').replace('/', '_')[:50] if row.name else None,
                        'sort_order': row.sort_order,
                        'created_by': row.created_by,
                        'owner_operator_id': row.owner_operator_id,
                        'created_at': row.created_at,
                        'updated_at': row.updated_at,
                    })
                    material_platform_id_map[row.id] = result.lastrowid

        # 3b. 迁移模板平台数据
        template_platform_id_map = {}  # old_id -> new_id
        
        if table_exists(conn, 'template_category') and column_exists(conn, 'template_category', 'platform_id'):
            template_platform_rows = conn.execute(text("""
                SELECT DISTINCT cp.*
                FROM category_platform cp
                INNER JOIN template_category tc ON cp.id = tc.platform_id
            """)).fetchall()

            for row in template_platform_rows:
                # 检查 template_platform 是否已存在同名平台
                existing = conn.execute(
                    text("SELECT id FROM template_platform WHERE owner_operator_id = :owner_id AND name = :name"),
                    {'owner_id': row.owner_operator_id, 'name': row.name}
                ).fetchone()

                if existing:
                    template_platform_id_map[row.id] = existing.id
                    # 更新现有记录的扩展字段
                    conn.execute(text("""
                        UPDATE template_platform 
                        SET platform_code = :code, description = :desc, color = :color
                        WHERE id = :id
                    """), {
                        'code': row.name.lower().replace(' ', '_').replace('/', '_')[:50] if row.name else None,
                        'desc': row.description,
                        'color': row.color,
                        'id': existing.id
                    })
                else:
                    result = conn.execute(text("""
                        INSERT INTO template_platform
                        (name, description, color, platform_code, sort_order, created_by, owner_operator_id, created_at, updated_at)
                        VALUES (:name, :description, :color, :code, :sort_order, :created_by, :owner_operator_id, :created_at, :updated_at)
                    """), {
                        'name': row.name,
                        'description': row.description,
                        'color': row.color,
                        'code': row.name.lower().replace(' ', '_').replace('/', '_')[:50] if row.name else None,
                        'sort_order': row.sort_order,
                        'created_by': row.created_by,
                        'owner_operator_id': row.owner_operator_id,
                        'created_at': row.created_at,
                        'updated_at': row.updated_at,
                    })
                    template_platform_id_map[row.id] = result.lastrowid

        # ================================================================
        # 阶段4: 为分类表添加新外键列并迁移数据
        # ================================================================

        # 4a. material_category: 添加 material_platform_id
        if table_exists(conn, 'material_category'):
            if not column_exists(conn, 'material_category', 'material_platform_id'):
                op.add_column('material_category', sa.Column('material_platform_id', sa.BigInteger(), nullable=True))
                if not index_exists(conn, 'material_category', 'ix_material_category_material_platform'):
                    op.create_index('ix_material_category_material_platform', 'material_category', ['material_platform_id'])

            # 迁移外键值
            for old_id, new_id in material_platform_id_map.items():
                conn.execute(
                    text("UPDATE material_category SET material_platform_id = :new_id WHERE platform_id = :old_id"),
                    {'new_id': new_id, 'old_id': old_id}
                )

        # 4b. template_category: 添加 template_platform_id
        if table_exists(conn, 'template_category'):
            if not column_exists(conn, 'template_category', 'template_platform_id'):
                op.add_column('template_category', sa.Column('template_platform_id', sa.BigInteger(), nullable=True))
                if not index_exists(conn, 'template_category', 'ix_template_category_template_platform'):
                    op.create_index('ix_template_category_template_platform', 'template_category', ['template_platform_id'])

            # 迁移外键值
            for old_id, new_id in template_platform_id_map.items():
                conn.execute(
                    text("UPDATE template_category SET template_platform_id = :new_id WHERE platform_id = :old_id"),
                    {'new_id': new_id, 'old_id': old_id}
                )

        # ================================================================
        # 阶段5: 设置新外键为非空，创建外键约束
        # ================================================================

        # material_category
        if table_exists(conn, 'material_category') and column_exists(conn, 'material_category', 'material_platform_id'):
            try:
                op.alter_column('material_category', 'material_platform_id', nullable=False)
                if not constraint_exists(conn, 'material_category', 'fk_material_category_material_platform'):
                    op.create_foreign_key(
                        'fk_material_category_material_platform',
                        'material_category', 'material_platform',
                        ['material_platform_id'], ['id'],
                        ondelete='CASCADE'
                    )
            except Exception:
                pass

        # template_category
        if table_exists(conn, 'template_category') and column_exists(conn, 'template_category', 'template_platform_id'):
            try:
                op.alter_column('template_category', 'template_platform_id', nullable=False)
                if not constraint_exists(conn, 'template_category', 'fk_template_category_template_platform'):
                    op.create_foreign_key(
                        'fk_template_category_template_platform',
                        'template_category', 'template_platform',
                        ['template_platform_id'], ['id'],
                        ondelete='CASCADE'
                    )
            except Exception:
                pass

        # ================================================================
        # 阶段6: 删除旧外键列
        # ================================================================

        # 删除旧外键约束和列
        if table_exists(conn, 'material_category') and column_exists(conn, 'material_category', 'platform_id'):
            # 删除约束
            try:
                if constraint_exists(conn, 'material_category', 'fk_material_category_platform'):
                    op.drop_constraint('fk_material_category_platform', 'material_category', type_='foreignkey')
            except Exception:
                pass
            try:
                if constraint_exists(conn, 'material_category', 'material_category_ibfk_3'):
                    op.drop_constraint('material_category_ibfk_3', 'material_category', type_='foreignkey')
            except Exception:
                pass
            
            # 删除索引和列
            try:
                if index_exists(conn, 'material_category', 'ix_material_category_platform'):
                    op.drop_index('ix_material_category_platform', table_name='material_category')
            except Exception:
                pass
            try:
                op.drop_column('material_category', 'platform_id')
            except Exception:
                pass

        if table_exists(conn, 'template_category') and column_exists(conn, 'template_category', 'platform_id'):
            # 删除约束
            try:
                if constraint_exists(conn, 'template_category', 'fk_template_category_platform'):
                    op.drop_constraint('fk_template_category_platform', 'template_category', type_='foreignkey')
            except Exception:
                pass
            try:
                if constraint_exists(conn, 'template_category', 'template_category_ibfk_3'):
                    op.drop_constraint('template_category_ibfk_3', 'template_category', type_='foreignkey')
            except Exception:
                pass
            
            # 删除索引和列
            try:
                if index_exists(conn, 'template_category', 'ix_template_category_platform'):
                    op.drop_index('ix_template_category_platform', table_name='template_category')
            except Exception:
                pass
            try:
                op.drop_column('template_category', 'platform_id')
            except Exception:
                pass

        # ================================================================
        # 阶段7: 删除旧的统一平台表
        # ================================================================
        if table_exists(conn, 'category_platform'):
            try:
                if index_exists(conn, 'category_platform', 'ix_category_platform_owner'):
                    op.drop_index('ix_category_platform_owner', table_name='category_platform')
            except Exception:
                pass
            try:
                op.drop_table('category_platform')
            except Exception:
                pass


def downgrade():
    """
    降级：独立架构 → 统一架构

    ⚠️ 警告：此操作可能导致数据丢失，建议在执行前备份数据！
    """
    conn = op.get_bind()

    # ================================================================
    # 阶段1: 重新创建 category_platform 统一平台表
    # ================================================================
    if not table_exists(conn, 'category_platform'):
        op.create_table(
            'category_platform',
            sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
            sa.Column('name', sa.String(100), nullable=False, comment='平台名称'),
            sa.Column('description', sa.String(500), nullable=True, comment='平台描述'),
            sa.Column('color', sa.String(20), nullable=True, comment='平台颜色'),
            sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0', comment='排序权重'),
            sa.Column('created_by', sa.BigInteger(), sa.ForeignKey('operator.id'), nullable=True, comment='创建者运营管理员ID'),
            sa.Column('owner_operator_id', sa.BigInteger(), sa.ForeignKey('operator.id'), nullable=False, comment='所属运营管理员ID'),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('owner_operator_id', 'name', name='uq_platform_owner_name')
        )
        op.create_index('ix_category_platform_owner', 'category_platform', ['owner_operator_id'])

    # ================================================================
    # 阶段2: 迁移数据回到统一平台表
    # ================================================================

    # 从 material_platform 迁移
    if table_exists(conn, 'material_platform'):
        material_rows = conn.execute(text("SELECT * FROM material_platform")).fetchall()
        cp_mapping = {}
        for row in material_rows:
            existing = conn.execute(
                text("SELECT id FROM category_platform WHERE owner_operator_id = :owner_id AND name = :name"),
                {'owner_id': row.owner_operator_id, 'name': row.name}
            ).fetchone()
            
            if existing:
                cp_mapping[('material', row.id)] = existing.id
            else:
                result = conn.execute(text("""
                    INSERT INTO category_platform
                    (name, description, color, sort_order, created_by, owner_operator_id, created_at, updated_at)
                    VALUES (:name, :description, :color, :sort_order, :created_by, :owner_operator_id, :created_at, :updated_at)
                """), {
                    'name': row.name, 'description': row.description, 'color': row.color,
                    'sort_order': row.sort_order, 'created_by': row.created_by,
                    'owner_operator_id': row.owner_operator_id,
                    'created_at': row.created_at, 'updated_at': row.updated_at,
                })
                cp_mapping[('material', row.id)] = result.lastrowid

        # 为 material_category 恢复旧外键列
        if table_exists(conn, 'material_category'):
            if not column_exists(conn, 'material_category', 'platform_id'):
                op.add_column('material_category', sa.Column('platform_id', sa.BigInteger(), nullable=True))
                op.create_index('ix_material_category_platform', 'material_category', ['platform_id'])

            # 更新外键值
            for (source, old_id), new_id in cp_mapping.items():
                if source == 'material':
                    conn.execute(
                        text("UPDATE material_category SET platform_id = :new_id WHERE material_platform_id = :old_id"),
                        {'new_id': new_id, 'old_id': old_id}
                    )

            # 设置非空
            try:
                op.alter_column('material_category', 'platform_id', nullable=False)
                op.create_foreign_key(
                    'fk_material_category_platform',
                    'material_category', 'category_platform',
                    ['platform_id'], ['id'], ondelete='CASCADE'
                )
            except Exception:
                pass

    # 从 template_platform 迁移
    if table_exists(conn, 'template_platform'):
        template_rows = conn.execute(text("SELECT * FROM template_platform")).fetchall()
        cp_mapping = {}
        for row in template_rows:
            existing = conn.execute(
                text("SELECT id FROM category_platform WHERE owner_operator_id = :owner_id AND name = :name"),
                {'owner_id': row.owner_operator_id, 'name': row.name}
            ).fetchone()
            if existing:
                cp_mapping[('template', row.id)] = existing.id
            else:
                result = conn.execute(text("""
                    INSERT INTO category_platform
                    (name, description, color, sort_order, created_by, owner_operator_id, created_at, updated_at)
                    VALUES (:name, :description, :color, :sort_order, :created_by, :owner_operator_id, :created_at, :updated_at)
                """), {
                    'name': row.name, 'description': row.description, 'color': row.color,
                    'sort_order': row.sort_order, 'created_by': row.created_by,
                    'owner_operator_id': row.owner_operator_id,
                    'created_at': row.created_at, 'updated_at': row.updated_at,
                })
                cp_mapping[('template', row.id)] = result.lastrowid

        # 为 template_category 恢复旧外键列
        if table_exists(conn, 'template_category'):
            if not column_exists(conn, 'template_category', 'platform_id'):
                op.add_column('template_category', sa.Column('platform_id', sa.BigInteger(), nullable=True))
                op.create_index('ix_template_category_platform', 'template_category', ['platform_id'])

            # 更新外键值
            for (source, old_id), new_id in cp_mapping.items():
                if source == 'template':
                    conn.execute(
                        text("UPDATE template_category SET platform_id = :new_id WHERE template_platform_id = :old_id"),
                        {'new_id': new_id, 'old_id': old_id}
                    )

            # 设置非空
            try:
                op.alter_column('template_category', 'platform_id', nullable=False)
                op.create_foreign_key(
                    'fk_template_category_platform',
                    'template_category', 'category_platform',
                    ['platform_id'], ['id'], ondelete='CASCADE'
                )
            except Exception:
                pass

    # ================================================================
    # 阶段3: 删除新外键列
    # ================================================================
    if table_exists(conn, 'material_category') and column_exists(conn, 'material_category', 'material_platform_id'):
        try:
            if constraint_exists(conn, 'material_category', 'fk_material_category_material_platform'):
                op.drop_constraint('fk_material_category_material_platform', 'material_category', type_='foreignkey')
        except Exception:
            pass
        try:
            if index_exists(conn, 'material_category', 'ix_material_category_material_platform'):
                op.drop_index('ix_material_category_material_platform', table_name='material_category')
        except Exception:
            pass
        try:
            op.drop_column('material_category', 'material_platform_id')
        except Exception:
            pass

    if table_exists(conn, 'template_category') and column_exists(conn, 'template_category', 'template_platform_id'):
        try:
            if constraint_exists(conn, 'template_category', 'fk_template_category_template_platform'):
                op.drop_constraint('fk_template_category_template_platform', 'template_category', type_='foreignkey')
        except Exception:
            pass
        try:
            if index_exists(conn, 'template_category', 'ix_template_category_template_platform'):
                op.drop_index('ix_template_category_template_platform', table_name='template_category')
        except Exception:
            pass
        try:
            op.drop_column('template_category', 'template_platform_id')
        except Exception:
            pass

    # ================================================================
    # 阶段4: 删除素材平台表
    # ================================================================
    if table_exists(conn, 'material_platform'):
        try:
            if index_exists(conn, 'material_platform', 'ix_material_platform_owner'):
                op.drop_index('ix_material_platform_owner', table_name='material_platform')
        except Exception:
            pass
        try:
            op.drop_table('material_platform')
        except Exception:
            pass

    # ================================================================
    # 阶段5: 清理 template_platform 扩展
    # ================================================================
    if table_exists(conn, 'template_platform'):
        if column_exists(conn, 'template_platform', 'platform_code'):
            try:
                op.drop_column('template_platform', 'platform_code')
            except Exception:
                pass
        if column_exists(conn, 'template_platform', 'rules_config_json'):
            try:
                op.drop_column('template_platform', 'rules_config_json')
            except Exception:
                pass
        if column_exists(conn, 'template_platform', 'config_json'):
            try:
                op.drop_column('template_platform', 'config_json')
            except Exception:
                pass
        if constraint_exists(conn, 'template_platform', 'uq_template_platform_owner_name'):
            try:
                op.drop_constraint('uq_template_platform_owner_name', 'template_platform', type_='unique')
            except Exception:
                pass
