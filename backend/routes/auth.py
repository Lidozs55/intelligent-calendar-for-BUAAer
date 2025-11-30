from flask import Blueprint, request, jsonify
from extensions import db
from models.user import User

# 创建蓝图
auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/buaa_id', methods=['POST'])
def set_buaa_id():
    """设置北航学号"""
    data = request.get_json()
    buaa_id = data.get('buaa_id')
    
    # 对于独立程序，我们假设只有一个用户，或者创建一个默认用户
    # 查找现有用户，如果没有则创建一个
    user = User.query.first()
    
    if user:
        # 更新现有用户的北航学号
        user.buaa_id = buaa_id
        db.session.commit()
        return jsonify({'message': '北航学号更新成功'}), 200
    else:
        # 创建新用户
        new_user = User(
            username='default_user',  # 默认用户名
            buaa_id=buaa_id
        )
        db.session.add(new_user)
        db.session.commit()
        return jsonify({'message': '北航学号设置成功'}), 201


@auth_bp.route('/buaa_id', methods=['GET'])
def get_buaa_id():
    """获取北航学号"""
    # 对于独立程序，我们假设只有一个用户
    user = User.query.first()
    
    if user:
        return jsonify({
            'buaa_id': user.buaa_id
        }), 200
    else:
        return jsonify({
            'buaa_id': None
        }), 200
