from flask import Blueprint, request, jsonify, session
from app.extensions import db
from app.models.user import User, Role, Permission
from app.middleware.auth import login_required, role_required
import random

admin_bp = Blueprint('admin', __name__)

AVATAR_COLORS = ['#3B6FE8', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899', '#14B8A6']

# ========== CRUD USERS ==========

@admin_bp.route('/users', methods=['GET'])
@login_required
@role_required('Administrateur')
def get_users():
    """Get all users with pagination and filters"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search = request.args.get('search', '')
    role_id = request.args.get('role_id', type=int)
    
    query = User.query.filter_by(is_active=True)
    
    if search:
        query = query.filter(
            User.username.ilike(f'%{search}%') |
            User.email.ilike(f'%{search}%') |
            User.full_name.ilike(f'%{search}%')
        )
    
    if role_id:
        query = query.filter_by(role_id=role_id)
    
    paginated = query.order_by(User.created_at.desc()).paginate(page=page, per_page=per_page)
    
    return jsonify({
        'users': [u.to_dict() for u in paginated.items],
        'total': paginated.total,
        'page': page,
        'per_page': per_page,
        'pages': paginated.pages
    })

@admin_bp.route('/users', methods=['POST'])
@login_required
@role_required('Administrateur')
def create_user():
    """Create a new user"""
    data = request.get_json()
    
    required = ['username', 'email', 'password', 'full_name', 'role_id']
    for field in required:
        if not data.get(field):
            return jsonify({'error': f'Field "{field}" is required'}), 400
    
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already exists'}), 409
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already exists'}), 409
    
    role = Role.query.get(data['role_id'])
    if not role:
        return jsonify({'error': 'Invalid role'}), 400
    
    user = User(
        username=data['username'],
        email=data['email'],
        full_name=data['full_name'],
        role_id=data['role_id'],
        department=data.get('department', ''),
        phone=data.get('phone', ''),
        avatar_color=random.choice(AVATAR_COLORS),
        is_active=data.get('is_active', True)
    )
    user.set_password(data['password'])
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify(user.to_dict()), 201

@admin_bp.route('/users/<int:user_id>', methods=['GET'])
@login_required
@role_required('Administrateur')
def get_user(user_id):
    """Get a single user by ID"""
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict())

@admin_bp.route('/users/<int:user_id>', methods=['PUT'])
@login_required
@role_required('Administrateur')
def update_user(user_id):
    """Update user information"""
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    
    if data.get('is_active') is False and user.id == session.get('user_id'):
        return jsonify({'error': 'Cannot deactivate your own account'}), 400
    
    updatable_fields = ['full_name', 'email', 'department', 'phone', 'is_active']
    for field in updatable_fields:
        if field in data:
            setattr(user, field, data[field])
    
    if 'role_id' in data:
        role = Role.query.get(data['role_id'])
        if not role:
            return jsonify({'error': 'Invalid role'}), 400
        user.role_id = data['role_id']
    
    if data.get('password'):
        user.set_password(data['password'])
    
    db.session.commit()
    return jsonify(user.to_dict())

@admin_bp.route('/users/<int:user_id>/lock', methods=['PATCH'])
@login_required
@role_required('Administrateur')
def toggle_lock(user_id):
    """Lock or unlock a user account"""
    user = User.query.get_or_404(user_id)
    
    if user.id == session.get('user_id'):
        return jsonify({'error': 'Cannot lock your own account'}), 400
    
    user.is_locked = not user.is_locked
    if not user.is_locked:
        user.reset_failed_attempts()
    
    db.session.commit()
    return jsonify({'is_locked': user.is_locked})

@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@login_required
@role_required('Administrateur')
def delete_user(user_id):
    """Soft delete (deactivate) a user"""
    user = User.query.get_or_404(user_id)
    
    if user.id == session.get('user_id'):
        return jsonify({'error': 'Cannot delete your own account'}), 400
    
    user.is_active = False
    db.session.commit()
    return jsonify({'success': True, 'message': 'User deactivated'})

@admin_bp.route('/roles', methods=['GET'])
@login_required
@role_required('Administrateur')
def get_roles():
    """Get all roles"""
    roles = Role.query.all()
    return jsonify([{'id': r.id, 'name': r.name, 'description': r.description} for r in roles])