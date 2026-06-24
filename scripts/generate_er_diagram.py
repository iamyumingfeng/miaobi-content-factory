#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["drawpyo>=0.2.0"]
# ///
"""
Generate ER diagram for AIGC content distribution platform
"""
import drawpyo
import math
import sys

# Entity definitions from our data model
ENTITIES = [
    {
        "name": "all_user",
        "attributes": [
            {"name": "id", "type": "bigint", "pk": True},
            {"name": "userid", "type": "string"},
            {"name": "nickname", "type": "string"},
            {"name": "password_hash", "type": "string"},
            {"name": "role", "type": "enum", "description": "super_admin/operator/sub_user"},
            {"name": "wechat_openid", "type": "string"},
            {"name": "wechat_unionid", "type": "string"},
            {"name": "status", "type": "enum", "description": "online/offline/disabled"},
            {"name": "user_positioning", "type": "string"},
            {"name": "user_category", "type": "string"},
            {"name": "created_by", "type": "bigint", "fk": True},
            {"name": "managed_by", "type": "bigint", "fk": True},
            {"name": "owner_admin_id", "type": "bigint", "fk": True},
            {"name": "created_at", "type": "datetime"},
            {"name": "updated_at", "type": "datetime"}
        ]
    },
    {
        "name": "user_tag",
        "attributes": [
            {"name": "id", "type": "bigint", "pk": True},
            {"name": "name", "type": "string"},
            {"name": "tag_type", "type": "enum", "description": "operator_tag/subuser_tag"},
            {"name": "description", "type": "string"},
            {"name": "color", "type": "string"},
            {"name": "created_by", "type": "bigint", "fk": True},
            {"name": "created_at", "type": "datetime"},
            {"name": "updated_at", "type": "datetime"}
        ]
    },
    {
        "name": "user_tag_rel",
        "attributes": [
            {"name": "id", "type": "bigint", "pk": True},
            {"name": "user_id", "type": "bigint", "fk": True},
            {"name": "tag_id", "type": "bigint", "fk": True},
            {"name": "created_at", "type": "datetime"}
        ]
    },
    {
        "name": "user_transfer_log",
        "attributes": [
            {"name": "id", "type": "bigint", "pk": True},
            {"name": "user_id", "type": "bigint", "fk": True},
            {"name": "from_manager_id", "type": "bigint", "fk": True},
            {"name": "to_manager_id", "type": "bigint", "fk": True},
            {"name": "transferred_by", "type": "bigint", "fk": True},
            {"name": "transfer_reason", "type": "string"},
            {"name": "created_at", "type": "datetime"}
        ]
    },
    {
        "name": "template",
        "attributes": [
            {"name": "id", "type": "bigint", "pk": True},
            {"name": "name", "type": "string"},
            {"name": "description", "type": "string"},
            {"name": "content_type", "type": "enum", "description": "text/image_text/video_text"},
            {"name": "prompt_template", "type": "text"},
            {"name": "variables_json", "type": "json"},
            {"name": "style_reference", "type": "string"},
            {"name": "platform_rules_json", "type": "json"},
            {"name": "status", "type": "enum", "description": "enabled/disabled"},
            {"name": "platform_id", "type": "bigint", "fk": True},
            {"name": "original_template_id", "type": "bigint", "fk": True},
            {"name": "created_by", "type": "bigint", "fk": True},
            {"name": "owner_admin_id", "type": "bigint", "fk": True},
            {"name": "created_at", "type": "datetime"},
            {"name": "updated_at", "type": "datetime"}
        ]
    },
    {
        "name": "template_platform",
        "attributes": [
            {"name": "id", "type": "bigint", "pk": True},
            {"name": "name", "type": "string"},
            {"name": "description", "type": "string"},
            {"name": "color", "type": "string"},
            {"name": "sort_order", "type": "int"},
            {"name": "created_by", "type": "bigint", "fk": True},
            {"name": "owner_admin_id", "type": "bigint", "fk": True},
            {"name": "created_at", "type": "datetime"},
            {"name": "updated_at", "type": "datetime"}
        ]
    },
    {
        "name": "template_tag",
        "attributes": [
            {"name": "id", "type": "bigint", "pk": True},
            {"name": "name", "type": "string"},
            {"name": "description", "type": "string"},
            {"name": "color", "type": "string"},
            {"name": "created_by", "type": "bigint", "fk": True},
            {"name": "created_at", "type": "datetime"},
            {"name": "updated_at", "type": "datetime"}
        ]
    },
    {
        "name": "template_tag_rel",
        "attributes": [
            {"name": "id", "type": "bigint", "pk": True},
            {"name": "template_id", "type": "bigint", "fk": True},
            {"name": "tag_id", "type": "bigint", "fk": True},
            {"name": "created_at", "type": "datetime"}
        ]
    },
    {
        "name": "material",
        "attributes": [
            {"name": "id", "type": "bigint", "pk": True},
            {"name": "title", "type": "string"},
            {"name": "text_content", "type": "text"},
            {"name": "source_url", "type": "string"},
            {"name": "source_type", "type": "enum", "description": "upload/link/description"},
            {"name": "content_type", "type": "enum", "description": "text/image_text/video_text/mix"},
            {"name": "image_count", "type": "int"},
            {"name": "video_count", "type": "int"},
            {"name": "status", "type": "enum", "description": "available/disabled"},
            {"name": "created_by", "type": "bigint", "fk": True},
            {"name": "owner_admin_id", "type": "bigint", "fk": True},
            {"name": "created_at", "type": "datetime"},
            {"name": "updated_at", "type": "datetime"}
        ]
    },
    {
        "name": "material_attachment",
        "attributes": [
            {"name": "id", "type": "bigint", "pk": True},
            {"name": "material_id", "type": "bigint", "fk": True},
            {"name": "file_type", "type": "enum", "description": "image/video"},
            {"name": "file_url", "type": "string"},
            {"name": "file_name", "type": "string"},
            {"name": "file_size", "type": "bigint"},
            {"name": "sort_order", "type": "int"},
            {"name": "width", "type": "int"},
            {"name": "height", "type": "int"},
            {"name": "duration", "type": "float"},
            {"name": "thumbnail_url", "type": "string"},
            {"name": "created_at", "type": "datetime"},
            {"name": "updated_at", "type": "datetime"}
        ]
    },
    {
        "name": "material_tag",
        "attributes": [
            {"name": "id", "type": "bigint", "pk": True},
            {"name": "name", "type": "string"},
            {"name": "description", "type": "string"},
            {"name": "color", "type": "string"},
            {"name": "created_by", "type": "bigint", "fk": True},
            {"name": "owner_admin_id", "type": "bigint", "fk": True},
            {"name": "created_at", "type": "datetime"},
            {"name": "updated_at", "type": "datetime"}
        ]
    },
    {
        "name": "material_tag_rel",
        "attributes": [
            {"name": "id", "type": "bigint", "pk": True},
            {"name": "material_id", "type": "bigint", "fk": True},
            {"name": "tag_id", "type": "bigint", "fk": True},
            {"name": "created_at", "type": "datetime"}
        ]
    },
    {
        "name": "material_favorite",
        "attributes": [
            {"name": "id", "type": "bigint", "pk": True},
            {"name": "material_id", "type": "bigint", "fk": True},
            {"name": "user_id", "type": "bigint", "fk": True},
            {"name": "created_at", "type": "datetime"}
        ]
    },
    {
        "name": "generation_task",
        "attributes": [
            {"name": "id", "type": "bigint", "pk": True},
            {"name": "material_id", "type": "bigint", "fk": True},
            {"name": "model_platform", "type": "string"},
            {"name": "model_id", "type": "string"},
            {"name": "variable_values_json", "type": "json"},
            {"name": "dedup_rules_json", "type": "json"},
            {"name": "status", "type": "enum", "description": "pending/processing/completed/failed/cancelled"},
            {"name": "total_count", "type": "int"},
            {"name": "queued_count", "type": "int"},
            {"name": "generating_count", "type": "int"},
            {"name": "completed_count", "type": "int"},
            {"name": "failed_count", "type": "int"},
            {"name": "created_by", "type": "bigint", "fk": True},
            {"name": "owner_admin_id", "type": "bigint", "fk": True},
            {"name": "created_at", "type": "datetime"},
            {"name": "updated_at", "type": "datetime"}
        ]
    },
    {
        "name": "generation_task_template",
        "attributes": [
            {"name": "id", "type": "bigint", "pk": True},
            {"name": "task_id", "type": "bigint", "fk": True},
            {"name": "template_id", "type": "bigint", "fk": True},
            {"name": "sort_order", "type": "int"},
            {"name": "created_at", "type": "datetime"}
        ]
    },
    {
        "name": "generation_task_subuser",
        "attributes": [
            {"name": "id", "type": "bigint", "pk": True},
            {"name": "task_id", "type": "bigint", "fk": True},
            {"name": "sub_user_id", "type": "bigint", "fk": True},
            {"name": "created_at", "type": "datetime"}
        ]
    },
    {
        "name": "generation_task_progress_log",
        "attributes": [
            {"name": "id", "type": "bigint", "pk": True},
            {"name": "task_id", "type": "bigint", "fk": True},
            {"name": "queued_count", "type": "int"},
            {"name": "generating_count", "type": "int"},
            {"name": "completed_count", "type": "int"},
            {"name": "failed_count", "type": "int"},
            {"name": "status", "type": "enum"},
            {"name": "progress_message", "type": "string"},
            {"name": "created_at", "type": "datetime"}
        ]
    },
    {
        "name": "generation_item",
        "attributes": [
            {"name": "id", "type": "bigint", "pk": True},
            {"name": "task_id", "type": "bigint", "fk": True},
            {"name": "sub_user_id", "type": "bigint", "fk": True},
            {"name": "template_id", "type": "bigint", "fk": True},
            {"name": "model_platform", "type": "string"},
            {"name": "model_id", "type": "string"},
            {"name": "generated_title", "type": "text"},
            {"name": "generated_text", "type": "text"},
            {"name": "generated_image_urls_json", "type": "json"},
            {"name": "generated_video_url", "type": "string"},
            {"name": "status", "type": "enum", "description": "queued/generating/completed/failed"},
            {"name": "retry_count", "type": "int"},
            {"name": "error_message", "type": "text"},
            {"name": "distribution_status", "type": "enum", "description": "draft/ready/distributed"},
            {"name": "distributed_at", "type": "datetime"},
            {"name": "confirmed_at", "type": "datetime"},
            {"name": "owner_admin_id", "type": "bigint", "fk": True},
            {"name": "created_at", "type": "datetime"},
            {"name": "updated_at", "type": "datetime"}
        ]
    },
    {
        "name": "distribution",
        "attributes": [
            {"name": "id", "type": "bigint", "pk": True},
            {"name": "task_id", "type": "bigint", "fk": True},
            {"name": "generation_item_id", "type": "bigint", "fk": True},
            {"name": "sub_user_id", "type": "bigint", "fk": True},
            {"name": "publish_status", "type": "enum", "description": "distributed/pending_publish/published"},
            {"name": "distributed_at", "type": "datetime"},
            {"name": "confirmed_at", "type": "datetime"},
            {"name": "created_at", "type": "datetime"}
        ]
    },
    {
        "name": "publish_account",
        "attributes": [
            {"name": "id", "type": "bigint", "pk": True},
            {"name": "sub_user_id", "type": "bigint", "fk": True},
            {"name": "platform", "type": "string"},
            {"name": "account_name", "type": "string"},
            {"name": "account_id", "type": "string"},
            {"name": "created_at", "type": "datetime"},
            {"name": "updated_at", "type": "datetime"}
        ]
    },
    {
        "name": "notification",
        "attributes": [
            {"name": "id", "type": "bigint", "pk": True},
            {"name": "user_id", "type": "bigint", "fk": True},
            {"name": "type", "type": "enum", "description": "task_completed/task_failed/cleanup_reminder/content_received"},
            {"name": "title", "type": "string"},
            {"name": "content", "type": "text"},
            {"name": "is_read", "type": "boolean"},
            {"name": "related_id", "type": "bigint"},
            {"name": "related_type", "type": "string"},
            {"name": "created_at", "type": "datetime"}
        ]
    },
    {
        "name": "operation_log",
        "attributes": [
            {"name": "id", "type": "bigint", "pk": True},
            {"name": "user_id", "type": "bigint", "fk": True},
            {"name": "action", "type": "string"},
            {"name": "table_name", "type": "string"},
            {"name": "record_id", "type": "bigint"},
            {"name": "old_value_json", "type": "json"},
            {"name": "new_value_json", "type": "json"},
            {"name": "ip_address", "type": "string"},
            {"name": "user_agent", "type": "string"},
            {"name": "created_at", "type": "datetime"}
        ]
    },
    {
        "name": "cleanup_rule",
        "attributes": [
            {"name": "id", "type": "bigint", "pk": True},
            {"name": "rule_name", "type": "string"},
            {"name": "content_type", "type": "string"},
            {"name": "retention_period", "type": "enum", "description": "month/quarter/year"},
            {"name": "enabled", "type": "boolean"},
            {"name": "last_executed_at", "type": "datetime"},
            {"name": "created_at", "type": "datetime"},
            {"name": "updated_at", "type": "datetime"}
        ]
    },
    {
        "name": "model_config",
        "attributes": [
            {"name": "id", "type": "bigint", "pk": True},
            {"name": "platform", "type": "string"},
            {"name": "model_id", "type": "string"},
            {"name": "model_name", "type": "string"},
            {"name": "model_type", "type": "enum", "description": "llm/image/video"},
            {"name": "api_endpoint", "type": "string"},
            {"name": "is_default", "type": "boolean"},
            {"name": "max_concurrency", "type": "int"},
            {"name": "config_json", "type": "json"},
            {"name": "status", "type": "enum", "description": "active/inactive"},
            {"name": "created_at", "type": "datetime"},
            {"name": "updated_at", "type": "datetime"}
        ]
    }
]

