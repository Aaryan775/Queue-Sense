# =============================================
# QueueSense - Database Models
# =============================================
# This module defines all SQLAlchemy ORM models
# that map to the database tables for the
# QueueSense application.
# =============================================

from datetime import datetime  # For timestamp fields
from . import db  # Import SQLAlchemy instance from app

# =============================================
# MODEL 1: Service
# Purpose: Stores different service types
# (Hospital, Bank, Government, Railway)
# =============================================
class Service(db.Model):
    """
    Model representing a service type in the queue system.
    Each service can have multiple locations and queues.
    """
    __tablename__ = 'services'  # Database table name
    
    # Primary key - unique identifier for each service
    service_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Service name (e.g., 'Hospital', 'Bank')
    service_name = db.Column(db.String(100), nullable=False)
    
    # Short code for token generation (e.g., 'H', 'B')
    service_code = db.Column(db.String(10), nullable=False, unique=True)
    
    # Optional description of the service
    description = db.Column(db.Text, nullable=True)
    
    # Font Awesome icon class for UI display
    icon = db.Column(db.String(50), default='fa-building')
    
    # Priority weight for elderly users (default: 3)
    elder_weight = db.Column(db.Integer, default=3)
    
    # Priority weight for appointment holders (default: 2)
    appointment_weight = db.Column(db.Integer, default=2)
    
    # Priority weight per 10 minutes of waiting (default: 1)
    wait_time_weight = db.Column(db.Integer, default=1)
    
    # Default service window duration in minutes
    service_duration = db.Column(db.Integer, default=20)
    
    # Whether the service is currently active
    is_active = db.Column(db.Boolean, default=True)
    
    # Timestamp fields
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to locations (one service has many locations)
    locations = db.relationship('Location', backref='service', lazy='dynamic')
    
    def to_dict(self):
        """Convert model to dictionary for JSON serialization"""
        return {
            'service_id': self.service_id,
            'service_name': self.service_name,
            'service_code': self.service_code,
            'description': self.description,
            'icon': self.icon,
            'elder_weight': self.elder_weight,
            'appointment_weight': self.appointment_weight,
            'wait_time_weight': self.wait_time_weight,
            'service_duration': self.service_duration,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


# =============================================
# MODEL 2: Location
# Purpose: Stores multiple locations per service
# =============================================
class Location(db.Model):
    """
    Model representing a physical location where
    a service is provided (e.g., Main Branch, City Clinic).
    """
    __tablename__ = 'locations'
    
    # Primary key
    location_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Foreign key to services table
    service_id = db.Column(db.Integer, db.ForeignKey('services.service_id'), nullable=False)
    
    # Name of the location
    location_name = db.Column(db.String(100), nullable=False)
    
    # Physical address
    address = db.Column(db.String(255), nullable=True)
    
    # Operating hours (stored as TIME)
    operating_hours_start = db.Column(db.Time, default=datetime.strptime('09:00', '%H:%M').time())
    operating_hours_end = db.Column(db.Time, default=datetime.strptime('17:00', '%H:%M').time())
    
    # Maximum queue capacity
    max_capacity = db.Column(db.Integer, default=50)
    
    # Whether location is active
    is_active = db.Column(db.Boolean, default=True)
    
    # Timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """Convert model to dictionary for JSON serialization"""
        return {
            'location_id': self.location_id,
            'service_id': self.service_id,
            'location_name': self.location_name,
            'address': self.address,
            'operating_hours_start': str(self.operating_hours_start) if self.operating_hours_start else None,
            'operating_hours_end': str(self.operating_hours_end) if self.operating_hours_end else None,
            'max_capacity': self.max_capacity,
            'is_active': self.is_active
        }


# =============================================
# MODEL 3: User
# Purpose: Stores registered users
# =============================================
class User(db.Model):
    """
    Model representing a user in the system.
    Users can be regular users, staff, or admin.
    """
    __tablename__ = 'users'
    
    # Primary key
    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Username for login (unique, required)
    username = db.Column(db.String(50), nullable=False, unique=True)
    
    # Bcrypt hashed password
    password_hash = db.Column(db.String(255), nullable=False)
    
    # Display name
    name = db.Column(db.String(100), nullable=False)
    
    # Phone number for notifications
    phone = db.Column(db.String(20), nullable=True)
    
    # Age for elder priority detection
    age = db.Column(db.Integer, nullable=True)
    
    # User category (normal or elder)
    category = db.Column(db.String(20), default='normal')
    
    # User gender
    gender = db.Column(db.String(20), nullable=True)
    
    # User role (user, staff, or admin)
    role = db.Column(db.String(20), default='user')
    
    # Whether account is active
    is_active = db.Column(db.Boolean, default=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Convert model to dictionary (excluding password)"""
        return {
            'user_id': self.user_id,
            'username': self.username,
            'name': self.name,
            'phone': self.phone,
            'age': self.age,
            'category': self.category,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


# =============================================
# MODEL 4: Staff
# Purpose: Staff members who manage queues
# =============================================
class Staff(db.Model):
    """
    Model representing staff members who manage
    queues and assist users at service locations.
    """
    __tablename__ = 'staff'
    
    # Primary key
    staff_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Foreign key to users table
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False, unique=True)
    
    # JSON array of service_ids this staff can manage
    assigned_services = db.Column(db.JSON, nullable=True)
    
    # Assigned counter/window number
    counter_number = db.Column(db.Integer, nullable=True)
    
    # Whether staff is currently available
    is_available = db.Column(db.Boolean, default=True)
    
    # Timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to user
    user = db.relationship('User', backref='staff_info')
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'staff_id': self.staff_id,
            'user_id': self.user_id,
            'user': self.user.to_dict() if self.user else None,
            'assigned_services': self.assigned_services,
            'counter_number': self.counter_number,
            'is_available': self.is_available
        }


# =============================================
# MODEL 5: Appointment
# Purpose: Stores booking records with time windows
# =============================================
class Appointment(db.Model):
    """
    Model representing an appointment booking.
    Uses service windows instead of fixed time slots.
    """
    __tablename__ = 'appointments'
    
    # Primary key
    app_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('services.service_id'), nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey('locations.location_id'), nullable=False)
    
    # Appointment date
    appointment_date = db.Column(db.Date, nullable=False)
    
    # Service window (start and end time)
    time_window_start = db.Column(db.Time, nullable=False)
    time_window_end = db.Column(db.Time, nullable=False)
    
    # Appointment status
    status = db.Column(db.String(20), default='scheduled')
    
    # Optional notes
    notes = db.Column(db.Text, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='appointments')
    service = db.relationship('Service', backref='appointments')
    location = db.relationship('Location', backref='appointments')
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'app_id': self.app_id,
            'appointment_id': self.app_id, # Frontend convenience
            'user_id': self.user_id,
            'user_name': self.user.name if self.user else 'Walk-in User',
            'service_id': self.service_id,
            'service_name': self.service.service_name if self.service else 'General',
            'location_id': self.location_id,
            'location_name': self.location.location_name if self.location else 'Main Center',
            'appointment_date': str(self.appointment_date) if self.appointment_date else None,
            'time_window_start': str(self.time_window_start) if self.time_window_start else None,
            'time_window_end': str(self.time_window_end) if self.time_window_end else None,
            'time_slot': f"{self.time_window_start.strftime('%H:%M')} - {self.time_window_end.strftime('%H:%M')}" if self.time_window_start else '09:00',
            'status': self.status,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


# =============================================
# MODEL 6: QueueElder
# Purpose: Priority queue for elderly users
# =============================================
class QueueElder(db.Model):
    """
    Model representing queue entries for elderly users.
    Elder queues have priority over normal queues.
    """
    __tablename__ = 'queue_elder'
    
    # Primary key
    queue_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Optional link to appointment
    app_id = db.Column(db.Integer, db.ForeignKey('appointments.app_id'), nullable=True)
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('services.service_id'), nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey('locations.location_id'), nullable=False)
    
    # Queue token (e.g., H001)
    token = db.Column(db.String(20), nullable=False)
    
    # Calculated priority score
    priority_score = db.Column(db.Integer, default=0)
    
    # Timestamps for tracking
    check_in_time = db.Column(db.DateTime, default=datetime.utcnow)
    called_time = db.Column(db.DateTime, nullable=True)
    served_time = db.Column(db.DateTime, nullable=True)
    
    # Status flags
    served_flag = db.Column(db.Boolean, default=False)
    is_emergency = db.Column(db.Boolean, default=False)
    
    # Assigned counter when called
    counter_number = db.Column(db.Integer, nullable=True)
    
    # Queue status
    status = db.Column(db.String(20), default='waiting')
    
    # Relationships
    user = db.relationship('User', backref='elder_queue_entries')
    service = db.relationship('Service', backref='elder_queue_entries')
    location = db.relationship('Location', backref='elder_queue_entries')
    appointment = db.relationship('Appointment', backref='elder_queue_entry')
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'queue_id': self.queue_id,
            'queue_type': 'elder',
            'app_id': self.app_id,
            'user_id': self.user_id,
            'user': self.user.to_dict() if self.user else None,
            'user_name': self.user.name if self.user else 'Walk-in',
            'service_id': self.service_id,
            'service_name': self.service.service_name if self.service else 'General',
            'location_id': self.location_id,
            'token': self.token,
            'priority_score': self.priority_score,
            'check_in_time': self.check_in_time.isoformat() if self.check_in_time else None,
            'called_time': self.called_time.isoformat() if self.called_time else None,
            'served_time': self.served_time.isoformat() if self.served_time else None,
            'served_flag': self.served_flag,
            'is_emergency': self.is_emergency,
            'counter_number': self.counter_number,
            'status': self.status
        }


# =============================================
# MODEL 7: QueueNormal
# Purpose: FIFO queue for normal users
# =============================================
class QueueNormal(db.Model):
    """
    Model representing queue entries for normal users.
    Uses FIFO (First In, First Out) ordering.
    """
    __tablename__ = 'queue_normal'
    
    # Primary key
    queue_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Optional link to appointment
    app_id = db.Column(db.Integer, db.ForeignKey('appointments.app_id'), nullable=True)
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('services.service_id'), nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey('locations.location_id'), nullable=False)
    
    # Queue token (e.g., B042)
    token = db.Column(db.String(20), nullable=False)
    
    # Calculated priority score
    priority_score = db.Column(db.Integer, default=0)
    
    # Timestamps for tracking
    check_in_time = db.Column(db.DateTime, default=datetime.utcnow)
    called_time = db.Column(db.DateTime, nullable=True)
    served_time = db.Column(db.DateTime, nullable=True)
    
    # Status flags
    served_flag = db.Column(db.Boolean, default=False)
    is_emergency = db.Column(db.Boolean, default=False)
    
    # Assigned counter when called
    counter_number = db.Column(db.Integer, nullable=True)
    
    # Queue status
    status = db.Column(db.String(20), default='waiting')
    
    # Relationships
    user = db.relationship('User', backref='normal_queue_entries')
    service = db.relationship('Service', backref='normal_queue_entries')
    location = db.relationship('Location', backref='normal_queue_entries')
    appointment = db.relationship('Appointment', backref='normal_queue_entry')
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'queue_id': self.queue_id,
            'queue_type': 'normal',
            'app_id': self.app_id,
            'user_id': self.user_id,
            'user': self.user.to_dict() if self.user else None,
            'user_name': self.user.name if self.user else 'Walk-in',
            'service_id': self.service_id,
            'service_name': self.service.service_name if self.service else 'General',
            'location_id': self.location_id,
            'token': self.token,
            'priority_score': self.priority_score,
            'check_in_time': self.check_in_time.isoformat() if self.check_in_time else None,
            'called_time': self.called_time.isoformat() if self.called_time else None,
            'served_time': self.served_time.isoformat() if self.served_time else None,
            'served_flag': self.served_flag,
            'is_emergency': self.is_emergency,
            'counter_number': self.counter_number,
            'status': self.status
        }


# =============================================
# MODEL 8: Analytics
# Purpose: Aggregated metrics for reporting
# =============================================
class Analytics(db.Model):
    """
    Model for storing daily analytics and metrics
    for each service and location.
    """
    __tablename__ = 'analytics'
    
    # Primary key
    analytics_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Foreign keys
    service_id = db.Column(db.Integer, db.ForeignKey('services.service_id'), nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey('locations.location_id'), nullable=False)
    
    # Date of analytics
    date = db.Column(db.Date, nullable=False)
    
    # Metrics
    total_users_served = db.Column(db.Integer, default=0)
    total_elder_served = db.Column(db.Integer, default=0)
    total_normal_served = db.Column(db.Integer, default=0)
    total_emergency = db.Column(db.Integer, default=0)
    avg_wait_time_minutes = db.Column(db.Float, default=0)
    avg_service_time_minutes = db.Column(db.Float, default=0)
    peak_hour = db.Column(db.Integer, nullable=True)
    no_shows = db.Column(db.Integer, default=0)
    
    # Timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    service = db.relationship('Service', backref='analytics')
    location = db.relationship('Location', backref='analytics')
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'analytics_id': self.analytics_id,
            'service_id': self.service_id,
            'location_id': self.location_id,
            'date': str(self.date) if self.date else None,
            'total_users_served': self.total_users_served,
            'total_elder_served': self.total_elder_served,
            'total_normal_served': self.total_normal_served,
            'total_emergency': self.total_emergency,
            'avg_wait_time_minutes': self.avg_wait_time_minutes,
            'avg_service_time_minutes': self.avg_service_time_minutes,
            'peak_hour': self.peak_hour,
            'no_shows': self.no_shows
        }


# =============================================
# MODEL 9: SystemSettings
# Purpose: Global system configuration
# =============================================
class SystemSettings(db.Model):
    """
    Model for storing global system settings
    that can be configured by admin.
    """
    __tablename__ = 'system_settings'
    
    # Primary key
    setting_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Setting key (unique identifier)
    setting_key = db.Column(db.String(50), nullable=False, unique=True)
    
    # Setting value
    setting_value = db.Column(db.Text, nullable=True)
    
    # Description of the setting
    description = db.Column(db.String(255), nullable=True)
    
    # Timestamp
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'setting_id': self.setting_id,
            'setting_key': self.setting_key,
            'setting_value': self.setting_value,
            'description': self.description
        }
