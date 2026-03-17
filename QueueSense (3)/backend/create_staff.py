from app import create_app, db
from app.models import User
import bcrypt

app = create_app()
with app.app_context():
    # Remove existing staff test user
    User.query.filter_by(username='staff@test.com').delete()
    db.session.commit()
    
    # Create new staff user
    password_bytes = 'password'.encode('utf-8')
    salt = bcrypt.gensalt()
    hash_str = bcrypt.hashpw(password_bytes, salt).decode('utf-8')
    
    u = User(
        username='staff@test.com',
        password_hash=hash_str,
        name='Test Staff',
        role='staff',
        is_active=True
    )
    db.session.add(u)
    db.session.commit()
    print('Staff user created with bcrypt: staff@test.com / password')
