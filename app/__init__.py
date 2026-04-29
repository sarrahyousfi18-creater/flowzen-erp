from flask import Flask, render_template, session, redirect
from .config import Config
from .extensions import db, bcrypt, migrate, cors

def create_app(config_class=Config):
    app = Flask(__name__, 
                template_folder='templates',
                static_folder='../static',
                static_url_path='/static')
    
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    bcrypt.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app, supports_credentials=True)
    
    # Register blueprints
    from .api.auth import auth_bp
    from .api.admin import admin_bp
    from .api.stock import stock_bp
    from .api.sales import sales_bp
    from .api.hr import hr_bp
    from .api.manager import manager_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(stock_bp, url_prefix='/api/stock')
    app.register_blueprint(sales_bp, url_prefix='/api/sales')
    app.register_blueprint(hr_bp, url_prefix='/api/hr')
    app.register_blueprint(manager_bp, url_prefix='/api/manager')
    
    # Page routes
    @app.route('/')
    def home():
        if session.get('user_id'):
            return redirect('/dashboard')
        return render_template('login.html')
    
    @app.route('/dashboard')
    def dashboard_page():
        if not session.get('user_id'):
            return redirect('/')
        return render_template('dashboard.html', 
                               role=session.get('role'),
                               fullname=session.get('fullname'))
    
    @app.route('/admin/')
    def admin_page():
        if not session.get('user_id'):
            return redirect('/')
        return render_template('admin/admin.html',
                               role=session.get('role'),
                               fullname=session.get('fullname'))
    
    @app.route('/stock/')
    def stock_page():
        if not session.get('user_id'):
            return redirect('/')
        return render_template('stock/stock.html',
                               role=session.get('role'),
                               fullname=session.get('fullname'))
    
    @app.route('/sales/')
    def sales_page():
        if not session.get('user_id'):
            return redirect('/')
        return render_template('sales/sales.html',
                               role=session.get('role'),
                               fullname=session.get('fullname'))
    
    @app.route('/hr/')
    def hr_page():
        if not session.get('user_id'):
            return redirect('/')
        return render_template('hr/hr.html',
                               role=session.get('role'),
                               fullname=session.get('fullname'))
    
    @app.route('/manager/')
    def manager_page():
        if not session.get('user_id'):
            return redirect('/')
        return render_template('manager/manager.html',
                               role=session.get('role'),
                               fullname=session.get('fullname'))
    
    return app