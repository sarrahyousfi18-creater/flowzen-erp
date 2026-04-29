from flask import Blueprint, request, jsonify, session
from app.extensions import db
from app.models.product import Product
from app.models.sale import SaleEntry, RevenueTarget
from app.middleware.auth import login_required, role_required
from datetime import datetime
from sqlalchemy import func

sales_bp = Blueprint('sales', __name__)
ALLOWED_ROLES = ('Administrateur', 'Commercial', 'Manager')

@sales_bp.route('/', methods=['GET'])
@login_required
def get_sales():
    """Get sales entries with pagination"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    
    query = SaleEntry.query
    
    if year and month:
        start = datetime(year, month, 1)
        if month == 12:
            end = datetime(year + 1, 1, 1)
        else:
            end = datetime(year, month + 1, 1)
        query = query.filter(
            SaleEntry.sale_date >= start,
            SaleEntry.sale_date < end
        )
    
    paginated = query.order_by(SaleEntry.sale_date.desc()).paginate(page=page, per_page=per_page)
    
    return jsonify({
        'sales': [s.to_dict() for s in paginated.items],
        'total': paginated.total,
        'page': page,
        'per_page': per_page,
        'pages': paginated.pages
    })

@sales_bp.route('/', methods=['POST'])
@role_required(*ALLOWED_ROLES)
def record_sale():
    """Record a new sale"""
    data = request.get_json()
    
    required = ['product_id', 'quantity']
    for field in required:
        if not data.get(field):
            return jsonify({'error': f'Field "{field}" is required'}), 400
    
    product = Product.query.get(data['product_id'])
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    
    if product.status == 'blocked':
        return jsonify({'error': 'Product is blocked and cannot be sold'}), 400
    
    qty = int(data['quantity'])
    if product.quantity < qty:
        return jsonify({'error': f'Insufficient stock. Available: {product.quantity}'}), 400
    
    discount_percent = float(data.get('discount_percent', 0))
    unit_price = product.selling_price
    subtotal = qty * unit_price
    discount_amount = subtotal * (discount_percent / 100)
    taxable_amount = subtotal - discount_amount
    tax_amount = taxable_amount * (product.tax_rate / 100)
    total = taxable_amount + tax_amount
    
    # Generate invoice number
    last_invoice = SaleEntry.query.order_by(SaleEntry.id.desc()).first()
    if last_invoice and last_invoice.invoice_number:
        try:
            num = int(last_invoice.invoice_number.split('-')[-1]) + 1
        except:
            num = 1
    else:
        num = 1
    invoice_number = f"INV-{datetime.utcnow().strftime('%Y%m')}-{num:06d}"
    
    sale = SaleEntry(
        invoice_number=invoice_number,
        product_id=product.id,
        seller_id=session.get('user_id'),
        quantity_sold=qty,
        unit_price=unit_price,
        discount_percent=discount_percent,
        discount_amount=round(discount_amount, 2),
        tax_amount=round(tax_amount, 2),
        subtotal=round(subtotal, 2),
        total=round(total, 2),
        payment_method=data.get('payment_method', 'cash'),
        notes=data.get('notes', '')
    )
    
    # Update stock
    product.quantity -= qty
    
    db.session.add(sale)
    db.session.commit()
    
    return jsonify(sale.to_dict()), 201

@sales_bp.route('/report', methods=['GET'])
@login_required
def get_sales_report():
    """Generate monthly sales report"""
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    
    if not year or not month:
        now = datetime.utcnow()
        year = year or now.year
        month = month or now.month
    
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)
    
    sales = SaleEntry.query.filter(
        SaleEntry.sale_date >= start_date,
        SaleEntry.sale_date < end_date
    ).all()
    
    total_revenue = sum(s.total for s in sales)
    total_quantity = sum(s.quantity_sold for s in sales)
    total_discount = sum(s.discount_amount for s in sales)
    
    # Sales by product
    product_sales = {}
    for sale in sales:
        key = sale.product_id
        if key not in product_sales:
            product_sales[key] = {
                'product_name': sale.product.name if sale.product else 'Unknown',
                'product_sku': sale.product.sku if sale.product else None,
                'quantity': 0,
                'revenue': 0.0
            }
        product_sales[key]['quantity'] += sale.quantity_sold
        product_sales[key]['revenue'] += sale.total
    
    # Sales by day
    daily_sales = {}
    for sale in sales:
        day = sale.sale_date.strftime('%Y-%m-%d')
        daily_sales[day] = daily_sales.get(day, 0) + sale.total
    
    return jsonify({
        'year': year,
        'month': month,
        'total_revenue': round(total_revenue, 2),
        'total_quantity': total_quantity,
        'total_discount': round(total_discount, 2),
        'transaction_count': len(sales),
        'average_transaction': round(total_revenue / len(sales), 2) if sales else 0,
        'product_sales': list(product_sales.values()),
        'daily_sales': [{'date': k, 'revenue': v} for k, v in daily_sales.items()],
        'sales': [s.to_dict() for s in sales]
    })

@sales_bp.route('/targets', methods=['GET'])
@role_required(*ALLOWED_ROLES)
def get_revenue_targets():
    """Get revenue targets"""
    year = request.args.get('year', type=int)
    
    query = RevenueTarget.query.order_by(RevenueTarget.year.desc(), RevenueTarget.month.desc())
    if year:
        query = query.filter_by(year=year)
    
    targets = query.all()
    return jsonify([t.to_dict() for t in targets])

@sales_bp.route('/targets', methods=['POST'])
@role_required(*ALLOWED_ROLES)
def set_revenue_target():
    """Set revenue target for a period"""
    data = request.get_json()
    
    if not data.get('year') or not data.get('month') or not data.get('target_amount'):
        return jsonify({'error': 'year, month, and target_amount are required'}), 400
    
    target = RevenueTarget.query.filter_by(
        year=data['year'],
        month=data['month']
    ).first()
    
    if target:
        target.target_amount = float(data['target_amount'])
    else:
        target = RevenueTarget(
            year=data['year'],
            month=data['month'],
            target_amount=float(data['target_amount']),
            created_by=session.get('user_id')
        )
        db.session.add(target)
    
    db.session.commit()
    return jsonify(target.to_dict()), 201

@sales_bp.route('/discounts/apply', methods=['POST'])
@role_required(*ALLOWED_ROLES)
def apply_discount():
    """Apply discount to a product"""
    data = request.get_json()
    
    product_id = data.get('product_id')
    discount_percent = float(data.get('discount_percent', 0))
    
    if not product_id:
        return jsonify({'error': 'product_id is required'}), 400
    
    if discount_percent < 0 or discount_percent > 60:
        return jsonify({'error': 'Discount must be between 0% and 60%'}), 400
    
    product = Product.query.get_or_404(product_id)
    
    original_price = product.selling_price
    product.selling_price = round(original_price * (1 - discount_percent / 100), 2)
    db.session.commit()
    
    return jsonify({
        'product_id': product_id,
        'product_name': product.name,
        'original_price': original_price,
        'discount_percent': discount_percent,
        'new_price': product.selling_price
    })