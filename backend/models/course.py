from datetime import datetime
from extensions import db

class Course(db.Model):
    """课程模型"""
    id = db.Column(db.Integer, primary_key=True)
    course_name = db.Column(db.String(100), nullable=False)
    teacher = db.Column(db.String(50), nullable=False)
    classroom = db.Column(db.String(50), nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    day_of_week = db.Column(db.Integer, nullable=False)  # 1-7，周一到周日
    week_range = db.Column(db.String(50), nullable=False)  # 如 "1-16"
    date = db.Column(db.Date, nullable=True)  # 具体日期，用于保存未来7天的课程
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Course {self.course_name}>'
