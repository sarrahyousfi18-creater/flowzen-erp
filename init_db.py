from app import create_app, db
from app.models.user import User, Role
from app.models.product import Product
from datetime import datetime

print("🔄 Initialisation de la base de données...")

app = create_app()

with app.app_context():
    # 1. Créer les tables
    print("📦 Création des tables...")
    db.create_all()
    print("✓ Tables créées")
    
    # 2. Vérifier si déjà peuplé
    if Role.query.count() > 0:
        print("✅ Base de données déjà initialisée")
    else:
        print("🌱 Peuplement des données...")
        
        # 3. Créer les rôles
        roles = {}
        role_names = ['Administrateur', 'Stock', 'Commercial', 'RH', 'Manager']
        for name in role_names:
            role = Role(name=name, description=f'{name} role', is_system=True)
            db.session.add(role)
            roles[name] = role
            print(f"  ✓ Rôle {name} créé")
        
        db.session.commit()
        
        # 4. Créer les utilisateurs
        users_data = [
            ('admin', 'admin@flowzen.com', 'admin123', 'Administrateur', 'Admin User', 'IT'),
            ('stock1', 'stock1@flowzen.com', 'stock123', 'Stock', 'Karim Trabelsi', 'Logistics'),
            ('commercial1', 'commercial1@flowzen.com', 'com123', 'Commercial', 'Yassine Khadri', 'Sales'),
            ('rh1', 'rh1@flowzen.com', 'rh123', 'RH', 'Sara Benali', 'HR'),
            ('manager1', 'manager1@flowzen.com', 'manager123', 'Manager', 'Nadia Mansouri', 'Operations'),
        ]
        
        for username, email, pw, role_name, full_name, dept in users_data:
            user = User(
                username=username,
                email=email,
                full_name=full_name,
                role_id=roles[role_name].id,
                department=dept,
                is_active=True
            )
            user.set_password(pw)
            db.session.add(user)
            print(f"  ✓ Utilisateur {username} créé (rôle: {role_name})")
        
        db.session.commit()
        
        # 5. Créer quelques produits
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
            print(f"  ✓ Produit {name} créé")
        
        db.session.commit()
        
        print("\n" + "="*60)
        print("✅ BASE DE DONNÉES INITIALISÉE AVEC SUCCÈS !")
        print("="*60)
        print("\n🔐 COMPTES DE TEST :")
        print("   ┌─────────────────┬──────────────┬─────────────────┐")
        print("   │ Utilisateur     │ Mot de passe │ Rôle            │")
        print("   ├─────────────────┼──────────────┼─────────────────┤")
        print("   │ admin           │ admin123     │ Administrateur  │")
        print("   │ stock1          │ stock123     │ Stock           │")
        print("   │ commercial1     │ com123       │ Commercial      │")
        print("   │ rh1             │ rh123        │ RH              │")
        print("   │ manager1        │ manager123   │ Manager         │")
        print("   └─────────────────┴──────────────┴─────────────────┘")
        print("\n🚀 Lancez maintenant : python run.py")

print("\n✨ Initialisation terminée !")