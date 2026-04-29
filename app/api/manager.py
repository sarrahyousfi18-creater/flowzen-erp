from flask import Blueprint, request, jsonify, session
from app.extensions import db
from app.models.user import User
from app.models.task import Task
from app.middleware.auth import login_required, role_required
from datetime import datetime

manager_bp = Blueprint('manager', __name__)
ALLOWED_ROLES = ('Administrateur', 'Manager')

# ========== TASK MANAGEMENT APIs (UC14) ==========

@manager_bp.route('/tasks', methods=['GET'])
@login_required
def get_tasks():
    """Get all tasks with optional filters"""
    department = request.args.get('department')
    status = request.args.get('status')
    priority = request.args.get('priority')
    assignee_id = request.args.get('assignee_id')
    
    q = Task.query
    
    if department:
        q = q.filter_by(department=department)
    if status:
        q = q.filter_by(status=status)
    if priority:
        q = q.filter_by(priority=priority)
    if assignee_id:
        q = q.filter_by(assignee_id=int(assignee_id))
    
    tasks = q.order_by(Task.created_at.desc()).all()
    return jsonify([t.to_dict() for t in tasks])

@manager_bp.route('/tasks', methods=['POST'])
@role_required(*ALLOWED_ROLES)
def create_task():
    """Create a new task and assign to employee"""
    data = request.get_json()
    
    if not data.get('title'):
        return jsonify({'error': 'Task title is required'}), 400
    if not data.get('assignee_id'):
        return jsonify({'error': 'Please select an assignee'}), 400
    
    assignee = User.query.get(data['assignee_id'])
    if not assignee:
        return jsonify({'error': 'Assignee not found'}), 404
    
    task = Task(
        title=data['title'],
        description=data.get('description', ''),
        assignee_id=data['assignee_id'],
        creator_id=session.get('user_id'),
        department=assignee.department or data.get('department'),
        priority=data.get('priority', 'medium'),
        status=data.get('status', 'todo'),
        due_date=datetime.fromisoformat(data['due_date']) if data.get('due_date') else None
    )
    
    db.session.add(task)
    db.session.commit()
    
    return jsonify(task.to_dict()), 201

@manager_bp.route('/tasks/<int:task_id>', methods=['PUT'])
@role_required(*ALLOWED_ROLES)
def update_task(task_id):
    """Update an existing task"""
    task = Task.query.get_or_404(task_id)
    data = request.get_json()
    
    if 'title' in data:
        task.title = data['title']
    if 'description' in data:
        task.description = data['description']
    if 'priority' in data:
        task.priority = data['priority']
    if 'status' in data:
        task.status = data['status']
        if data['status'] == 'done':
            task.completed_at = datetime.utcnow()
    if 'department' in data:
        task.department = data['department']
    if 'assignee_id' in data:
        new_assignee = User.query.get(data['assignee_id'])
        if new_assignee:
            task.assignee_id = data['assignee_id']
            task.department = new_assignee.department
    if data.get('due_date'):
        task.due_date = datetime.fromisoformat(data['due_date'])
    
    db.session.commit()
    return jsonify(task.to_dict())

@manager_bp.route('/tasks/<int:task_id>', methods=['DELETE'])
@role_required(*ALLOWED_ROLES)
def delete_task(task_id):
    """Delete a task"""
    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    return jsonify({'success': True})

# ========== DEPARTMENT MANAGEMENT APIs (UC13) ==========

@manager_bp.route('/departments', methods=['GET'])
@login_required
def get_departments():
    """Get all departments with employee counts"""
    departments = db.session.query(
        User.department,
        db.func.count(User.id).label('employee_count')
    ).filter(
        User.department != None,
        User.department != '',
        User.is_active == True
    ).group_by(User.department).all()
    
    result = []
    for dept, count in departments:
        # Get task statistics for each department
        task_stats = db.session.query(
            Task.status,
            db.func.count(Task.id)
        ).filter_by(department=dept).group_by(Task.status).all()
        
        todo_count = sum(1 for s, c in task_stats if s in ['todo', 'in_progress'])
        done_count = sum(1 for s, c in task_stats if s == 'done')
        
        result.append({
            'name': dept,
            'employee_count': count,
            'tasks_pending': todo_count,
            'tasks_completed': done_count
        })
    
    return jsonify(result)

@manager_bp.route('/overview', methods=['GET'])
@login_required
def get_manager_overview():
    """Get overview statistics for manager dashboard"""
    total_tasks = Task.query.count()
    pending_tasks = Task.query.filter(Task.status.in_(['todo', 'in_progress'])).count()
    completed_tasks = Task.query.filter_by(status='done').count()
    overdue_tasks = Task.query.filter(
        Task.due_date < datetime.utcnow(),
        Task.status.notin_(['done', 'cancelled'])
    ).count()
    
    # Tasks by priority
    high_priority = Task.query.filter_by(priority='high').count()
    medium_priority = Task.query.filter_by(priority='medium').count()
    low_priority = Task.query.filter_by(priority='low').count()
    critical_priority = Task.query.filter_by(priority='critical').count()
    
    departments = db.session.query(
        User.department
    ).filter(
        User.department != None,
        User.is_active == True
    ).distinct().count()
    
    employees = User.query.filter_by(is_active=True).count()
    
    recent_tasks = Task.query.order_by(Task.created_at.desc()).limit(10).all()
    
    return jsonify({
        'total_tasks': total_tasks,
        'pending_tasks': pending_tasks,
        'completed_tasks': completed_tasks,
        'overdue_tasks': overdue_tasks,
        'completion_rate': round(completed_tasks / total_tasks * 100, 1) if total_tasks > 0 else 0,
        'tasks_by_priority': {
            'critical': critical_priority,
            'high': high_priority,
            'medium': medium_priority,
            'low': low_priority
        },
        'departments_count': departments,
        'employees_count': employees,
        'recent_tasks': [t.to_dict() for t in recent_tasks]
    })