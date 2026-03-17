from app import create_app, db
from app.models import User
import bcrypt

app = create_app()

def verify_login(username, password):
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        if not user:
            print(f"FAILED: User '{username}' not found.")
            return False
        
        stored_hash = user.password_hash.encode('utf-8')
        input_password = password.encode('utf-8')
        
        if bcrypt.checkpw(input_password, stored_hash):
            print(f"SUCCESS: Login verified for user '{username}'.")
            return True
        else:
            print(f"FAILED: Password verification failed for user '{username}'.")
            return False

if __name__ == "__main__":
    print("Verifying staff login logic...")
    verify_login('staff', 'Staff@123')
