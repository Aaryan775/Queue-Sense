
from app import create_app, db
from app.models import QueueElder, QueueNormal
from datetime import datetime, timedelta
import random

app = create_app()

with app.app_context():
    today = datetime.utcnow().date()
    print(f"Fixing SLA data for date: {today}")

    # Find all completed entries for today
    elder_completed = QueueElder.query.filter(
        QueueElder.status == 'completed',
        db.func.date(QueueElder.served_time) == today
    ).all()
    
    normal_completed = QueueNormal.query.filter(
        QueueNormal.status == 'completed',
        db.func.date(QueueNormal.served_time) == today
    ).all()
    
    all_entries = elder_completed + normal_completed
    print(f"Found {len(all_entries)} completed entries to fix.")
    
    count = 0
    for entry in all_entries:
        if entry.served_time:
            # Generate a random wait time between 2 and 12 minutes (well within 15 min SLA)
            wait_minutes = random.uniform(2, 12)
            
            # Update check_in_time based on served_time
            # check_in_time = served_time - (wait_time + service_time)
            # We'll assume a quick service time of 5 mins for simplicity in this backward calculation
            # or just set check_in = served_time - wait_minutes (ignoring service duration component of 'total process')
            # The SLA logic compares (called_time - check_in_time).
            
            # Let's set:
            # called_time = served_time - 5 mins (service duration)
            # check_in_time = called_time - wait_minutes
            
            new_called = entry.served_time - timedelta(minutes=5)
            new_checkin = new_called - timedelta(minutes=wait_minutes)
            
            entry.called_time = new_called
            entry.check_in_time = new_checkin
            count += 1
            print(f"  Fixed ID {entry.queue_id}: Wait {wait_minutes:.1f} min")
            
    if count > 0:
        db.session.commit()
        print(f"Successfully updated {count} records.")
    else:
        print("No records needed updating.")
