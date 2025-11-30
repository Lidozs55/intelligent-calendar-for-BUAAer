from datetime import datetime
from extensions import db

class Entry(db.Model):
    __tablename__ = 'entries'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    entry_type = db.Column(db.String(20), nullable=False)  # course, meeting, study, sports, etc.
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    color = db.Column(db.String(20), nullable=True, default="#4a90e2")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Entry {self.title} ({self.entry_type})>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'entry_type': self.entry_type,
            'start_time': self.start_time.isoformat(),  # 不添加UTC时区标记，前端直接作为本地时间处理
            'end_time': self.end_time.isoformat(),  # 不添加UTC时区标记，前端直接作为本地时间处理
            'color': self.color,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
