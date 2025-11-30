from datetime import datetime
from extensions import db

class User(db.Model):
    """用户模型"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=True)  # 密码哈希字段设为可选
    buaa_id = db.Column(db.String(20), unique=True, nullable=True)
    buaa_cookies = db.Column(db.Text, nullable=True)  # 存储北航系统Cookie
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    # tasks = db.relationship('Task', backref='user', lazy=True)
    
    def __repr__(self):
        return f'<User {self.username}>'
