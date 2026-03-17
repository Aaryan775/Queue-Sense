from app import create_app, db
from app.models import Analytics, QueueElder, QueueNormal, User
from sqlalchemy import func
from datetime import datetime

app = create_app()
with app.app_context():
    try:
        print("Checking Analytics sum...")
        historical_total = db.session.query(func.sum(Analytics.total_users_served)).scalar()
        print(f"Historical Total: {historical_total}")
        
        print("Checking Live today...")
        today = datetime.utcnow().date()
        elder_today = QueueElder.query.filter(
            QueueElder.status == 'completed',
            func.date(QueueElder.served_time) == today
        ).count()
        print(f"Elder Today: {elder_today}")
        
        print("Checking Happy Clients...")
        # Fix: User query might be the issue if models aren't linked correctly in the join
        historical_users = db.session.query(User.user_id).join(
            QueueElder, User.user_id == QueueElder.user_id
        ).filter(QueueElder.status == 'completed').distinct().count()
        print(f"Historical Users: {historical_users}")
        
    except Exception as e:
        print(f"Caught error: {e}")
        import traceback
        traceback.print_exc()
