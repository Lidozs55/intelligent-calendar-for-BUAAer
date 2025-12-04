from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from services.schedule_manager import ScheduleManager
from models import FocusRecord, Entry
from extensions import db

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


@schedule_bp.route('/save_focus_record', methods=['POST'])
def save_focus_record():
    """
    保存专注记录
    :return: 保存结果
    """
    data = request.get_json()
    
    try:
        # 创建专注记录对象
        focus_record = FocusRecord(
            task_title=data.get('task_title'),
            duration=data.get('duration'),
            start_time=datetime.fromisoformat(data.get('start_time')),
            end_time=datetime.fromisoformat(data.get('end_time'))
        )
        
        # 保存到数据库
        db.session.add(focus_record)
        db.session.commit()
        
        # 自动清理30天前的专注记录
        clean_old_focus_records()
        
        return jsonify({'message': '专注记录保存成功', 'record': focus_record.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'保存专注记录失败: {str(e)}'}), 500


def clean_old_focus_records():
    """
    清理30天前的专注记录
    """
    try:
        # 计算30天前的日期
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        # 删除30天前的专注记录
        deleted_count = FocusRecord.query.filter(
            FocusRecord.end_time < thirty_days_ago
        ).delete()
        
        db.session.commit()
        
        print(f'已清理{deleted_count}条30天前的专注记录')
    except Exception as e:
        db.session.rollback()
        print(f'清理专注记录失败: {str(e)}')


@schedule_bp.route('/schedule_break', methods=['POST'])
def schedule_break():
    """
    安排休息
    :return: 安排结果
    """
    data = request.get_json()
    
    try:
        # 创建休息安排的条目
        rest_entry = Entry(
            title=data.get('title', '[建议]外出活动休息'),
            description='自动生成的休息安排',
            entry_type=data.get('entry_type', 'sports'),
            start_time=datetime.fromisoformat(data.get('start_time')),
            end_time=datetime.fromisoformat(data.get('end_time')),
            color='#4caf50'  # 使用绿色表示休息
        )
        
        # 保存到数据库
        db.session.add(rest_entry)
        db.session.commit()
        
        return jsonify({'message': '休息安排成功', 'entry': rest_entry.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'安排休息失败: {str(e)}'}), 500


@schedule_bp.route('/get_focus_history', methods=['GET'])
def get_focus_history():
    """
    获取最近5次专注历史记录
    :return: 最近5次专注历史记录
    """
    try:
        # 获取最近5次专注历史，按结束时间倒序排列
        recent_records = FocusRecord.query.order_by(FocusRecord.end_time.desc()).limit(5).all()
        
        # 转换为字典列表
        history_data = [record.to_dict() for record in recent_records]
        
        return jsonify({'focus_history': history_data}), 200
    except Exception as e:
        return jsonify({'message': f'获取专注历史失败: {str(e)}'}), 500
