import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import create_app, db
from app.models import QueueElder, QueueNormal

app = create_app()
with app.app_context():
    print("--- Detailed Status Check ---")
    
    def print_entries(title, model):
        print(f"\n[{title}]")
        entries = model.query.filter(model.status.in_(['waiting', 'called', 'serving'])).all()
        if not entries:
            print("No active entries.")
        for e in entries:
            print(f"- {e.token} | Status: {e.status} | Service: {e.service_id} | Location: {e.location_id} | Counter: {e.counter_number}")

    print_entries("ELDER", QueueElder)
    print_entries("NORMAL", QueueNormal)
