from app import create_app, db
from app.models import User, Staff
import bcrypt

app = create_app()

def create_staff_user(username, password, name, role='staff', counter_number=1):
    with app.app_context():
        # 1. Check if user already exists
        user = User.query.filter_by(username=username).first()
        
        if not user:
            print(f"Creating user '{username}'...")
            password_bytes = password.encode('utf-8')
            salt = bcrypt.gensalt()
            password_hash = bcrypt.hashpw(password_bytes, salt)
            
            user = User(
                username=username,
                password_hash=password_hash.decode('utf-8'),
                name=name,
                role=role,
                is_active=True
            )
            db.session.add(user)
            db.session.commit()
            print(f"User '{username}' created successfully.")
        else:
            print(f"User '{username}' already exists. Updating password...")
            password_bytes = password.encode('utf-8')
            salt = bcrypt.gensalt()
            password_hash = bcrypt.hashpw(password_bytes, salt)
            user.password_hash = password_hash.decode('utf-8')
            db.session.commit()

        # 2. Check if staff entry exists
        staff = Staff.query.filter_by(user_id=user.user_id).first()
        if not staff:
            print(f"Creating staff record for user '{username}'...")
            staff = Staff(
                user_id=user.user_id,
                counter_number=counter_number,
                is_available=True
            )
            db.session.add(staff)
            db.session.commit()
            print(f"Staff record created successfully.")
        else:
            print(f"Staff record already exists for user '{username}'.")

if __name__ == "__main__":
    print("Fixing staff login...")
    create_staff_user('staff', 'Staff@123', 'Default Staff', counter_number=1)
    print("Done!")
