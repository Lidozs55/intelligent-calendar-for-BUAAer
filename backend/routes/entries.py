from flask import Blueprint, jsonify, request
from models.entry import Entry
from models.course import Course
from datetime import datetime, timedelta, timezone
from extensions import db

entries_bp = Blueprint('entries', __name__)

@entries_bp.route('/', methods=['GET'])
def get_entries():
    """获取所有条目（包括课程、会议等）"""
    try:
        # 获取所有条目
        entries = Entry.query.all()
        return jsonify({'entries': [entry.to_dict() for entry in entries]}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@entries_bp.route('/', methods=['POST'])
def add_entry():
    """添加新条目"""
    try:
        data = request.get_json()
        
        # 验证必填字段
        required_fields = ['title', 'entry_type', 'start_time', 'end_time']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'缺少必填字段: {field}'}), 400
        
        # 创建新条目
        # 处理datetime-local格式的字符串，添加秒和时区信息
        def parse_datetime_local(date_str):
            # 如果日期字符串不包含秒，添加秒
            if len(date_str) == 16:  # 格式为 YYYY-MM-DDTHH:MM
                date_str += ':00'  # 添加秒
            # 前端发送的是本地时间，我们需要将其转换为UTC时间
            local_dt = datetime.fromisoformat(date_str)
            # 直接将本地时间作为UTC时间处理
            return local_dt.replace(tzinfo=None)
        
        new_entry = Entry(
            title=data['title'],
            description=data.get('description'),
            entry_type=data['entry_type'],
            start_time=parse_datetime_local(data['start_time']),
            end_time=parse_datetime_local(data['end_time']),
            color=data.get('color')
        )
        
        db.session.add(new_entry)
        db.session.commit()
        
        return jsonify({'entry': new_entry.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@entries_bp.route('/<int:entry_id>', methods=['PUT'])
def update_entry(entry_id):
    """更新条目"""
    try:
        entry = Entry.query.get_or_404(entry_id)
        data = request.get_json()
        
        # 处理datetime-local格式的字符串，添加秒和时区信息
        def parse_datetime_local(date_str):
            # 如果日期字符串不包含秒，添加秒
            if len(date_str) == 16:  # 格式为 YYYY-MM-DDTHH:MM
                date_str += ':00'  # 添加秒
            # 前端发送的是本地时间，我们需要将其转换为UTC时间
            # 首先解析为本地时间，然后转换为UTC时间
            local_dt = datetime.fromisoformat(date_str)
            # 直接使用replace方法将本地时间转换为UTC时间，不考虑时区差异
            # 因为前端和后端都在中国时区（UTC+8），所以直接将本地时间作为UTC时间处理
            return local_dt.replace(tzinfo=None)
        
        # 更新字段
        if 'title' in data:
            entry.title = data['title']
        if 'description' in data:
            entry.description = data['description']
        if 'entry_type' in data:
            entry.entry_type = data['entry_type']
        if 'start_time' in data:
            entry.start_time = parse_datetime_local(data['start_time'])
        if 'end_time' in data:
            entry.end_time = parse_datetime_local(data['end_time'])
        if 'color' in data:
            entry.color = data['color']
        
        db.session.commit()
        
        return jsonify({'entry': entry.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@entries_bp.route('/<int:entry_id>', methods=['DELETE'])
def delete_entry(entry_id):
    """删除条目"""
    try:
        entry = Entry.query.get_or_404(entry_id)
        db.session.delete(entry)
        db.session.commit()
        return jsonify({'message': '条目已删除'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@entries_bp.route('/courses', methods=['GET'])
def get_course_entries():
    """获取课程类型的条目"""
    try:
        # 获取未来14天的课程
        today = datetime.utcnow().date()
        entries = Entry.query.filter(
            Entry.entry_type == 'course',
            Entry.start_time >= datetime.combine(today, datetime.min.time()),
            Entry.start_time <= datetime.combine(today + timedelta(days=14), datetime.max.time())
        ).all()
        return jsonify({'entries': [entry.to_dict() for entry in entries]}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@entries_bp.route('/<string:date>', methods=['GET'])
def get_entries_by_date_range(date):
    """获取指定日期及之后7天内的所有条目
    
    Args:
        date: 格式为 yyyy-mm-dd 的日期字符串
        
    Returns:
        JSON格式的条目列表，包含指定日期及之后7天内的所有条目
    """
    try:
        # 解析日期参数
        try:
            start_date = datetime.strptime(date, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': '日期格式错误，应为 yyyy-mm-dd'}), 400
        
        # 计算结束日期（开始日期 + 6天，共7天）
        end_date = start_date + timedelta(days=6)
        
        # 构建查询条件
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())
        
        # 查询指定日期范围内的所有条目
        entries = Entry.query.filter(
            Entry.start_time >= start_datetime,
            Entry.start_time <= end_datetime
        ).all()
        
        result = {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'entries': [entry.to_dict() for entry in entries]
        }
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


