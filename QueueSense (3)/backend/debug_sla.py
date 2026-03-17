
from app import create_app, db
from app.models import QueueElder, QueueNormal, Service
from datetime import datetime
from sqlalchemy import func

app = create_app()

with app.app_context():
    today = datetime.utcnow().date()
    print(f"Checking data for date: {today}")

    services = Service.query.all()
    for s in services:
        print(f"Service: {s.service_name} (ID: {s.service_id})")
        
        elder_completed = QueueElder.query.filter(
            QueueElder.service_id == s.service_id,
            QueueElder.status == 'completed',
            func.date(QueueElder.served_time) == today
        ).all()
        
        normal_completed = QueueNormal.query.filter(
            QueueNormal.service_id == s.service_id,
            QueueNormal.status == 'completed',
            func.date(QueueNormal.served_time) == today
        ).all()
        
        print(f"  Elder Completed Today: {len(elder_completed)}")
        print(f"  Normal Completed Today: {len(normal_completed)}")
        
        all_completed = elder_completed + normal_completed
        measurable = 0
        within_sla = 0
        sla_threshold = 15
        
        for e in all_completed:
            if e.called_time and e.check_in_time:
                measurable += 1
                wait = (e.called_time - e.check_in_time).total_seconds() / 60
                if wait <= sla_threshold:
                    within_sla += 1
                else:
                    print(f"    Breach: ID {e.queue_id}, Wait {wait:.1f} min")
            else:
                print(f"    Not Measurable: ID {e.queue_id} (Missing timestamps)")
                
        if measurable > 0:
            sla = (within_sla / measurable) * 100
            print(f"  Calculated SLA: {sla:.1f}%")
        else:
            print("  Calculated SLA: 0% (No measurable entries)")
