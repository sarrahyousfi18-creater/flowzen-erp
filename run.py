from app import create_app

app = create_app()

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 FLOWZEN ERP SYSTEM")
    print("="*60)
    print("\n📍 Server running at: http://localhost:5000")
    print("\n🔐 Demo Accounts:")
    print("   ┌─────────────────┬──────────────┬─────────────────┐")
    print("   │ Username        │ Password     │ Role            │")
    print("   ├─────────────────┼──────────────┼─────────────────┤")
    print("   │ admin           │ admin123     │ Administrateur  │")
    print("   │ stock1          │ stock123     │ Stock           │")
    print("   │ commercial1     │ com123       │ Commercial      │")
    print("   │ rh1             │ rh123        │ RH              │")
    print("   │ manager1        │ manager123   │ Manager         │")
    print("   └─────────────────┴──────────────┴─────────────────┘")
    print("\n" + "="*60 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)