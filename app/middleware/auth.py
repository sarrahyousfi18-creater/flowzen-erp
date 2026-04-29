from functools import wraps
from flask import request, jsonify, g, current_app, session
import jwt
from datetime import datetime, timedelta

def generate_tokens(user):
    """Generate access and refresh tokens for a user"""
    access_token = jwt.encode({
        'user_id': user.id,
        'username': user.username,
        'role': user.role_obj.name if user.role_obj else None,
        'exp': datetime.utcnow() + timedelta(hours=8)
    }, current_app.config['JWT_SECRET'], algorithm='HS256')
    
    refresh_token = jwt.encode({
        'user_id': user.id,
        'type': 'refresh',
        'exp': datetime.utcnow() + timedelta(days=7)
    }, current_app.config['JWT_SECRET'], algorithm='HS256')
    
    return access_token, refresh_token

def decode_token(token):
    """Decode and validate JWT token"""
    try:
        payload = jwt.decode(token, current_app.config['JWT_SECRET'], algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # Check session first
        if session.get('user_id'):
            from app.models.user import User
            user = User.query.get(session['user_id'])
            if user and user.is_active:
                g.current_user = user
                return f(*args, **kwargs)
        
        # Then check Authorization header
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return jsonify({'error': 'Authentication required'}), 401
        
        payload = decode_token(token)
        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        from app.models.user import User
        user = User.query.get(payload['user_id'])
        if not user or not user.is_active:
            return jsonify({'error': 'User not found or inactive'}), 401
        
        g.current_user = user
        return f(*args, **kwargs)
    
    return decorated

def role_required(*allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not hasattr(g, 'current_user'):
                # Try to get from session
                if session.get('user_id'):
                    from app.models.user import User
                    user = User.query.get(session['user_id'])
                    if user and user.is_active:
                        g.current_user = user
                    else:
                        return jsonify({'error': 'Authentication required'}), 401
                else:
                    return jsonify({'error': 'Authentication required'}), 401
            
            user_role = g.current_user.role_obj.name if g.current_user.role_obj else None
            if user_role not in allowed_roles:
                return jsonify({'error': f'Forbidden. Required role: {", ".join(allowed_roles)}'}), 403
            
            return f(*args, **kwargs)
        return decorated
    return decorator