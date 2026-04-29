from flask import Blueprint, request, jsonify, session
from app.extensions import db
from app.models.product import Product, StockMovement
from app.middleware.auth import login_required, role_required
from datetime import datetime

stock_bp = Blueprint('stock', __name__)
ALLOWED_ROLES = ('Administrateur', 'Stock', 'Manager')

@stock_bp.route('/products', methods=['GET'])
@login_required
def get_products():
    """Get all products"""
    category = request.args.get('category')
    status = request.args.get('status')
    search = request.args.get('q', '')
    
    q = Product.query.filter_by(is_deleted=False)
    if category:
        q = q.filter_by(category_id=category)
    if status:
        q = q.filter_by(status=status)
    if search:
        q = q.filter(Product.name.ilike(f'%{search}%') | Product.sku.ilike(f'%{search}%'))
    
    products = q.order_by(Product.name).all()
    return jsonify([p.to_dict() for p in products])

@stock_bp.route('/products', methods=['POST'])
@role_required(*ALLOWED_ROLES)
def add_product():
    """Create a new product"""
    data = request.get_json()
    
    if not data.get('name') or not data.get('selling_price'):
        return jsonify({'error': 'Name and selling price are required'}), 400
    
    sku = data.get('sku') or f"SKU-{Product.query.count() + 1:04d}"
    if Product.query.filter_by(sku=sku).first():
        return jsonify({'error': 'SKU already exists'}), 409
    
    product = Product(
        sku=sku,
        name=data['name'],
        description=data.get('description', ''),
        quantity=int(data.get('quantity', 0)),
        unit=data.get('unit', 'pcs'),
        min_stock=int(data.get('min_stock', 5)),
        max_stock=int(data.get('max_stock', 100)),
        purchase_price=float(data.get('purchase_price', 0)),
        selling_price=float(data['selling_price']),
        tax_rate=float(data.get('tax_rate', 19.0)),
        supplier=data.get('supplier', ''),
        warehouse=data.get('warehouse', 'Main'),
        status='active'
    )
    
    db.session.add(product)
    db.session.commit()
    
    # Record stock movement
    if product.quantity > 0:
        movement = StockMovement(
            product_id=product.id,
            movement_type='IN',
            quantity=product.quantity,
            previous_quantity=0,
            new_quantity=product.quantity,
            notes='Initial stock',
            performed_by=session.get('user_id')
        )
        db.session.add(movement)
        db.session.commit()
    
    return jsonify(product.to_dict()), 201

@stock_bp.route('/products/<int:product_id>', methods=['GET'])
@login_required
def get_product(product_id):
    """Get a single product"""
    product = Product.query.get_or_404(product_id)
    return jsonify(product.to_dict())

@stock_bp.route('/products/<int:product_id>', methods=['PUT'])
@role_required(*ALLOWED_ROLES)
def update_product(product_id):
    """Update a product"""
    product = Product.query.get_or_404(product_id)
    data = request.get_json()
    
    for field in ['name', 'description', 'unit', 'supplier', 'warehouse']:
        if field in data:
            setattr(product, field, data[field])
    for field in ['quantity', 'min_stock', 'max_stock']:
        if field in data:
            setattr(product, field, int(data[field]))
    for field in ['purchase_price', 'selling_price', 'tax_rate']:
        if field in data:
            setattr(product, field, float(data[field]))
    
    db.session.commit()
    return jsonify(product.to_dict())

@stock_bp.route('/products/<int:product_id>', methods=['DELETE'])
@role_required('Administrateur', 'Stock')
def delete_product(product_id):
    """Soft delete a product"""
    product = Product.query.get_or_404(product_id)
    product.is_deleted = True
    db.session.commit()
    return jsonify({'success': True})

@stock_bp.route('/products/<int:product_id>/quantity', methods=['PATCH'])
@role_required(*ALLOWED_ROLES)
def update_quantity(product_id):
    """Update product quantity"""
    product = Product.query.get_or_404(product_id)
    data = request.get_json()
    
    qty = data.get('quantity')
    if qty is None or int(qty) < 0:
        return jsonify({'error': 'Invalid quantity'}), 400
    
    old_qty = product.quantity
    product.quantity = int(qty)
    db.session.commit()
    
    return jsonify(product.to_dict())

@stock_bp.route('/products/<int:product_id>/restock', methods=['PATCH'])
@role_required(*ALLOWED_ROLES)
def restock(product_id):
    """Restock a product"""
    product = Product.query.get_or_404(product_id)
    data = request.get_json()
    
    qty = int(data.get('quantity', 0))
    if qty <= 0:
        return jsonify({'error': 'Restock quantity must be positive'}), 400
    
    product.quantity += qty
    product.last_restocked_at = datetime.utcnow()
    db.session.commit()
    return jsonify(product.to_dict())

@stock_bp.route('/products/<int:product_id>/block', methods=['PATCH'])
@role_required(*ALLOWED_ROLES)
def toggle_block(product_id):
    """Block/unblock a product"""
    product = Product.query.get_or_404(product_id)
    product.status = 'blocked' if product.status == 'active' else 'active'
    db.session.commit()
    return jsonify(product.to_dict())

@stock_bp.route('/products/low-stock', methods=['GET'])
@login_required
def low_stock():
    """Get low stock products"""
    products = Product.query.filter(
        Product.quantity <= Product.min_stock,
        Product.is_deleted == False,
        Product.status == 'active'
    ).all()
    return jsonify([p.to_dict() for p in products])

@stock_bp.route('/movements', methods=['GET'])
@login_required
def get_stock_movements():
    """Get stock movement history"""
    product_id = request.args.get('product_id', type=int)
    limit = request.args.get('limit', 50, type=int)
    
    q = StockMovement.query.order_by(StockMovement.created_at.desc())
    if product_id:
        q = q.filter_by(product_id=product_id)
    
    movements = q.limit(limit).all()
    return jsonify([{
        'id': m.id,
        'product_id': m.product_id,
        'product_name': m.product.name if m.product else None,
        'movement_type': m.movement_type,
        'quantity': m.quantity,
        'previous_quantity': m.previous_quantity,
        'new_quantity': m.new_quantity,
        'notes': m.notes,
        'created_at': m.created_at.isoformat() if m.created_at else None
    } for m in movements])