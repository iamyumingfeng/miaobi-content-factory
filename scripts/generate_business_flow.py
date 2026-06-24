#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["drawpyo>=0.2.0"]
# ///
"""
Generate business flow diagrams for AIGC content distribution platform
"""
import drawpyo
import sys

def create_title(page, title, x, y, width=400, height=40):
    """Create a title object"""
    obj = drawpyo.diagram.Object(page=page, value=title)
    obj.position = (x, y)
    obj.width = width
    obj.height = height
    obj.apply_style_string(
        "text;html=1;strokeColor=none;fillColor=none;"
        "align=center;verticalAlign=middle;fontSize=18;fontStyle=1;"
    )
    return obj

def create_process(page, value, x, y, width=180, height=50):
    """Create a process step"""
    obj = drawpyo.diagram.object_from_library(
        page=page,
        library="flowchart",
        obj_name="process",
        value=value
    )
    obj.position = (x, y)
    obj.width = width
    obj.height = height
    obj.apply_style_string(
        "rounded=0;whiteSpace=wrap;html=1;"
        "fillColor=#dae8fc;strokeColor=#6c8ebf;fontSize=12;"
    )
    return obj

def create_decision(page, value, x, y, width=160, height=60):
    """Create a decision shape"""
    obj = drawpyo.diagram.object_from_library(
        page=page,
        library="flowchart",
        obj_name="decision",
        value=value
    )
    obj.position = (x, y)
    obj.width = width
    obj.height = height
    obj.apply_style_string(
        "rhombus;whiteSpace=wrap;html=1;"
        "fillColor=#fff2cc;strokeColor=#d6b656;fontSize=11;"
    )
    return obj

def create_terminator(page, value, x, y, width=160, height=40):
    """Create a start/end shape"""
    obj = drawpyo.diagram.object_from_library(
        page=page,
        library="flowchart",
        obj_name="terminator",
        value=value
    )
    obj.position = (x, y)
    obj.width = width
    obj.height = height
    obj.apply_style_string(
        "rounded=1;whiteSpace=wrap;html=1;"
        "fillColor=#d5e8d4;strokeColor=#82b366;fontSize=12;"
    )
    return obj

def create_data(page, value, x, y, width=160, height=50):
    """Create a data/input/output shape"""
    obj = drawpyo.diagram.object_from_library(
        page=page,
        library="flowchart",
        obj_name="data",
        value=value
    )
    obj.position = (x, y)
    obj.width = width
    obj.height = height
    obj.apply_style_string(
        "whiteSpace=wrap;html=1;"
        "fillColor=#f5f5f5;strokeColor=#666666;fontSize=11;"
    )
    return obj

def create_document(page, value, x, y, width=160, height=50):
    """Create a document shape"""
    obj = drawpyo.diagram.object_from_library(
        page=page,
        library="general",
        obj_name="document",
        value=value
    )
    obj.position = (x, y)
    obj.width = width
    obj.height = height
    obj.apply_style_string(
        "whiteSpace=wrap;html=1;"
        "fillColor=#e1d5e7;strokeColor=#9673a6;fontSize=11;"
    )
    return obj

def create_note(page, value, x, y, width=180, height=50):
    """Create a note shape"""
    obj = drawpyo.diagram.object_from_library(
        page=page,
        library="general",
        obj_name="note",
        value=value
    )
    obj.position = (x, y)
    obj.width = width
    obj.height = height
    obj.apply_style_string(
        "whiteSpace=wrap;html=1;"
        "fillColor=#fff2cc;strokeColor=#d6b656;fontSize=10;"
    )
    return obj

