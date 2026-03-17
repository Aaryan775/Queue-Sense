from app import create_app, db
from app.models import QueueElder, QueueNormal, User
from app.utils.queue_engine import QueueEngine
from datetime import datetime, timedelta

app = create_app()
with app.app_context():
    print("Testing Dummy Data Generation for Yesterday...")
    yesterday = (datetime.utcnow() - timedelta(days=1)).strftime('%Y-%m-%d')
    service_id = 1
    location_id = 1
    
    # Check count before
    count_before = QueueElder.query.count() + QueueNormal.query.count()
    
    result = QueueEngine.generate_dummy_data(service_id, location_id, count_elder=2, count_normal=2, target_date=yesterday)
    print(f"Result: {result}")
    
    count_after = QueueElder.query.count() + QueueNormal.query.count()
    print(f"Entries added: {count_after - count_before}")
    
    # Verify the date
    sample = QueueElder.query.filter_by(service_id=service_id).order_by(QueueElder.queue_id.desc()).first()
    if sample:
        print(f"Sample Entry Date: {sample.check_in_time.date()}")
        if str(sample.check_in_time.date()) == yesterday:
            print("SUCCESS: Data generated for correct date.")
        else:
            print(f"FAILURE: Expected {yesterday}, got {sample.check_in_time.date()}")
            
    print("\nTesting Call Next Priority (Score-Based Jumping)...")
    # Add a normal person who has been waiting for 2 hours (120 mins)
    # 120 mins / 10 = 12 points. Wait weight is usually 1, so 12 points.
    # An elder arriving now gets 3 points (elder weight).
    # Logic: 12 > 3 + 5 -> 12 > 8 (TRUE) -> Normal should jump.
    
    user_n = User.query.filter_by(role='user', category='normal').first()
    user_e = User.query.filter_by(role='user', category='elder').first()
    
    if user_n and user_e:
        # Clear existing waiting to be sure
        QueueElder.query.filter_by(status='waiting', service_id=service_id).delete()
        QueueNormal.query.filter_by(status='waiting', service_id=service_id).delete()
        
        # Add Elder (just arrived)
        entry_e = QueueElder(
            user_id=user_e.user_id, service_id=service_id, location_id=location_id,
            token="E-NEW", status='waiting', check_in_time=datetime.utcnow()
        )
        # Add Normal (arrived 2 hours ago)
        entry_n = QueueNormal(
            user_id=user_n.user_id, service_id=service_id, location_id=location_id,
            token="N-OLD", status='waiting', check_in_time=datetime.utcnow() - timedelta(hours=2)
        )
        db.session.add(entry_e)
        db.session.add(entry_n)
        db.session.commit()
        
        # Now call next
        next_call = QueueEngine.get_next_in_queue(service_id, location_id)
        if next_call['entry']:
            print(f"Priority Call Result: {next_call['entry'].token} (Type: {next_call['queue_type']})")
            if next_call['entry'].token == "N-OLD":
                print("SUCCESS: Normal person with high wait time jumped ahead of new elder.")
            else:
                # Let's check the actual scores
                print(f"Scores -> Elder: {entry_e.priority_score}, Normal: {entry_n.priority_score}")
                print("FAILURE: Normal person did not jump.")
            
    print("\nTesting Cancel Call...")
    # Call someone
    called = QueueEngine.call_next(service_id, location_id, 1)
    if called['success']:
        token = called['token']
        print(f"Called Token: {token}")
        
        # Now cancel
        entry_type = 'elder' if token.startswith('E') else 'normal' # Simplified for test
        # Actually QueueEngine.call_next returns the entry. Let's find it.
        # For simplicity, we'll just check if status is 'called'
        q_id = None
        if token.startswith('P'): # Pension starts with P
            e = QueueElder.query.filter_by(token=token, status='called').first()
            if e: q_id = e.queue_id; q_type = 'elder'
            else:
                n = QueueNormal.query.filter_by(token=token, status='called').first()
                if n: q_id = n.queue_id; q_type = 'normal'
        
        if q_id:
            cancel_res = QueueEngine.cancel_call(q_id, q_type)
            print(f"Cancel Result: {cancel_res}")
            # Check status again
            if q_type == 'elder':
                check = QueueElder.query.get(q_id)
            else:
                check = QueueNormal.query.get(q_id)
            print(f"New Status: {check.status}")
            if check.status == 'waiting':
                print("SUCCESS: Call cancelled.")
            else:
                print("FAILURE: Status not reset.")
