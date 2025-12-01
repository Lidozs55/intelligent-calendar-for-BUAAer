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
            'completed': task.completed
        })
    
    return jsonify({'tasks': result}), 200


@tasks_bp.route('/', methods=['POST'])
def add_task():
    """添加任务"""
    from datetime import datetime
    
    print("[Tasks Route] 接收到添加任务请求")
    data = request.get_json()
    
    print(f"[Tasks Route] 任务数据: {data}")
    
    # 验证必填字段
    if 'title' not in data:
        print("[Tasks Route] 缺少必填字段: title")
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
    
    print("[Tasks Route] 创建新任务对象")
    new_task = Task(
        title=data['title'],
        description=data.get('description', ''),
        task_type=data.get('task_type', 'homework'),
        deadline=parse_datetime(data.get('deadline')),
        priority=data.get('priority', 'medium')
    )
    
    print(f"[Tasks Route] 新任务对象: {new_task}")
    
    print("[Tasks Route] 添加到数据库会话")
    db.session.add(new_task)
    print("[Tasks Route] 提交到数据库")
    db.session.commit()
    print("[Tasks Route] 提交到数据库成功")
    
    # 返回完整的任务信息
    result = {
        'message': '任务添加成功',
        'task': {
            'id': new_task.id,
            'title': new_task.title,
            'description': new_task.description,
            'task_type': new_task.task_type,
            'deadline': new_task.deadline.isoformat() if new_task.deadline else None,
            'priority': new_task.priority,
            'completed': new_task.completed
        }
    }
    print(f"[Tasks Route] 返回结果: {result}")
    return jsonify(result), 201


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
    task.completed = data.get('completed', task.completed)
    
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
    task = Task.query.get(task_id)
    
    if not task:
        return jsonify({'message': '任务不存在'}), 404
    
    db.session.delete(task)
    db.session.commit()
    
    return jsonify({'message': '任务删除成功'}), 200


@tasks_bp.route('/<int:task_id>/complete', methods=['PUT'])
def complete_task(task_id):
    """标记任务为完成"""
    task = Task.query.get(task_id)
    
    if not task:
        return jsonify({'message': '任务不存在'}), 404
    
    task.completed = True
    db.session.commit()
    
    return jsonify({'message': '任务已标记为完成'}), 200


@tasks_bp.route('/<int:task_id>/uncomplete', methods=['PUT'])
def uncomplete_task(task_id):
    """标记任务为未完成"""
    task = Task.query.get(task_id)
    
    if not task:
        return jsonify({'message': '任务不存在'}), 404
    
    task.completed = False
    db.session.commit()
    
    return jsonify({'message': '任务已标记为未完成'}), 200
