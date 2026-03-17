from app import create_app, db
from app.models import Service, Location
from datetime import time

app = create_app()

with app.app_context():
    # Define services
    services_data = [
        {'id': 1, 'name': 'Pension Disbursement', 'code': 'P', 'icon': 'fa-hand-holding-dollar'},
        {'id': 2, 'name': 'Senior Citizen Scheme', 'code': 'S', 'icon': 'fa-users-viewfinder'},
        {'id': 3, 'name': 'Retirement Benefit Claim', 'code': 'R', 'icon': 'fa-file-invoice-dollar'},
        {'id': 4, 'name': 'Digital Life Certificate Sync', 'code': 'D', 'icon': 'fa-fingerprint'},
        {'id': 5, 'name': 'Elderly Health Checkup Registry', 'code': 'H', 'icon': 'fa-heart-pulse'},
        {'id': 6, 'name': 'Fixed Deposit / Savings', 'code': 'F', 'icon': 'fa-piggy-bank'},
        {'id': 7, 'name': 'Asset Management', 'code': 'A', 'icon': 'fa-chart-pie'},
        {'id': 8, 'name': 'Tax & Legal Assistance', 'code': 'T', 'icon': 'fa-scale-balanced'}
    ]

    print("Seeding services...")
    for s_data in services_data:
        existing = Service.query.get(s_data['id'])
        if not existing:
            s = Service(
                service_id=s_data['id'],
                service_name=s_data['name'],
                service_code=s_data['code'],
                icon=s_data['icon'],
                is_active=True
            )
            db.session.add(s)
            print(f"Created service: {s_data['name']}")
        else:
            print(f"Service {s_data['name']} already exists.")
    
    db.session.commit()

    print("Seeding locations...")
    # Create one location for each service (1-to-1 mapping as used in frontend)
    for s_data in services_data:
        existing = Location.query.get(s_data['id'])
        if not existing:
            l = Location(
                location_id=s_data['id'],
                service_id=s_data['id'],
                location_name=f"{s_data['name']} Counter",
                address="Main Center, Floor 1",
                operating_hours_start=time(9, 0),
                operating_hours_end=time(17, 0),
                is_active=True
            )
            db.session.add(l)
            print(f"Created location for: {s_data['name']}")
        else:
            print(f"Location for {s_data['name']} already exists.")
    
    db.session.commit()
    print("Database seeded successfully!")
