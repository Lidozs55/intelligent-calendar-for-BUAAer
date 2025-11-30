from flask import Blueprint, request, jsonify
from services.schedule_manager import ScheduleManager

# 创建蓝图
schedule_bp = Blueprint('schedule', __name__)

# 初始化日程管理器
schedule_manager = ScheduleManager()


@schedule_bp.route('/check_conflict', methods=['POST'])
def check_conflict():
    """
    检查日程冲突
    :return: 冲突的事件列表
    """
    data = request.get_json()
    user_id = data.get('user_id')
    new_event = data.get('event')
    
    if not user_id or not new_event:
        return jsonify({'message': '缺少必要参数'}), 400
    
    try:
        conflicts = schedule_manager.check_conflict(user_id, new_event)
        return jsonify({'conflicts': conflicts}), 200
    except Exception as e:
        return jsonify({'message': f'检查冲突失败: {str(e)}'}), 500


@schedule_bp.route('/auto_schedule', methods=['POST'])
def auto_schedule():
    """
    自动安排任务时间
    :return: 推荐的开始时间和结束时间
    """
    data = request.get_json()
    user_id = data.get('user_id')
    task_id = data.get('task_id')
    
    if not user_id or not task_id:
        return jsonify({'message': '缺少必要参数'}), 400
    
    try:
        recommended_time = schedule_manager.auto_schedule(user_id, task_id)
        if recommended_time:
            return jsonify({'recommended_time': recommended_time}), 200
        else:
            return jsonify({'message': '没有找到合适的时间段'}), 404
    except Exception as e:
        return jsonify({'message': f'自动安排失败: {str(e)}'}), 500


@schedule_bp.route('/find_available_slots', methods=['POST'])
def find_available_slots():
    """
    查找可用时间段
    :return: 可用的时间段列表
    """
    data = request.get_json()
    user_id = data.get('user_id')
    deadline = data.get('deadline')
    estimated_time = data.get('estimated_time')
    
    if not user_id or not deadline or not estimated_time:
        return jsonify({'message': '缺少必要参数'}), 400
    
    try:
        # 这里可以根据实际需求实现
        return jsonify({'available_slots': []}), 200
    except Exception as e:
        return jsonify({'message': f'查找可用时间段失败: {str(e)}'}), 500
