from app import create_app, db
from app.models import QueueNormal, QueueElder

app = create_app()
with app.app_context():
    normal_waiting = QueueNormal.query.filter_by(status='waiting').all()
    elder_waiting = QueueElder.query.filter_by(status='waiting').all()
    
    print(f"Normal Waiting: {len(normal_waiting)}")
    for n in normal_waiting[:5]:
        print(f" - {n.token} (ID: {n.queue_id})")
        
    print(f"Elder Waiting: {len(elder_waiting)}")
    for e in elder_waiting[:5]:
        print(f" - {e.token} (ID: {e.queue_id})")
