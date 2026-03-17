import sys
import os
import json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import create_app
from app.api.analytics import get_dashboard_stats

app = create_app()
with app.app_context():
    # Simulate a staff user
    class MockUser:
        user_id = 99
        role = 'staff'
    
    # We need to bypass the @token_required decorator or mock it
    # For now, let's just call the internal logic if possible, 
    # but the route has decorators.
    # Let's try calling the function directly if we can mock current_user.
    
    # Re-importing without decorators is hard. 
    # Let's just use the flask test client.
    client = app.test_client()
    # Mocking token might be hard. 
    # Let's just use the DB query logic directly from analytics.py since I know it.
    
    from app.models import QueueElder, QueueNormal
    from datetime import datetime
    
    today = datetime.utcnow().date()
    e_serving = QueueElder.query.filter(QueueElder.status.in_(['called', 'serving'])).count()
    n_serving = QueueNormal.query.filter(QueueNormal.status.in_(['called', 'serving'])).count()
    currently_serving = e_serving + n_serving
    
    print(f"Currently Serving Count: {currently_serving}")
