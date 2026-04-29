from flask import Blueprint, request, jsonify, session
from app.extensions import db
from app.models.user import User
from app.models.hr import Attendance, Recruitment, HRMetric
from app.middleware.auth import login_required, role_required
from datetime import datetime, date, timedelta

hr_bp = Blueprint('hr', __name__)
ALLOWED_ROLES = ('Administrateur', 'RH', 'Manager')

# ========== ATTENDANCE APIs ==========

@hr_bp.route('/attendance', methods=['GET'])
@role_required(*ALLOWED_ROLES)
def get_attendance():
    """Get attendance records"""
    from_date = request.args.get('from')
    to_date = request.args.get('to')
    emp_id = request.args.get('employee_id')
    
    q = Attendance.query
    if from_date:
        q = q.filter(Attendance.date >= date.fromisoformat(from_date))
    if to_date:
        q = q.filter(Attendance.date <= date.fromisoformat(to_date))
    if emp_id:
        q = q.filter_by(employee_id=int(emp_id))
    
    records = q.order_by(Attendance.date.desc()).all()
    return jsonify([r.to_dict() for r in records])

@hr_bp.route('/attendance', methods=['POST'])
@role_required(*ALLOWED_ROLES)
def log_attendance():
    """Record attendance for an employee"""
    data = request.get_json()
    
    emp_id = int(data.get('employee_id'))
    att_date = date.fromisoformat(data.get('date', date.today().isoformat()))
    
    existing = Attendance.query.filter_by(employee_id=emp_id, date=att_date).first()
    if existing:
        return jsonify({'error': 'Attendance already logged for this date'}), 409
    
    check_in = datetime.fromisoformat(data['check_in']) if data.get('check_in') else None
    check_out = datetime.fromisoformat(data['check_out']) if data.get('check_out') else None
    
    att = Attendance(
        employee_id=emp_id,
        date=att_date,
        check_in=check_in,
        check_out=check_out,
        status=data.get('status', 'present'),
        notes=data.get('notes', '')
    )
    
    db.session.add(att)
    db.session.commit()
    return jsonify(att.to_dict()), 201

# ========== EMPLOYEE APIs ==========

@hr_bp.route('/employees', methods=['GET'])
@role_required(*ALLOWED_ROLES)
def get_employees():
    """Get all employees"""
    employees = User.query.filter(User.is_active == True).all()
    
    return jsonify([{
        'id': e.id,
        'full_name': e.full_name,
        'department': e.department,
        'email': e.email,
        'role': e.role_obj.name if e.role_obj else None,
        'avatar_color': e.avatar_color
    } for e in employees])

# ========== METRICS APIs (UC12) ==========

@hr_bp.route('/metrics', methods=['GET'])
@role_required(*ALLOWED_ROLES)
def hr_metrics():
    """Get HR metrics dashboard data (UC12 - Auto Calculate HR Metrics)"""
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)
    
    # This week attendance
    week_records = Attendance.query.filter(Attendance.date >= week_start).all()
    present = sum(1 for r in week_records if r.status == 'present')
    absent = sum(1 for r in week_records if r.status == 'absent')
    late = sum(1 for r in week_records if r.status == 'late')
    remote = sum(1 for r in week_records if r.status == 'remote')
    total = len(week_records)
    
    # Average hours this week
    hours_list = []
    for r in week_records:
        if r.check_in and r.check_out:
            hours_list.append((r.check_out - r.check_in).total_seconds() / 3600)
    avg_hours = round(sum(hours_list) / len(hours_list), 1) if hours_list else 0
    
    # Total employees
    total_emp = User.query.filter_by(is_active=True).count()
    
    # Open recruitments
    open_recruitments = Recruitment.query.filter_by(status='open').count()
    
    # Calculate turnover rate (UC12)
    # For demo: use last 30 days
    thirty_days_ago = today - timedelta(days=30)
    new_hires = 0  # Would be calculated from recruitment data
    departures = 0  # Would be calculated from user deactivations
    turnover_rate = 0
    if total_emp > 0:
        turnover_rate = round(((departures + new_hires) / total_emp) * 100, 1)
    
    # Calculate average time to hire (UC12)
    avg_time_to_hire = 0  # Would be calculated from recruitment data
    
    return jsonify({
        'total_employees': total_emp,
        'present_week': present,
        'absent_week': absent,
        'late_week': late,
        'remote_week': remote,
        'total_records': total,
        'attendance_rate': round(present / total * 100, 1) if total > 0 else 0,
        'avg_hours': avg_hours,
        'open_recruitments': open_recruitments,
        'turnover_rate': turnover_rate,
        'new_hires': new_hires,
        'departures': departures,
        'avg_time_to_hire_days': avg_time_to_hire
    })

# ========== RECRUITMENT APIs (UC10) ==========

@hr_bp.route('/recruitments', methods=['GET'])
@role_required(*ALLOWED_ROLES)
def get_recruitments():
    """Get all recruitments"""
    recs = Recruitment.query.order_by(Recruitment.created_at.desc()).all()
    return jsonify([r.to_dict() for r in recs])

@hr_bp.route('/recruitments', methods=['POST'])
@role_required(*ALLOWED_ROLES)
def create_recruitment():
    """Create a new recruitment"""
    data = request.get_json()
    
    if not data.get('position') or not data.get('department'):
        return jsonify({'error': 'Position and department are required'}), 400
    
    rec = Recruitment(
        position=data['position'],
        department=data['department'],
        number_of_openings=data.get('number_of_openings', 1),
        status=data.get('status', 'open'),
        priority=data.get('priority', 'medium'),
        description=data.get('description', ''),
        target_date=date.fromisoformat(data['target_date']) if data.get('target_date') else None,
        created_by=session.get('user_id')
    )
    
    db.session.add(rec)
    db.session.commit()
    return jsonify(rec.to_dict()), 201

@hr_bp.route('/recruitments/<int:rec_id>', methods=['PUT'])
@role_required(*ALLOWED_ROLES)
def update_recruitment(rec_id):
    """Update recruitment"""
    rec = Recruitment.query.get_or_404(rec_id)
    data = request.get_json()
    
    for field in ['position', 'department', 'status', 'priority', 'description']:
        if field in data:
            setattr(rec, field, data[field])
    if 'number_of_openings' in data:
        rec.number_of_openings = data['number_of_openings']
    if data.get('target_date'):
        rec.target_date = date.fromisoformat(data['target_date'])
    
    db.session.commit()
    return jsonify(rec.to_dict())

@hr_bp.route('/recruitments/<int:rec_id>', methods=['DELETE'])
@role_required(*ALLOWED_ROLES)
def delete_recruitment(rec_id):
    """Delete recruitment"""
    rec = Recruitment.query.get_or_404(rec_id)
    db.session.delete(rec)
    db.session.commit()
    return jsonify({'success': True})