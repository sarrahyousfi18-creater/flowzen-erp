from datetime import datetime
from app.extensions import db

class ProductCategory(db.Model):
    __tablename__ = 'product_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('product_categories.id'))
    description = db.Column(db.String(200))
    
    children = db.relationship('ProductCategory', backref=db.backref('parent', remote_side=[id]))

class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(50), unique=True, nullable=False, index=True)
    barcode = db.Column(db.String(50), unique=True)
    name = db.Column(db.String(120), nullable=False, index=True)
    description = db.Column(db.Text, default='')
    
    category_id = db.Column(db.Integer, db.ForeignKey('product_categories.id'))
    category = db.relationship('ProductCategory', backref='products')
    
    quantity = db.Column(db.Integer, default=0)
    reserved_quantity = db.Column(db.Integer, default=0)
    unit = db.Column(db.String(20), default='pcs')
    min_stock = db.Column(db.Integer, default=5)
    max_stock = db.Column(db.Integer, default=100)
    reorder_point = db.Column(db.Integer, default=10)
    
    purchase_price = db.Column(db.Float, default=0.0)
    selling_price = db.Column(db.Float, nullable=False)
    tax_rate = db.Column(db.Float, default=19.0)
    
    supplier = db.Column(db.String(120))
    warehouse = db.Column(db.String(80), default='Main')
    shelf_location = db.Column(db.String(50))
    
    status = db.Column(db.String(20), default='active')
    is_deleted = db.Column(db.Boolean, default=False, index=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_restocked_at = db.Column(db.DateTime, nullable=True)
    
    @property
    def available_quantity(self):
        return self.quantity - self.reserved_quantity
    
    @property
    def stock_status(self):
        if self.available_quantity <= 0:
            return 'out_of_stock'
        if self.available_quantity <= self.min_stock:
            return 'low_stock'
        if self.available_quantity >= self.max_stock:
            return 'overstock'
        return 'in_stock'
    
    def to_dict(self):
        return {
            'id': self.id,
            'sku': self.sku,
            'name': self.name,
            'description': self.description,
            'category': self.category.name if self.category else None,
            'quantity': self.quantity,
            'available_quantity': self.available_quantity,
            'unit': self.unit,
            'min_stock': self.min_stock,
            'max_stock': self.max_stock,
            'purchase_price': self.purchase_price,
            'selling_price': self.selling_price,
            'tax_rate': self.tax_rate,
            'supplier': self.supplier,
            'warehouse': self.warehouse,
            'status': self.status,
            'stock_status': self.stock_status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

class StockMovement(db.Model):
    __tablename__ = 'stock_movements'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    movement_type = db.Column(db.String(20), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    previous_quantity = db.Column(db.Integer)
    new_quantity = db.Column(db.Integer)
    notes = db.Column(db.Text)
    performed_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)