# Relationship definitions
RELATIONSHIPS = [
    {"from": "all_user", "to": "all_user", "label": "创建/管理"},
    {"from": "all_user", "to": "user_tag", "label": "创建"},
    {"from": "user_tag", "to": "user_tag_rel", "label": "包含"},
    {"from": "all_user", "to": "user_tag_rel", "label": "属于"},
    {"from": "all_user", "to": "user_transfer_log", "label": "执行/被转移"},
    {"from": "all_user", "to": "template", "label": "创建"},
    {"from": "all_user", "to": "material", "label": "上传"},
    {"from": "all_user", "to": "generation_task", "label": "发起"},
    {"from": "all_user", "to": "notification", "label": "接收"},
    {"from": "template_platform", "to": "template", "label": "平台关联"},
    {"from": "template", "to": "template_tag_rel", "label": "标签关联"},
    {"from": "template_tag", "to": "template_tag_rel", "label": "标签关联"},
    {"from": "material", "to": "material_attachment", "label": "包含"},
    {"from": "material", "to": "material_tag_rel", "label": "标签关联"},
    {"from": "material_tag", "to": "material_tag_rel", "label": "标签关联"},
    {"from": "material", "to": "material_favorite", "label": "被收藏"},
    {"from": "all_user", "to": "material_favorite", "label": "收藏"},
    {"from": "generation_task", "to": "generation_item", "label": "包含"},
    {"from": "generation_task", "to": "generation_task_template", "label": "包含模板"},
    {"from": "generation_task", "to": "generation_task_subuser", "label": "包含创作者"},
    {"from": "generation_task", "to": "generation_task_progress_log", "label": "进度快照"},
    {"from": "material", "to": "generation_task", "label": "使用"},
    {"from": "template", "to": "generation_task_template", "label": "使用"},
    {"from": "all_user", "to": "generation_task_subuser", "label": "目标用户"},
    {"from": "template", "to": "generation_item", "label": "应用"},
    {"from": "model_config", "to": "generation_task", "label": "配置"},
    {"from": "model_config", "to": "generation_item", "label": "调用"},
    {"from": "generation_item", "to": "distribution", "label": "分发"},
    {"from": "generation_task", "to": "distribution", "label": "关联任务"},
    {"from": "all_user", "to": "distribution", "label": "接收"},
    {"from": "all_user", "to": "publish_account", "label": "拥有"},
    {"from": "all_user", "to": "operation_log", "label": "执行"},
    {"from": "all_user", "to": "cleanup_rule", "label": "配置"},
    {"from": "template_platform", "to": "template_tag", "label": "管理"},
    {"from": "all_user", "to": "template_platform", "label": "创建"},
    {"from": "all_user", "to": "template_tag", "label": "创建"},
    {"from": "all_user", "to": "material_tag", "label": "创建"},
    {"from": "model_config", "to": "model_config", "label": "默认配置"}
]