def create_edge(page, source, target, label="", style=""):
    """Create an edge between two objects"""
    edge = drawpyo.diagram.Edge(
        page=page,
        source=source,
        target=target,
        label=label
    )
    if style == "dashed":
        edge.apply_style_string(
            "endArrow=block;html=1;edgeStyle=orthogonalEdgeStyle;"
            "rounded=0;orthogonalLoop=1;jettySize=auto;dashed=1;"
        )
    else:
        edge.apply_style_string(
            "endArrow=block;html=1;edgeStyle=orthogonalEdgeStyle;"
            "rounded=0;orthogonalLoop=1;jettySize=auto;"
        )
    return edge

def main():
    # Create draw.io file
    file = drawpyo.File()
    file.file_path = "/Users/yumingfeng/Workspace/AgentWork/auto_aigc_factory/docs"
    file.file_name = "business-flow.drawio"

    # Page 1: 管理员内容生成主流程
    page1 = drawpyo.Page(file=file)
    page1.name = "内容生成主流程"

    create_title(page1, "创作管理员 - 内容生成主流程", 300, 20)

    # Start
    start = create_terminator(page1, "开始", 320, 80)

    # Step 1
    step1 = create_process(page1, "步骤1: 选择复刻素材\n(从素材库选择或新建)", 290, 150, 240)
    create_edge(page1, start, step1)

    # Step 2
    step2 = create_process(page1, "步骤2: 选择模板\n(可编辑调整, 仅针对本次任务)", 290, 230, 240)
    create_edge(page1, step1, step2)

    # Step 3
    step3 = create_process(page1, "步骤3: 配置AI模型\n(自动或指定平台模型)", 290, 310, 240)
    create_edge(page1, step2, step3)

    # Step 4
    step4 = create_process(page1, "步骤4: 配置去重规则\n(敏感词/品牌名替换)", 290, 390, 240)
    create_edge(page1, step3, step4)

    # Step 5
    step5 = create_process(page1, "步骤5: 勾选目标创作者\n(支持按分类筛选)", 290, 470, 240)
    create_edge(page1, step4, step5)

    # Step 6
    step6 = create_process(page1, "步骤6: 确认并提交\n创建后台异步任务", 290, 550, 240)
    create_edge(page1, step5, step6)

    # Create generation task
    create_task = create_process(page1, "创建generation_task记录\n为每个创作者创建generation_item", 280, 630, 260)
    create_edge(page1, step6, create_task)

    # Push to queue
    push_queue = create_process(page1, "将任务推入Redis队列\n立即返回任务ID", 280, 710, 260)
    create_edge(page1, create_task, push_queue)

    # End of this flow
    end1 = create_terminator(page1, "任务已提交\n(后台开始处理)", 300, 790, 220)
    create_edge(page1, push_queue, end1)

    # Note on the right
    note1 = create_note(page1, "账户退出不影响\n任务后台执行", 600, 350, 160, 60)

    # Page 2: 异步生成引擎流程
    page2 = drawpyo.Page(file=file)
    page2.name = "异步生成引擎流程"

    create_title(page2, "Celery异步生成引擎 - 处理流程", 350, 20)

    # Start
    start2 = create_terminator(page2, "Celery Worker\n监听队列", 320, 80, 180)

    # Get task
    get_task = create_process(page2, "从Redis队列\n获取generation_item", 290, 150, 240)
    create_edge(page2, start2, get_task)

    # Check concurrency
    check_concurrent = create_decision(page2, "检查模型平台\n并发限制", 300, 230)
    create_edge(page2, get_task, check_concurrent)

    # Concurrent OK?
    yes_concurrent = create_process(page2, "调用模型适配器\n生成内容", 150, 320, 200)
    create_edge(page2, check_concurrent, yes_concurrent, "是")

    no_concurrent = create_process(page2, "任务放回队列\n延迟重试(指数退避)", 470, 320, 200)
    create_edge(page2, check_concurrent, no_concurrent, "否\n限流")
    create_edge(page2, no_concurrent, get_task, "", "dashed")

    # Call model
    call_model = create_decision(page2, "模型调用\n是否成功?", 160, 400)
    create_edge(page2, yes_concurrent, call_model)

    # Success?
    success = create_process(page2, "更新generation_item\n状态=completed", 50, 480, 180)
    create_edge(page2, call_model, success, "成功")

    fail = create_decision(page2, "重试次数\n<3次?", 320, 480)
    create_edge(page2, call_model, fail, "失败")

    retry = create_process(page2, "重试次数+1\n放回队列重试", 310, 560, 180)
    create_edge(page2, fail, retry, "是")
    create_edge(page2, retry, get_task, "", "dashed")

    mark_fail = create_process(page2, "更新状态=failed\n记录错误信息", 480, 560, 180)
    create_edge(page2, fail, mark_fail, "否")

    # Update task summary
    update_summary = create_process(page2, "更新generation_task\n汇总统计进度", 200, 650, 260)
    create_edge(page2, success, update_summary)
    create_edge(page2, mark_fail, update_summary)

    # WebSocket push
    ws_push = create_process(page2, "WebSocket推送\n进度到前端", 220, 730, 220)
    create_edge(page2, update_summary, ws_push)

    # Check all done?
    check_done = create_decision(page2, "所有任务\n完成?", 230, 810)
    create_edge(page2, ws_push, check_done)

    yes_done = create_terminator(page2, "任务完成\n发送通知", 150, 890, 160)
    create_edge(page2, check_done, yes_done, "是")

    no_done = create_process(page2, "继续处理\n下一个任务", 380, 890, 160)
    create_edge(page2, check_done, no_done, "否")
    create_edge(page2, no_done, get_task, "", "dashed")

    # Page 3: 内容分发与创作者确认流程
    page3 = drawpyo.Page(file=file)
    page3.name = "内容分发与创作者流程"

    create_title(page3, "内容分发与创作者确认流程", 350, 20)

    # Left side: Admin flow
    create_title(page3, "创作管理员", 150, 70, 200, 30)

    admin_start = create_process(page3, "查看生成任务结果", 120, 120, 260)

    select_content = create_process(page3, "勾选内容\n选择目标创作者", 120, 200, 260)
    create_edge(page3, admin_start, select_content)

    confirm_dist = create_process(page3, "确认分发\n创建distribution记录", 120, 280, 260)
    create_edge(page3, select_content, confirm_dist)

    update_status = create_process(page3, "更新状态为\n已分发/待发布", 120, 360, 260)
    create_edge(page3, confirm_dist, update_status)

    notify_subuser = create_process(page3, "通知创作者\n有新内容到达", 120, 440, 260)
    create_edge(page3, update_status, notify_subuser)

    # Right side: Sub-user flow
    create_title(page3, "创作者", 550, 70, 200, 30)

    subuser_login = create_process(page3, "小程序/Web端\n查看新内容列表", 520, 120, 260)
    create_edge(page3, notify_subuser, subuser_login, "通知")

    view_detail = create_process(page3, "查看内容详情\n标题/正文/配图", 520, 200, 260)
    create_edge(page3, subuser_login, view_detail)

    copy_download = create_process(page3, "一键复制文案\n下载图片/视频", 520, 280, 260)
    create_edge(page3, view_detail, copy_download)

    manual_publish = create_process(page3, "手动发布到\n自媒体平台", 520, 360, 260)
    create_edge(page3, copy_download, manual_publish)

    click_confirm = create_process(page3, "点击「确认已发出」", 520, 440, 260)
    create_edge(page3, manual_publish, click_confirm)

    update_published = create_process(page3, "系统更新状态\n为「已发布」", 520, 520, 260)
    create_edge(page3, click_confirm, update_published)

    end3 = create_terminator(page3, "流程完成", 550, 600)
    create_edge(page3, update_published, end3)

    # Back to admin: View status
    admin_view_status = create_process(page3, "查看各创作者\n发布状态", 120, 520, 260)
    create_edge(page3, update_published, admin_view_status, "状态同步")

    # Page 4: 用户管理流程
    page4 = drawpyo.Page(file=file)
    page4.name = "用户管理流程"

    create_title(page4, "用户管理 - 超级管理员 & 创作管理员", 350, 20)

    # Super Admin flow
    create_title(page4, "超级管理员", 150, 70, 200, 30)

    sa_start = create_process(page4, "管理创作管理员", 120, 120, 260)

    sa_create_op = create_process(page4, "创建/编辑/禁用/删除\n创作管理员", 80, 200, 180)
    sa_transfer = create_process(page4, "创作者转移\n(跨创作管理员)", 290, 200, 180)

    edge_sa1 = create_edge(page4, sa_start, sa_create_op)
    edge_sa2 = create_edge(page4, sa_start, sa_transfer)

    # Transfer sub-process
    transfer_step1 = create_process(page4, "选择要转移的创作者", 280, 280, 200)
    create_edge(page4, sa_transfer, transfer_step1)

    transfer_step2 = create_process(page4, "选择目标创作管理员", 280, 360, 200)
    create_edge(page4, transfer_step1, transfer_step2)

    transfer_step3 = create_process(page4, "确认转移\n记录transfer_log", 280, 440, 200)
    create_edge(page4, transfer_step2, transfer_step3)

    # Operator Admin flow
    create_title(page4, "创作管理员", 550, 70, 200, 30)

    op_start = create_process(page4, "管理创作者", 520, 120, 260)

    op_create_tag = create_process(page4, "创建创作者分类标签", 470, 200, 200)
    op_create_subuser = create_process(page4, "创建邀请码\n邀请创作者注册", 690, 200, 200)

    create_edge(page4, op_start, op_create_tag)
    create_edge(page4, op_start, op_create_subuser)

    op_bind_tag = create_process(page4, "创作者绑定/解绑标签", 470, 280, 200)
    create_edge(page4, op_create_tag, op_bind_tag)

    op_manage = create_process(page4, "编辑/禁用/删除创作者", 690, 280, 200)
    create_edge(page4, op_create_subuser, op_manage)

    # Sub-user registration
    create_title(page4, "创作者注册", 350, 540, 200, 30)

    sub_invite = create_data(page4, "获得邀请码\n(userid + password)", 200, 590, 220)

    sub_wechat = create_process(page4, "小程序微信授权登录", 200, 670, 220)
    create_edge(page4, sub_invite, sub_wechat)

    sub_bind = create_process(page4, "输入邀请码\n绑定账号", 200, 750, 220)
    create_edge(page4, sub_wechat, sub_bind)

    sub_done = create_terminator(page4, "注册完成", 500, 670, 140)
    create_edge(page4, sub_bind, sub_done)

    # Page 5: 系统整体业务架构
    page5 = drawpyo.Page(file=file)
    page5.name = "系统整体业务架构"

    create_title(page5, "妙笔内容工场 - 整体业务架构", 400, 20)

    # Swimlanes - Roles
    # Super Admin
    sa_box = drawpyo.diagram.Object(page=page5, value="超级管理员")
    sa_box.position = (30, 80)
    sa_box.width = 120
    sa_box.height = 50
    sa_box.apply_style_string(
        "rounded=1;whiteSpace=wrap;html=1;"
        "fillColor=#d5e8d4;strokeColor=#82b366;fontStyle=1;"
    )

    sa_func1 = create_document(page5, "全局用户管理\n(运营+创作者)", 30, 150, 120, 60)
    sa_func2 = create_document(page5, "全局数据视图\n(所有任务)", 30, 230, 120, 60)
    sa_func3 = create_document(page5, "系统设置\n(模型/并发)", 30, 310, 120, 60)

    # Operator Admin
    op_box = drawpyo.diagram.Object(page=page5, value="创作管理员")
    op_box.position = (200, 80)
    op_box.width = 140
    op_box.height = 50
    op_box.apply_style_string(
        "rounded=1;whiteSpace=wrap;html=1;"
        "fillColor=#dae8fc;strokeColor=#6c8ebf;fontStyle=1;"
    )

    op_func1 = create_document(page5, "模板管理\n(自定义平台/标签)", 200, 150, 140, 60)
    op_func2 = create_document(page5, "素材库管理", 200, 230, 140, 60)
    op_func3 = create_document(page5, "批量内容生成\n(核心功能)", 200, 310, 140, 60)
    op_func4 = create_document(page5, "内容分发", 200, 390, 140, 60)
    op_func5 = create_document(page5, "创作员管理\n(分类/转移)", 200, 470, 140, 60)

    # Sub-user
    sub_box = drawpyo.diagram.Object(page=page5, value="创作者")
    sub_box.position = (400, 80)
    sub_box.width = 120
    sub_box.height = 50
    sub_box.apply_style_string(
        "rounded=1;whiteSpace=wrap;html=1;"
        "fillColor=#fff2cc;strokeColor=#d6b656;fontStyle=1;"
    )

    sub_func1 = create_document(page5, "查看分发内容", 400, 150, 120, 60)
    sub_func2 = create_document(page5, "复制文案\n下载图片/视频", 400, 230, 120, 60)
    sub_func3 = create_document(page5, "确认发布", 400, 310, 120, 60)

    # Backend Engine
    engine_box = drawpyo.diagram.Object(page=page5, value="后端引擎")
    engine_box.position = (580, 80)
    engine_box.width = 160
    engine_box.height = 50
    engine_box.apply_style_string(
        "rounded=1;whiteSpace=wrap;html=1;"
        "fillColor=#e1d5e7;strokeColor=#9673a6;fontStyle=1;"
    )

    eng_func1 = create_document(page5, "Celery异步队列\n任务调度", 580, 150, 160, 60)
    eng_func2 = create_document(page5, "AI模型适配器\n(7+平台)", 580, 230, 160, 60)
    eng_func3 = create_document(page5, "WebSocket\n实时进度推送", 580, 310, 160, 60)
    eng_func4 = create_document(page5, "COS存储\n(图片/视频)", 580, 390, 160, 60)

    # AI Platforms
    ai_box = drawpyo.diagram.Object(page=page5, value="AI模型平台")
    ai_box.position = (800, 80)
    ai_box.width = 140
    ai_box.height = 50
    ai_box.apply_style_string(
        "rounded=1;whiteSpace=wrap;html=1;"
        "fillColor=#f8cecc;strokeColor=#b85450;fontStyle=1;"
    )

    ai_func1 = create_process(page5, "百炼\n(文本/图片)", 800, 150, 140, 45)
    ai_func2 = create_process(page5, "元宝", 800, 210, 140, 45)
    ai_func3 = create_process(page5, "月之暗面", 800, 270, 140, 45)
    ai_func4 = create_process(page5, "智谱AI", 800, 330, 140, 45)
    ai_func5 = create_process(page5, "豆包", 800, 390, 140, 45)
    ai_func6 = create_process(page5, "即梦/可灵\n(图片/视频)", 800, 450, 140, 45)

    # Connect lines
    create_edge(page5, op_func3, eng_func1)
    create_edge(page5, eng_func1, eng_func2)
    create_edge(page5, eng_func2, ai_func1)
    create_edge(page5, eng_func3, op_func3, "进度推送", "dashed")
    create_edge(page5, op_func4, sub_func1, "分发")
    create_edge(page5, sub_func3, op_func4, "状态同步", "dashed")

    # Save the file
    file.write()
    print(f"Successfully created: {file.file_path}/{file.file_name}")
    print("Pages created:")
    print("  1. 内容生成主流程")
    print("  2. 异步生成引擎流程")
    print("  3. 内容分发与创作者流程")
    print("  4. 用户管理流程")
    print("  5. 系统整体业务架构")
    return 0

if __name__ == "__main__":
    sys.exit(main())
