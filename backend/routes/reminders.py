from flask import Blueprint, request, jsonify
from services.reminder import reminder_service
from models.task import Task
from extensions import db
from datetime import datetime

reminders_bp = Blueprint('reminders', __name__)

def clean_expired_tasks():
    """清理已过期的任务"""
    try:
        now = datetime.now()
        
        # 删除所有已过期的任务
        expired_tasks = Task.query.filter(Task.deadline < now).all()
        
        if expired_tasks:
            # 记录删除的任务数量
            deleted_count = len(expired_tasks)
            
            # 删除任务
            for task in expired_tasks:
                db.session.delete(task)
            
            db.session.commit()
            
            return {
                'success': True,
                'deleted_count': deleted_count
            }
        
        return {
            'success': True,
            'deleted_count': 0
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

@reminders_bp.route('/upcoming', methods=['GET', 'POST'])
def get_upcoming_reminders():
    """
    获取即将到来的提醒
    
    Request Body (可选):
        settings: 用户设置的提醒参数，包含不同事件类型的阈值时间
        
    Returns:
        json: 包含即将到来事件的列表
    """
    try:
        # 清理过期任务
        clean_expired_tasks()
        
        # 获取用户设置
        settings = None
        if request.method == 'POST':
            settings = request.json.get('settings', {})
        elif request.method == 'GET':
            # 从查询参数中获取简单设置（兼容旧版）
            settings = {}
            for key in ['course', 'homework', 'lecture', 'meeting']:
                if key in request.args:
                    settings[key] = int(request.args[key])
            
            # 处理考试的多级提醒
            if 'exam' in request.args:
                settings['exam'] = list(map(int, request.args.getlist('exam')))
        
        # 获取即将到来的事件
        reminders = reminder_service.get_upcoming_events(settings=settings)
        
        # 转换为JSON可序列化的格式
        serialized_reminders = []
        for reminder in reminders:
            serialized_reminders.append({
                'id': reminder['id'],
                'title': reminder['title'],
                'event_type': reminder['event_type'],
                'start_time': reminder['start_time'].isoformat(),
                'end_time': reminder['end_time'].isoformat(),
                'time_diff': reminder['time_diff'],
                'urgency': reminder['urgency'],
                'description': reminder['description'],
                'color': reminder['color']
            })
        
        return jsonify({
            'success': True,
            'reminders': serialized_reminders,
            'count': len(serialized_reminders)
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
