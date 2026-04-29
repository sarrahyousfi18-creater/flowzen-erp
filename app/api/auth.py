from flask import Blueprint, request, jsonify, session, g
from app.extensions import db
from app.models.user import User
from app.middleware.auth import generate_tokens, login_required
from datetime import datetime

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    
    username = data.get('username', '').strip()
    password = data.get('password', '')
    role_name = data.get('role', '')
    
    if not username or not password or not role_name:
        return jsonify({'error': 'All fields are required'}), 400
    
    user = User.query.filter_by(username=username).first()
    
    if not user:
        return jsonify({'error': 'Invalid credentials'}), 401
    
    # Check if account is locked
    if user.is_account_locked():
        return jsonify({'error': 'Account locked. Too many failed attempts.'}), 403
    
    # Check if active
    if not user.is_active:
        return jsonify({'error': 'Account deactivated'}), 403
    
    # Check role
    if user.role_obj.name != role_name:
        user.increment_failed_attempts()
        db.session.commit()
        return jsonify({'error': 'Invalid role for this account'}), 401
    
    # Check password
    if not user.check_password(password):
        user.increment_failed_attempts()
        db.session.commit()
        return jsonify({'error': 'Wrong password'}), 401
    
    # Success - reset failed attempts
    user.reset_failed_attempts()
    user.last_login = datetime.utcnow()
    db.session.commit()
    
    # Set session
    session['user_id'] = user.id
    session['username'] = user.username
    session['role'] = user.role_obj.name
    session['fullname'] = user.full_name
    
    # Generate tokens
    access_token, refresh_token = generate_tokens(user)
    
    # Redirect based on role
    redirect_map = {
        'Administrateur': '/admin/',
        'Stock': '/stock/',
        'Commercial': '/sales/',
        'RH': '/hr/',
        'Manager': '/manager/'
    }
    
    return jsonify({
        'success': True,
        'role': user.role_obj.name,
        'redirect': redirect_map.get(user.role_obj.name, '/dashboard'),
        'access_token': access_token,
        'user': user.to_dict()
    })

@auth_bp.route('/api/auth/logout', methods=['POST'])
@login_required
def logout():
    session.clear()
    return jsonify({'success': True})

@auth_bp.route('/api/auth/me', methods=['GET'])
@login_required
def me():
    return jsonify(g.current_user.to_dict())