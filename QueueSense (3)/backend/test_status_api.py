import sys
import os
import json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import create_app
from app.api.queues import get_queue_status

app = create_app()
with app.app_context():
    response, status_code = get_queue_status(0, 0)
    data = response.get_json()
    print(json.dumps(data, indent=2))
