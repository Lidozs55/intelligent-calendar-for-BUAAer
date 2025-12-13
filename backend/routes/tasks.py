from flask import Blueprint, request, jsonify
from extensions import db
from models.task import Task

# 创建蓝图
tasks_bp = Blueprint('tasks', __name__)


@tasks_bp.route('/', methods=['GET'])
def get_tasks():
    """获取任务列表"""
    completed = request.args.get('completed')
    
    # 构建查询
    query = Task.query
    
    # 根据completed参数过滤
    if completed is not None:
        query = query.filter_by(completed=completed.lower() == 'true')
    
    tasks = query.all()
    
    # 转换为JSON格式
    result = []
    for task in tasks:
        result.append({
            'id': task.id,
            'title': task.title,
            'description': task.description,
            'task_type': task.task_type,
            'deadline': task.deadline.isoformat() if task.deadline else None,
            'priority': task.priority,
            'completed': task.completed,
            'entry_id': task.entry_id  # 返回entry_id字段
        })
    
    return jsonify({'tasks': result}), 200


@tasks_bp.route('/', methods=['POST'])
def add_task():
    """添加任务"""
    from datetime import datetime
    
    data = request.get_json()
    
    # 验证必填字段
    if 'title' not in data:
        return jsonify({'error': '缺少必填字段: title'}), 400
    
    # 转换datetime-local格式的字符串为datetime对象
    def parse_datetime(date_str):
        if date_str:
            # 处理datetime-local格式（如YYYY-MM-DDTHH:MM）
            if len(date_str) == 16:  # 格式为 YYYY-MM-DDTHH:MM
                date_str += ':00'  # 添加秒
            # 直接将datetime-local格式解析为UTC时间，不进行时区转换
            return datetime.fromisoformat(date_str)
        return None
    
    new_task = Task(
        title=data['title'],
        description=data.get('description', ''),
        task_type=data.get('task_type', 'homework'),
        deadline=parse_datetime(data.get('deadline')),
        priority=data.get('priority', 50),
        urgency=data.get('urgency', 50.0),  # 添加紧急度字段，默认为50.0
        entry_id=data.get('entry_id')  # 添加对entry_id的支持
    )
    
    db.session.add(new_task)
    db.session.commit()
    
    # 返回完整的任务信息
    return jsonify({
        'message': '任务添加成功',
        'task': {
            'id': new_task.id,
            'title': new_task.title,
            'description': new_task.description,
            'task_type': new_task.task_type,
            'deadline': new_task.deadline.isoformat() if new_task.deadline else None,
            'priority': new_task.priority,
            'urgency': new_task.urgency,
            'completed': new_task.completed,
            'entry_id': new_task.entry_id  # 返回entry_id
        }
    }), 201


@tasks_bp.route('/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    """更新任务"""
    from datetime import datetime
    
    data = request.get_json()
    task = Task.query.get(task_id)
    
    if not task:
        return jsonify({'message': '任务不存在'}), 404
    
    # 转换datetime-local格式的字符串为datetime对象
    def parse_datetime(date_str):
        if date_str:
            # 处理datetime-local格式（如YYYY-MM-DDTHH:MM）
            if len(date_str) == 16:  # 格式为 YYYY-MM-DDTHH:MM
                date_str += ':00'  # 添加秒
            # 直接将datetime-local格式解析为UTC时间，不进行时区转换
            # 因为前端已经将UTC时间转换为本地时间显示，所以保存时需要直接存储
            return datetime.fromisoformat(date_str)
        return None
    
    # 更新任务信息
    task.title = data.get('title', task.title)
    task.description = data.get('description', task.description)
    task.task_type = data.get('task_type', task.task_type)
    task.deadline = parse_datetime(data.get('deadline')) if data.get('deadline') is not None else task.deadline
    task.priority = data.get('priority', task.priority)
    task.urgency = data.get('urgency', task.urgency)  # 更新紧急度字段
    task.completed = data.get('completed', task.completed)
    task.entry_id = data.get('entry_id', task.entry_id)  # 更新entry_id
    
    db.session.commit()
    
    # 返回完整的任务信息
    return jsonify({
        'message': '任务更新成功',
        'task': {
            'id': task.id,
            'title': task.title,
            'description': task.description,
            'task_type': task.task_type,
            'deadline': task.deadline.isoformat() if task.deadline else None,
            'priority': task.priority,
            'completed': task.completed
        }
    }), 200


@tasks_bp.route('/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    """删除任务"""
    from models.entry import Entry
    
    task = Task.query.get(task_id)
    
    if not task:
        return jsonify({'message': '任务不存在'}), 404
    
    # 如果任务关联了日程，恢复日程样式
    if task.entry_id:
        entry = Entry.query.get(task.entry_id)
        if entry:
            # 恢复默认颜色
            entry.color = "#4a90e2"  # 默认蓝色
            # 移除[任务已完成]标记
            if entry.description and "[任务已完成]" in entry.description:
                entry.description = entry.description.replace(" [任务已完成]", "").replace("[任务已完成]", "")
    
    # 删除任务
    db.session.delete(task)
    db.session.commit()
    
    return jsonify({'message': '任务删除成功'}), 200


@tasks_bp.route('/<int:task_id>/complete', methods=['PUT'])
def complete_task(task_id):
    """标记任务为完成"""
    from models.entry import Entry
    
    task = Task.query.get(task_id)
    
    if not task:
        return jsonify({'message': '任务不存在'}), 404
    
    # 标记任务为完成
    task.completed = True
    
    # 如果任务关联了日程，更新日程样式
    if task.entry_id:
        entry = Entry.query.get(task.entry_id)
        if entry:
            # 更新日程颜色，使用浅色表示已完成
            entry.color = '#e0e0e0'  # 浅灰色表示已完成
            entry.description = f"{entry.description} [任务已完成]" if entry.description else "[任务已完成]"
    
    db.session.commit()
    
    return jsonify({'message': '任务已标记为完成'}), 200


@tasks_bp.route('/<int:task_id>/uncomplete', methods=['PUT'])
def uncomplete_task(task_id):
    """标记任务为未完成"""
    from models.entry import Entry
    
    task = Task.query.get(task_id)
    
    if not task:
        return jsonify({'message': '任务不存在'}), 404
    
    # 标记任务为未完成
    task.completed = False
    
    # 如果任务关联了日程，恢复日程样式
    if task.entry_id:
        entry = Entry.query.get(task.entry_id)
        if entry:
            # 恢复默认颜色
            entry.color = "#4a90e2"  # 默认蓝色
            # 移除[任务已完成]标记
            if entry.description and "[任务已完成]" in entry.description:
                entry.description = entry.description.replace(" [任务已完成]", "").replace("[任务已完成]", "")
    
    db.session.commit()
    
    return jsonify({'message': '任务已标记为未完成'}), 200
