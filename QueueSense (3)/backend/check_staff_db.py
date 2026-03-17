from app import create_app, db
from app.models import Staff, User

app = create_app()

with app.app_context():
    staff_members = Staff.query.all()
    print(f"{'Staff ID':<10} | {'User ID':<10} | {'Username':<20} | {'Counter':<10}")
    print("-" * 60)
    for s in staff_members:
        username = s.user.username if s.user else "N/A"
        print(f"{s.staff_id:<10} | {s.user_id:<10} | {username:<20} | {s.counter_number:<10}")
