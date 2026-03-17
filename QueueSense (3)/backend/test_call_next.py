import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import create_app, db
from app.utils.queue_engine import QueueEngine

app = create_app()
with app.app_context():
    print("--- Testing Call Next ---")
    # counter=1, service=0 (Universal), location=0 (Universal)
    result = QueueEngine.call_next(0, 0, 1)
    print(f"Result: {result}")
    
    if 'success' in result:
        print(f"Successfully called: {result['token']} for counter {result['counter_number']}")
        db.session.commit() # Ensure it's committed
    else:
        print(f"Error calling next: {result.get('error')}")
