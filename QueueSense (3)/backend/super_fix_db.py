from app import create_app, db
from app.models import User, Staff, Service, Location
import bcrypt
from datetime import time

app = create_app()

with app.app_context():
    # 1. Disable FK checks and drop ALL recognized tables
    with db.engine.connect() as conn:
        print("Cleaning database...")
        conn.execute(db.text("SET FOREIGN_KEY_CHECKS = 0"))
        
        # Comprehensive table list from inspector
        tables = ['analytics', 'appointments', 'locations', 'queue_elder', 'queue_normal', 
                  'services', 'staff', 'staff_services', 'system_settings', 'users', 'alembic_version']
        
        for table in tables:
            try:
                conn.execute(db.text(f"DROP TABLE IF EXISTS {table}"))
                print(f"  Dropped table: {table}")
            except Exception as e:
                print(f"  Error dropping {table}: {e}")
        
        conn.execute(db.text("SET FOREIGN_KEY_CHECKS = 1"))
        conn.commit()

    # 2. Create tables
    print("Re-creating schema...")
    db.create_all()

    # 3. Seed Users
    print("Seeding users...")
    password_hash = bcrypt.hashpw('User@123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    admin_hash = bcrypt.hashpw('Admin@123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    staff_hash = bcrypt.hashpw('Staff@123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    users = [
        User(username='demo', password_hash=password_hash, name='Demo User', phone='1234567890', role='user', is_active=True),
        User(username='admin', password_hash=admin_hash, name='Queen Master Admin', phone='9999999999', role='admin', is_active=True),
        User(username='staff', password_hash=staff_hash, name='Front Desk Staff', phone='8888888888', role='staff', is_active=True)
    ]
    for u in users: db.session.add(u)
    db.session.commit()

    # 4. Seed Staff Entry
    staff_user = User.query.filter_by(username='staff').first()
    new_staff_entry = Staff(user_id=staff_user.user_id, assigned_services=[1,2,3,4,5,6,7,8], counter_number=1, is_available=True)
    db.session.add(new_staff_entry)

    # 5. Seed Services (Explicitly IDs 1-8)
    print("Seeding services...")
    services_data = [
        {'id': 1, 'name': 'Pension Disbursement', 'code': 'P', 'icon': 'fa-hand-holding-dollar'},
        {'id': 2, 'name': 'Senior Citizen Scheme', 'code': 'S', 'icon': 'fa-users-viewfinder'},
        {'id': 3, 'name': 'Retirement Benefit Claim', 'code': 'R', 'icon': 'fa-file-invoice-dollar'},
        {'id': 4, 'name': 'Digital Life Certificate Sync', 'code': 'D', 'icon': 'fa-fingerprint'},
        {'id': 5, 'name': 'Elderly Health Checkup Registry', 'code': 'H', 'icon': 'fa-heart-pulse'},
        {'id': 6, 'name': 'Fixed Deposit / Savings', 'code': 'F', 'icon': 'fa-piggy-bank'},
        {'id': 7, 'name': 'Asset Management', 'code': 'A', 'icon': 'fa-chart-pie'},
        {'id': 8, 'name': 'Tax & Legal Assistance', 'code': 'T', 'icon': 'fa-scale-balanced'}
    ]

    for s_data in services_data:
        s = Service(
            service_id=s_data['id'],
            service_name=s_data['name'],
            service_code=s_data['code'],
            icon=s_data['icon'],
            is_active=True
        )
        db.session.add(s)
        
        # Seed Location for each service
        l = Location(
            location_id=s_data['id'],
            service_id=s_data['id'],
            location_name=f"{s_data['name']} Counter",
            address="Main Center, Floor 1",
            operating_hours_start=time(9, 0),
            operating_hours_end=time(17, 0),
            is_active=True
        )
        db.session.add(l)

    db.session.commit()
    print("Database fully reset and seeded successfully!")
