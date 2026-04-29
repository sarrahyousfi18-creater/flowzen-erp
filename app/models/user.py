from datetime import datetime, timedelta
from flask import current_app
from app.extensions import db

class Permission(db.Model):
    __tablename__ = 'permissions'
    
    id = db.Column(db.Integer, primary_key=True)
    module = db.Column(db.String(50), nullable=False)
    can_read = db.Column(db.Boolean, default=False)
    can_write = db.Column(db.Boolean, default=False)
    can_delete = db.Column(db.Boolean, default=False)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    
    def to_dict(self):
        return {
            'module': self.module,
            'can_read': self.can_read,
            'can_write': self.can_write,
            'can_delete': self.can_delete
        }

class Role(db.Model):
    __tablename__ = 'roles'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(200))
    is_system = db.Column(db.Boolean, default=False)
    
    permissions = db.relationship('Permission', backref='role', lazy='dynamic', cascade='all, delete-orphan')
    users = db.relationship('User', backref='role_obj', lazy='dynamic')
    
    def has_permission(self, module, action):
        perm = self.permissions.filter_by(module=module).first()
        if not perm:
            return False
        if action == 'read':
            return perm.can_read
        elif action == 'write':
            return perm.can_write
        elif action == 'delete':
            return perm.can_delete
        return False
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'permissions': [p.to_dict() for p in self.permissions]
        }

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    full_name = db.Column(db.String(120), nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    
    is_active = db.Column(db.Boolean, default=True)
    is_locked = db.Column(db.Boolean, default=False)
    failed_login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime, nullable=True)
    
    department = db.Column(db.String(80))
    phone = db.Column(db.String(20))
    avatar_color = db.Column(db.String(7), default='#3B6FE8')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    
    def set_password(self, password):
        from app.extensions import bcrypt
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    def check_password(self, password):
        from app.extensions import bcrypt
        return bcrypt.check_password_hash(self.password_hash, password)
    
    def increment_failed_attempts(self):
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= current_app.config.get('MAX_LOGIN_ATTEMPTS', 5):
            self.is_locked = True
            self.locked_until = datetime.utcnow() + timedelta(minutes=current_app.config.get('LOCKOUT_DURATION', 30))
    
    def reset_failed_attempts(self):
        self.failed_login_attempts = 0
        self.is_locked = False
        self.locked_until = None
    
    def is_account_locked(self):
        if self.is_locked and self.locked_until:
            if datetime.utcnow() > self.locked_until:
                self.reset_failed_attempts()
                return False
            return True
        return False
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'role': self.role_obj.name if self.role_obj else None,
            'role_id': self.role_id,
            'department': self.department,
            'phone': self.phone,
            'is_active': self.is_active,
            'is_locked': self.is_locked,
            'avatar_color': self.avatar_color,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
        }