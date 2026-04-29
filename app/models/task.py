from datetime import datetime
from app.extensions import db

class Task(db.Model):
    __tablename__ = 'tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default='')
    assignee_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    department = db.Column(db.String(80))
    priority = db.Column(db.String(20), default='medium')
    status = db.Column(db.String(30), default='todo')
    due_date = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @property
    def is_overdue(self):
        if self.due_date and self.status not in ['done', 'cancelled']:
            return datetime.utcnow() > self.due_date
        return False
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'assignee_id': self.assignee_id,
            'assignee_name': self.assignee.full_name if self.assignee else None,
            'creator_name': self.creator.full_name if self.creator else None,
            'department': self.department,
            'priority': self.priority,
            'status': self.status,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_overdue': self.is_overdue,
        }