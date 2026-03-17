from app import create_app, db
from app.models import User, Service, Location, QueueElder, QueueNormal, Appointment
from datetime import datetime, timedelta, time
import random

app = create_app()
with app.app_context():
    # Clear existing data (optional, but good for clean demo)
    QueueElder.query.delete()
    QueueNormal.query.delete()
    Appointment.query.delete()
    # User.query.filter(User.role == 'user').delete()
    db.session.commit()

    # Get services and locations
    services = Service.query.all()
    locations = Location.query.all()
    
    if not services or not locations:
        print("Error: Please run seed_db.py first to create services and locations.")
        exit()

    # Create dummy users if not enough
    existing_users = User.query.filter_by(role='user').all()
    if len(existing_users) < 20:
        names = ["Aarav Sharma", "Vivaan Patel", "Aditya Gupta", "Vihaan Singh", "Arjun Verma", 
                 "Sai Kumar", "Ishaan Reddy", "Krishna Rao", "Rohan Joshi", "Aryan Malhotra",
                 "Sanya Kapoor", "Ananya Deshmukh", "Zara Khan", "Myra Iyer", "Kyra Nair"]
        
        for i in range(20 - len(existing_users)):
            name = random.choice(names) + f" {i}"
            u = User(
                username=f"user_{i}_{random.randint(100,999)}@example.com",
                password_hash='pbkdf2:sha256:260000$...',
                name=name,
                phone=f"98765{random.randint(10000,99999)}",
                category=random.choice(['normal', 'elder']),
                role='user',
                is_active=True
            )
            db.session.add(u)
        db.session.commit()
        existing_users = User.query.filter_by(role='user').all()

    # Generate historical data for today (Hourly Load)
    current_time = datetime.utcnow()
    start_of_day = current_time.replace(hour=8, minute=0, second=0, microsecond=0)
    
    print("Generating demo queue entries...")
    for i in range(100):
        user = random.choice(existing_users)
        service = random.choice(services)
        location = random.choice(locations)
        
        # Random time between 9 AM and now
        random_minutes = random.randint(0, int((current_time - start_of_day).total_seconds() // 60))
        check_in = start_of_day + timedelta(minutes=random_minutes)
        
        is_elder = user.category == 'elder'
        
        # Determine status: 50% waiting, 40% completed, 10% no_show
        status_weights = [50, 40, 10]
        status = random.choices(['waiting', 'completed', 'no_show'], weights=status_weights)[0]
            entry = QueueElder(
                user_id=user.user_id,
                service_id=service.service_id,
                location_id=location.location_id,
                token=f"E{random.randint(100,999)}",
                check_in_time=check_in,
                status=random.choices(['waiting', 'completed', 'no_show'], weights=[20, 70, 10])[0],
                is_emergency=random.random() < 0.1
            )
        else:
            entry = QueueNormal(
                user_id=user.user_id,
                service_id=service.service_id,
                location_id=location.location_id,
                token=f"N{random.randint(100,999)}",
                check_in_time=check_in,
                status=random.choices(['waiting', 'completed', 'no_show'], weights=[20, 70, 10])[0]
            )
            
        if entry.status == 'completed':
            entry.served_flag = True
            # 60% within SLA (5-14 mins), 40% outside (16-45 mins)
            within_sla = random.random() < 0.6
            wait_mins = random.randint(5, 14) if within_sla else random.randint(16, 45)
            entry.called_time = entry.check_in_time + timedelta(minutes=wait_mins)
            entry.served_time = entry.called_time + timedelta(minutes=random.randint(10, 20))
            entry.counter_number = random.randint(1, 5)

        db.session.add(entry)

    db.session.commit()
    print("Demo data generation completed.")
