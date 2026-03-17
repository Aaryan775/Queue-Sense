from app import create_app, db
from app.models import User
import bcrypt

app = create_app()

def reset_password(username, new_password):
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        if user:
            password_bytes = new_password.encode('utf-8')
            salt = bcrypt.gensalt()
            password_hash = bcrypt.hashpw(password_bytes, salt)
            
            user.password_hash = password_hash.decode('utf-8')
            db.session.commit()
            print(f"Password for '{username}' reset successfully.")
        else:
            print(f"User '{username}' not found!")

if __name__ == "__main__":
    print("Resetting demo account passwords...")
    reset_password('demo', 'User@123')
    reset_password('admin', 'Admin@123')
    reset_password('staff', 'Staff@123')
    print("Done! You can now login with these credentials.")
