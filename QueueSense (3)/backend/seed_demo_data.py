from app import create_app, db
from app.models import User, Service, Location, QueueElder, QueueNormal, Appointment
from datetime import datetime, timedelta, time
import random

app = create_app()

def get_or_create_users(count, category):
    users = User.query.filter_by(role='user', category=category).limit(count).all()
    if len(users) < count:
        names = ["Aarav Sharma", "Vivaan Patel", "Aditya Gupta", "Vihaan Singh", "Arjun Verma", 
                 "Sai Kumar", "Ishaan Reddy", "Krishna Rao", "Rohan Joshi", "Aryan Malhotra",
                 "Sanya Kapoor", "Ananya Deshmukh", "Zara Khan", "Myra Iyer", "Kyra Nair"]
        for i in range(count - len(users)):
            name = random.choice(names) + f" {category.capitalize()} {i}"
            u = User(
                username=f"{category}_{i}_{random.randint(100,999)}@example.com",
                password_hash='pbkdf2:sha256:260000$...',
                name=name,
                phone=f"9{random.randint(100000000,999999999)}",
                category=category,
                role='user',
                is_active=True
            )
            db.session.add(u)
        db.session.commit()
        users = User.query.filter_by(role='user', category=category).limit(count).all()
    return users

with app.app_context():
    print("Clearing some old demo data...")
    # We don't clear everything to avoid breaking the user's existing flow, but we clear appointments and queues to start fresh for this request.
    QueueElder.query.delete()
    QueueNormal.query.delete()
    Appointment.query.delete()
    db.session.commit()

    services = Service.query.all()
    locations = Location.query.all()
    
    if not services or not locations:
        print("Error: Services/Locations not found.")
        exit()

    normal_users = get_or_create_users(40, 'normal')
    elder_users = get_or_create_users(15, 'elder')

    today = datetime.utcnow().date()
    yesterday = today - timedelta(days=1)
    last_week_start = today - timedelta(days=7)

    # 1. Seed Normal Appointments (Today, Yesterday, Last Week)
    print("Seeding normal appointments...")
    
    today_normal_appointments = []
    # Today (10)
    for i in range(10):
        u = normal_users[i]
        s = random.choice(services)
        l = random.choice(locations)
        start_hour = 10 + (i // 4)
        start_min = (i % 4) * 15
        end_hour = start_hour + ((start_min + 15) // 60)
        end_min = (start_min + 15) % 60
        # First 5 are checked in
        status = 'checked_in' if i < 5 else 'scheduled'
        apt = Appointment(
            user_id=u.user_id, service_id=s.service_id, location_id=l.location_id,
            appointment_date=today, time_window_start=time(start_hour, start_min), time_window_end=time(end_hour, end_min),
            status=status
        )
        db.session.add(apt)
        if status == 'checked_in':
            today_normal_appointments.append(apt)

    # Yesterday (6)
    for i in range(10, 16):
        idx = i - 10
        u = normal_users[i]
        s = random.choice(services)
        l = random.choice(locations)
        start_hour = 14 + (idx // 4)
        start_min = (idx % 4) * 15
        end_hour = start_hour + ((start_min + 15) // 60)
        end_min = (start_min + 15) % 60
        apt = Appointment(
            user_id=u.user_id, service_id=s.service_id, location_id=l.location_id,
            appointment_date=yesterday, time_window_start=time(start_hour, start_min), time_window_end=time(end_hour, end_min),
            status='completed'
        )
        db.session.add(apt)

    # Last Week (15)
    for i in range(16, 31):
        u = normal_users[i]
        s = random.choice(services)
        l = random.choice(locations)
        apt_date = today - timedelta(days=random.randint(2, 7))
        apt = Appointment(
            user_id=u.user_id, service_id=s.service_id, location_id=l.location_id,
            appointment_date=apt_date, time_window_start=time(11, 0), time_window_end=time(11, 30),
            status='completed'
        )
        db.session.add(apt)

    # 2. Seed 8 Elder Appointments (Today)
    print("Seeding elder appointments...")
    today_elder_appointments = []
    for i in range(8):
        u = elder_users[i]
        s = random.choice(services)
        l = random.choice(locations)
        # First 3 are checked in
        status = 'checked_in' if i < 3 else 'scheduled'
        apt = Appointment(
            user_id=u.user_id, service_id=s.service_id, location_id=l.location_id,
            appointment_date=today, time_window_start=time(9, i*7), time_window_end=time(9, (i+1)*7),
            status=status
        )
        db.session.add(apt)
        if status == 'checked_in':
            today_elder_appointments.append(apt)

    db.session.commit() # Commit to get app_ids

    # 3. Seed 8 Elder People in Active Queue
    print("Seeding active elder queue...")
    for i in range(8):
        apt = today_elder_appointments[i] if i < len(today_elder_appointments) else None
        u = elder_users[i+5] if i+5 < len(elder_users) else elder_users[i]
        s = random.choice(services)
        l = random.choice(locations)
        entry = QueueElder(
            user_id=u.user_id, service_id=s.service_id, location_id=l.location_id,
            app_id=apt.app_id if apt else None,
            token=f"{s.service_code}{random.randint(100,200)}", status='waiting',
            check_in_time=datetime.utcnow() - timedelta(minutes=random.randint(5, 30)),
            priority_score=15
        )
        db.session.add(entry)

    # 4. Seed some Completed people for Today (SLA calculation)
    print("Seeding completed entries for today...")
    for i in range(10):
        u = normal_users[i+10] if i+10 < len(normal_users) else normal_users[i]
        s = random.choice(services)
        l = random.choice(locations)
        # 70% within SLA (5-14 mins), 30% outside (20-40 mins)
        within_sla = random.random() < 0.7
        wait_mins = random.randint(5, 14) if within_sla else random.randint(20, 40)
        
        check_in = datetime.utcnow() - timedelta(minutes=wait_mins + 15)
        called = check_in + timedelta(minutes=wait_mins)
        served = called + timedelta(minutes=10)
        
        entry = QueueNormal(
            user_id=u.user_id, service_id=s.service_id, location_id=l.location_id,
            token=f"{s.service_code}{random.randint(600,700)}", status='completed',
            check_in_time=check_in, called_time=called, served_time=served,
            served_flag=True, counter_number=random.randint(1, 5)
        )
        db.session.add(entry)

    # 5. Seed Active Normal Queue (Waiting)
    print("Seeding active normal queue (waiting)...")
    for i in range(10):
        # Use users from index 30 onwards
        u = normal_users[i+30] if i+30 < len(normal_users) else normal_users[i]
        s = random.choice(services)
        l = random.choice(locations)
        entry = QueueNormal(
            user_id=u.user_id, service_id=s.service_id, location_id=l.location_id,
            token=f"{s.service_code}{random.randint(800,900)}", status='waiting',
            check_in_time=datetime.utcnow() - timedelta(minutes=random.randint(5, 60))
        )
        db.session.add(entry)

    db.session.commit()
    print("Seeding completed successfully!")
