from app import create_app, db
from app.models.user import User, Role, Permission
from app.models.product import Product
from app.models.sale import SaleEntry
from app.models.hr import Attendance, Recruitment
from app.models.task import Task
from datetime import datetime, date, timedelta
import random

def seed_database():
    app = create_app()
    
    with app.app_context():
        if Role.query.count() > 0:
            print("✅ Database already seeded, skipping...")
            return
        
        print("🌱 Seeding database...")
        
        # Create Roles
        roles_data = {
            'Administrateur': 'Full system access',
            'Stock': 'Inventory management',
            'Commercial': 'Sales and reports',
            'RH': 'HR management',
            'Manager': 'Department oversight'
        }
        
        roles = {}
        for name, desc in roles_data.items():
            role = Role(name=name, description=desc, is_system=True)
            db.session.add(role)
            roles[name] = role
        
        db.session.flush()
        print("✓ Roles created")
        
        # Create Permissions
        permissions = [
            ('Administrateur', 'admin', True, True, True),
            ('Administrateur', 'stock', True, True, True),
            ('Administrateur', 'sales', True, True, True),
            ('Administrateur', 'hr', True, True, True),
            ('Administrateur', 'manager', True, True, True),
            ('Stock', 'stock', True, True, True),
            ('Commercial', 'sales', True, True, True),
            ('RH', 'hr', True, True, True),
            ('Manager', 'manager', True, True, True),
        ]
        
        for role_name, module, read, write, delete in permissions:
            role = roles[role_name]
            perm = Permission(
                role_id=role.id,
                module=module,
                can_read=read,
                can_write=write,
                can_delete=delete
            )
            db.session.add(perm)
        
        db.session.commit()
        print("✓ Permissions created")
        
        # Create Users
        users_data = [
            ('admin', 'admin@flowzen.com', 'admin123', 'Administrateur', 'Admin User', 'IT', '#3B6FE8'),
            ('stock1', 'stock1@flowzen.com', 'stock123', 'Stock', 'Karim Trabelsi', 'Logistics', '#F59E0B'),
            ('commercial1', 'commercial1@flowzen.com', 'com123', 'Commercial', 'Yassine Khadri', 'Sales', '#EC4899'),
            ('rh1', 'rh1@flowzen.com', 'rh123', 'RH', 'Sara Benali', 'HR', '#10B981'),
            ('manager1', 'manager1@flowzen.com', 'manager123', 'Manager', 'Nadia Mansouri', 'Operations', '#8B5CF6'),
        ]
        
        users = {}
        for username, email, pw, role_name, full_name, dept, color in users_data:
            user = User(
                username=username,
                email=email,
                full_name=full_name,
                role_id=roles[role_name].id,
                department=dept,
                avatar_color=color,
                is_active=True
            )
            user.set_password(pw)
            db.session.add(user)
            users[username] = user
        
        db.session.commit()
        print("✓ Users created")
        
        # Create Products
        products_data = [
            ('SKU-001', 'Laptop Dell XPS 15', 10, 1200.0, 3, 50),
            ('SKU-002', 'Office Chair Pro', 5, 180.0, 2, 30),
            ('SKU-003', 'USB-C Hub 7-in-1', 25, 35.0, 5, 100),
            ('SKU-004', 'Wireless Keyboard', 8, 99.0, 3, 60),
            ('SKU-005', 'Monitor LG 27"', 4, 480.0, 2, 25),
        ]
        
        for sku, name, qty, price, min_s, max_s in products_data:
            prod = Product(
                sku=sku,
                name=name,
                quantity=qty,
                selling_price=price,
                min_stock=min_s,
                max_stock=max_s,
                tax_rate=19.0,
                status='active'
            )
            db.session.add(prod)
        
        db.session.commit()
        print("✓ Products created")
        
        # Create Sales
        commercial = users['commercial1']
        for i in range(20):
            prod = Product.query.first()
            qty = random.randint(1, 3)
            discount = random.choice([0, 5, 10])
            revenue = qty * prod.selling_price * (1 - discount / 100)
            
            sale = SaleEntry(
                invoice_number=f"INV-2024{str(i+1).zfill(4)}",
                product_id=prod.id,
                seller_id=commercial.id,
                quantity_sold=qty,
                unit_price=prod.selling_price,
                discount_percent=discount,
                discount_amount=round(qty * prod.selling_price * discount / 100, 2),
                tax_amount=round(revenue * 0.19, 2),
                subtotal=round(qty * prod.selling_price, 2),
                total=round(revenue, 2),
                sale_date=datetime.utcnow() - timedelta(days=random.randint(1, 30)),
                payment_method=random.choice(['cash', 'card'])
            )
            db.session.add(sale)
        
        # Create Tasks
        manager = users['manager1']
        tasks_data = [
            ('Audit Stock Q2', 'Complete inventory count', 'stock1', 'high', 'todo', 7),
            ('Monthly Sales Report', 'Generate April report', 'commercial1', 'high', 'todo', 5),
            ('Prepare Onboarding', 'New hire orientation', 'rh1', 'medium', 'in_progress', 3),
            ('HR Dashboard', 'Compile metrics for board', 'rh1', 'critical', 'todo', 10),
        ]
        
        for title, desc, assignee_key, priority, status, days in tasks_data:
            task = Task(
                title=title,
                description=desc,
                assignee_id=users[assignee_key].id,
                creator_id=manager.id,
                department=users[assignee_key].department,
                priority=priority,
                status=status,
                due_date=datetime.utcnow() + timedelta(days=days)
            )
            db.session.add(task)
        
        # Create Recruitments
        rh = users['rh1']
        recs_data = [
            ('Senior Backend Engineer', 'IT', 'open', 30),
            ('Sales Representative', 'Sales', 'in_progress', 20),
            ('HR Business Partner', 'HR', 'open', 45),
        ]
        
        for pos, dept, status, days in recs_data:
            rec = Recruitment(
                position=pos,
                department=dept,
                status=status,
                number_of_openings=1,
                description=f'Looking for {pos}',
                target_date=date.today() + timedelta(days=days),
                created_by=rh.id
            )
            db.session.add(rec)
        
        db.session.commit()
        
        print("\n" + "="*50)
        print("✅ DATABASE SEEDED SUCCESSFULLY!")
        print("="*50)
        print("\n📋 DEMO ACCOUNTS:")
        print("   ┌─────────────────┬──────────────┬─────────────────┐")
        print("   │ Username        │ Password     │ Role            │")
        print("   ├─────────────────┼──────────────┼─────────────────┤")
        print("   │ admin           │ admin123     │ Administrateur  │")
        print("   │ stock1          │ stock123     │ Stock           │")
        print("   │ commercial1     │ com123       │ Commercial      │")
        print("   │ rh1             │ rh123        │ RH              │")
        print("   │ manager1        │ manager123   │ Manager         │")
        print("   └─────────────────┴──────────────┴─────────────────┘")
        print("\n🚀 You can now run: python run.py")

if __name__ == '__main__':
    seed_database()