def create_entity_table(page, entity, x, y):
    """Create an ER entity table"""
    attr_count = len(entity['attributes'])
    height = 30 + attr_count * 22
    width = 200

    # Create header
    header = drawpyo.diagram.Object(page=page, value=entity['name'])
    header.position = (x, y)
    header.width = width
    header.height = 30
    header.apply_style_string(
        "rounded=0;whiteSpace=wrap;html=1;"
        "fillColor=#dae8fc;strokeColor=#6c8ebf;"
        "fontStyle=1;fontSize=14;"
    )

    # Create attributes section
    current_y = y + 30
    for attr in entity['attributes']:
        attr_obj = drawpyo.diagram.Object(page=page)
        attr_obj.position = (x, current_y)
        attr_obj.width = width
        attr_obj.height = 22

        # Format attribute name with type indicator
        attr_text = attr['name']
        if attr.get('pk'):
            attr_text = f"«PK» {attr_text}"
        elif attr.get('fk'):
            attr_text = f"«FK» {attr_text}"

        attr_obj.value = attr_text

        # Different styles for PK, FK, and regular attributes
        if attr.get('pk'):
            attr_obj.apply_style_string(
                "rounded=0;whiteSpace=wrap;html=1;"
                "fillColor=#d5e8d4;strokeColor=#82b366;"
                "fontStyle=2;fontSize=11;"
            )
        elif attr.get('fk'):
            attr_obj.apply_style_string(
                "rounded=0;whiteSpace=wrap;html=1;"
                "fillColor=#fff2cc;strokeColor=#d6b656;"
                "fontSize=11;"
            )
        else:
            attr_obj.apply_style_string(
                "rounded=0;whiteSpace=wrap;html=1;"
                "fillColor=#f5f5f5;strokeColor=#666666;"
                "fontSize=11;"
            )

        current_y += 22

    return header, (x, y, width, height)

