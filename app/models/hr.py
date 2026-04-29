from datetime import datetime, date
from app.extensions import db

class Attendance(db.Model):
    __tablename__ = 'attendance'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.Date, default=date.today, nullable=False)
    check_in = db.Column(db.DateTime, nullable=True)
    check_out = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default='present')
    overtime_hours = db.Column(db.Float, default=0.0)
    notes = db.Column(db.String(200), default='')
    
    __table_args__ = (db.UniqueConstraint('employee_id', 'date', name='uix_attendance'),)
    
    @property
    def hours_worked(self):
        if self.check_in and self.check_out:
            delta = self.check_out - self.check_in
            return round(delta.total_seconds() / 3600, 2)
        return 0.0
    
    def to_dict(self):
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'employee_name': self.employee.full_name if self.employee else None,
            'date': self.date.isoformat() if self.date else None,
            'check_in': self.check_in.isoformat() if self.check_in else None,
            'check_out': self.check_out.isoformat() if self.check_out else None,
            'hours_worked': self.hours_worked,
            'status': self.status,
            'notes': self.notes,
        }

class Recruitment(db.Model):
    __tablename__ = 'recruitments'
    
    id = db.Column(db.Integer, primary_key=True)
    position = db.Column(db.String(120), nullable=False)
    department = db.Column(db.String(80), nullable=False)
    number_of_openings = db.Column(db.Integer, default=1)
    status = db.Column(db.String(30), default='open')
    priority = db.Column(db.String(20), default='medium')
    description = db.Column(db.Text)
    target_date = db.Column(db.Date, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'position': self.position,
            'department': self.department,
            'number_of_openings': self.number_of_openings,
            'status': self.status,
            'priority': self.priority,
            'description': self.description,
            'target_date': self.target_date.isoformat() if self.target_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

class HRMetric(db.Model):
    __tablename__ = 'hr_metrics'
    
    id = db.Column(db.Integer, primary_key=True)
    period_start = db.Column(db.Date, nullable=False)
    period_end = db.Column(db.Date, nullable=False)
    
    total_employees = db.Column(db.Integer, default=0)
    new_hires = db.Column(db.Integer, default=0)
    departures = db.Column(db.Integer, default=0)
    turnover_rate = db.Column(db.Float, default=0.0)
    absenteeism_rate = db.Column(db.Float, default=0.0)
    avg_time_to_hire_days = db.Column(db.Float, default=0.0)
    attendance_rate = db.Column(db.Float, default=0.0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'period_start': self.period_start.isoformat(),
            'period_end': self.period_end.isoformat(),
            'total_employees': self.total_employees,
            'new_hires': self.new_hires,
            'departures': self.departures,
            'turnover_rate': self.turnover_rate,
            'absenteeism_rate': self.absenteeism_rate,
            'avg_time_to_hire_days': self.avg_time_to_hire_days,
            'attendance_rate': self.attendance_rate,
        }