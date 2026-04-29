from datetime import datetime
from app.extensions import db

class SaleEntry(db.Model):
    __tablename__ = 'sale_entries'
    
    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(50), unique=True, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    quantity_sold = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    discount_percent = db.Column(db.Float, default=0.0)
    discount_amount = db.Column(db.Float, default=0.0)
    tax_amount = db.Column(db.Float, default=0.0)
    subtotal = db.Column(db.Float, nullable=False)
    total = db.Column(db.Float, nullable=False)
    
    sale_date = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    payment_method = db.Column(db.String(30), default='cash')
    notes = db.Column(db.Text, default='')
    
    def to_dict(self):
        return {
            'id': self.id,
            'invoice_number': self.invoice_number,
            'product_id': self.product_id,
            'product_name': self.product.name if self.product else None,
            'quantity_sold': self.quantity_sold,
            'unit_price': self.unit_price,
            'discount_percent': self.discount_percent,
            'discount_amount': self.discount_amount,
            'tax_amount': self.tax_amount,
            'subtotal': self.subtotal,
            'total': self.total,
            'sale_date': self.sale_date.isoformat() if self.sale_date else None,
            'payment_method': self.payment_method,
            'notes': self.notes,
        }

class RevenueTarget(db.Model):
    __tablename__ = 'revenue_targets'
    
    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, nullable=False)
    month = db.Column(db.Integer, nullable=False)
    target_amount = db.Column(db.Float, nullable=False)
    actual_amount = db.Column(db.Float, default=0.0)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @property
    def achievement_percent(self):
        if self.target_amount > 0:
            return round((self.actual_amount / self.target_amount) * 100, 1)
        return 0
    
    def to_dict(self):
        return {
            'id': self.id,
            'year': self.year,
            'month': self.month,
            'target_amount': self.target_amount,
            'actual_amount': self.actual_amount,
            'achievement_percent': self.achievement_percent,
        }