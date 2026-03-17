from app import create_app, db
from app.models import User

app = create_app()

with app.app_context():
    users = User.query.all()
    print(f"{'Username':<20} | {'Role':<10} | {'Is Active':<10} | {'Password Hash':<60}")
    print("-" * 110)
    for user in users:
        print(f"{user.username:<20} | {user.role:<10} | {str(user.is_active):<10} | {user.password_hash}")
