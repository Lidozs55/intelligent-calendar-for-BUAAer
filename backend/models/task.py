from datetime import datetime
from extensions import db

class Task(db.Model):
    """任务模型 - 仅表示截止日期（events）"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    task_type = db.Column(db.String(20), nullable=False)  # 如 "homework", "exam", "lecture"
    deadline = db.Column(db.DateTime, nullable=False)  # 截止时间（必须字段）
    priority = db.Column(db.String(10), nullable=False, default="medium")  # low, medium, high, urgent
    completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Task {self.title}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'task_type': self.task_type,
            'deadline': self.deadline.isoformat(),  # 不添加UTC时区标记，直接存储本地时间
            'priority': self.priority,
            'completed': self.completed,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
