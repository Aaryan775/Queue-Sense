from app import create_app, db
from app.models import User, Staff
import bcrypt

app = create_app()

with app.app_context():
    # Use raw connection to ensure FK checks are disabled for the session
    with db.engine.connect() as conn:
        print("Disabling foreign key checks and dropping tables...")
        conn.execute(db.text("SET FOREIGN_KEY_CHECKS = 0"))
        
        # Drop tables explicitly using raw SQL because drop_all() is being stubborn
        tables = ['appointments', 'queues', 'staff', 'users', 'locations', 'services', 'alembic_version']
        for table in tables:
            try:
                conn.execute(db.text(f"DROP TABLE IF EXISTS {table}"))
                print(f"Dropped {table}")
            except Exception as e:
                print(f"Error dropping {table}: {e}")
        
        conn.execute(db.text("SET FOREIGN_KEY_CHECKS = 1"))
        conn.commit()
        print("Tables dropped.")
    
    print("Creating all tables...")
    db.create_all()
    print("Tables created.")
    
    # Create a demo user
    print("Creating demo user...")
    password = 'User@123'
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(password_bytes, salt)
    
    demo_user = User(
        username='demo',
        password_hash=password_hash.decode('utf-8'),
        name='Demo User',
        phone='1234567890',
        age=25,
        category='normal',
        role='user',
        is_active=True
    )
    db.session.add(demo_user)
    
    # Create Admin User
    print("Creating admin user...")
    admin_pass = 'Admin@123'
    admin_hash = bcrypt.hashpw(admin_pass.encode('utf-8'), bcrypt.gensalt())
    
    admin_user = User(
        username='admin',
        password_hash=admin_hash.decode('utf-8'),
        name='System Administrator',
        phone='9999999999',
        age=40,
        category='normal',
        role='admin',
        is_active=True
    )
    db.session.add(admin_user)
    
    # Create Staff User
    print("Creating staff user...")
    staff_pass = 'Staff@123'
    staff_hash = bcrypt.hashpw(staff_pass.encode('utf-8'), bcrypt.gensalt())
    
    staff_user = User(
        username='staff',
        password_hash=staff_hash.decode('utf-8'),
        name='Staff Member',
        phone='8888888888',
        age=30,
        category='normal',
        role='staff',
        is_active=True
    )
    db.session.add(staff_user)
    db.session.commit() # Commit users first to get IDs
    
    # Add to Staff table
    new_staff_entry = Staff(
        user_id=staff_user.user_id,
        assigned_services=[],
        counter_number=1,
        is_available=True
    )
    db.session.add(new_staff_entry)
    db.session.commit()

    print("Users created:")
    print("1. User: username='demo', password='User@123'")
    print("2. Admin: username='admin', password='Admin@123'")
    print("3. Staff: username='staff', password='Staff@123'")
    print("Database fixed successfully!")
