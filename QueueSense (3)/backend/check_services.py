from app import create_app, db
from app.models import Service, Location

app = create_app()

with app.app_context():
    services = Service.query.all()
    print(f"Total services found: {len(services)}")
    for s in services:
        print(f"ID: {s.service_id}, Name: {s.service_name}, Active: {s.is_active}")
        
    locations = Location.query.all()
    print(f"\nTotal locations found: {len(locations)}")
    for l in locations:
        print(f"ID: {l.location_id}, Name: {l.location_name}, Active: {l.is_active}, Service ID: {l.service_id}")