def find_entity_bounds(entities, entity_name):
    """Find entity in entities list"""
    for e in entities:
        if e['name'] == entity_name:
            return e
    return None

def main():
    # Create draw.io file
    file = drawpyo.File()
    file.file_path = "/Users/yumingfeng/Workspace/AgentWork/auto_aigc_factory/docs"
    file.file_name = "data-model.drawio"

    page = drawpyo.Page(file=file)

    # Add title
    title = drawpyo.diagram.Object(page=page, value="妙笔内容工场 - 核心数据模型ER图")
    title.position = (400, 20)
    title.width = 400
    title.height = 40
    title.apply_style_string(
        "text;html=1;strokeColor=none;fillColor=none;"
        "align=center;verticalAlign=middle;fontSize=20;fontStyle=1;"
    )

    # Arrange entities in a grid layout
    entity_objects = {}
    entity_bounds = {}

    # Group entities by module
    modules = {
        "用户管理": ["all_user", "user_tag", "user_tag_rel", "user_transfer_log"],
        "模板管理": ["template_platform", "template", "template_tag", "template_tag_rel"],
        "素材管理": ["material", "material_attachment", "material_tag", "material_tag_rel", "material_favorite"],
        "内容生成": ["generation_task", "generation_task_template", "generation_task_subuser",
                   "generation_task_progress_log", "generation_item"],
        "内容分发": ["distribution", "publish_account"],
        "系统配置": ["notification", "operation_log", "cleanup_rule", "model_config"]
    }

    # Position entities
    col_x = [50, 300, 550, 800, 1050, 1300]
    row_y = 80

    for col_idx, (module_name, entity_names) in enumerate(modules.items()):
        current_y = row_y

        # Add module header
        module_header = drawpyo.diagram.Object(page=page, value=module_name)
        module_header.position = (col_x[col_idx], current_y)
        module_header.width = 200
        module_header.height = 25
        module_header.apply_style_string(
            "rounded=1;whiteSpace=wrap;html=1;"
            "fillColor=#6c8ebf;strokeColor=#2c5aa0;"
            "fontColor=#ffffff;fontStyle=1;fontSize=13;"
        )
        current_y += 35

        for entity_name in entity_names:
            entity = find_entity_bounds(ENTITIES, entity_name)
            if entity:
                header_obj, bounds = create_entity_table(page, entity, col_x[col_idx], current_y)
                entity_objects[entity_name] = header_obj
                entity_bounds[entity_name] = bounds
                current_y += len(entity['attributes']) * 22 + 40

    # Add relationships (edges)
    for rel in RELATIONSHIPS:
        from_obj = entity_objects.get(rel['from'])
        to_obj = entity_objects.get(rel['to'])

        if from_obj and to_obj:
            edge = drawpyo.diagram.Edge(
                page=page,
                source=from_obj,
                target=to_obj,
                label=rel['label']
            )
            edge.apply_style_string(
                "endArrow=block;html=1;edgeStyle=orthogonalEdgeStyle;"
                "rounded=0;orthogonalLoop=1;jettySize=auto;"
            )

    # Save the file
    file.write()
    print(f"Successfully created: {file.file_path}/{file.file_name}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
