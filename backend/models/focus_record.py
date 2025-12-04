from datetime import datetime
from extensions import db

class FocusRecord(db.Model):
    __tablename__ = 'focus_records'
    
    id = db.Column(db.Integer, primary_key=True)
    task_title = db.Column(db.String(100), nullable=False)
    duration = db.Column(db.Integer, nullable=False)  # 专注时长（秒）
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<FocusRecord {self.task_title} - {self.duration}s>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'task_title': self.task_title,
            'duration': self.duration,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'created_at': self.created_at.isoformat()
        }
