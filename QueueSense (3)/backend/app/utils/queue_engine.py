# =============================================
# QueueSense - Queue Engine
# =============================================
# This module contains the core queue management
# logic including priority scoring, token generation,
# and queue operations.
# =============================================

from datetime import datetime, timedelta  # For time calculations
from sqlalchemy import func  # For database aggregate functions

# Import database and models
from .. import db
from ..models import (
    Service, Location, User, QueueElder, QueueNormal, 
    Appointment, Analytics
)


class QueueEngine:
    """
    Core queue management engine that handles:
    - Priority score calculation
    - Token generation
    - Queue joining and management
    - Next token selection using weighted priority
    """
    
    # =============================================
    # Priority Score Calculation
    # =============================================
    
    @staticmethod
    def calculate_priority_score(user, service, has_appointment=False, check_in_time=None):
        """
        Calculate the priority score for a user in the queue.
        
        Priority Score = (is_elder * elder_weight) + 
                        (has_appointment * appointment_weight) + 
                        (wait_minutes // 10 * wait_time_weight)
        
        Args:
            user: User object
            service: Service object containing weight configurations
            has_appointment: Boolean indicating if user has an appointment
            check_in_time: DateTime when user joined the queue
            
        Returns:
            int: Calculated priority score
        """
        score = 0  # Initialize score
        
        # =============================================
        # Elder Weight Component
        # =============================================
        # Add elder weight if user is classified as elder
        if user.category == 'elder':
            score += service.elder_weight  # Default: 3 points
        
        # =============================================
        # Appointment Weight Component
        # =============================================
        # Add appointment weight if user has a valid appointment
        if has_appointment:
            score += service.appointment_weight  # Default: 2 points
        
        # =============================================
        # Wait Time Weight Component
        # =============================================
        # Add wait time weight based on how long user has been waiting
        if check_in_time:
            # Calculate minutes since check-in
            wait_duration = datetime.utcnow() - check_in_time
            wait_minutes = wait_duration.total_seconds() / 60  # Convert to minutes
            
            # Add 1 point for every 10 minutes of waiting
            score += int(wait_minutes // 10) * service.wait_time_weight
        
        return score
    
    # =============================================
    # Token Generation
    # =============================================
    
    @staticmethod
    def generate_token(service_id, location_id, target_date=None):
        """
        Generate a unique queue token for a service.
        
        Token format: {ServiceCode}{Number}
        Example: H001 for Hospital, B042 for Bank
        
        Args:
            service_id: ID of the service
            location_id: ID of the location
            target_date: Date for which to generate the token (defaults to today)
            
        Returns:
            str: Generated token (e.g., 'H001')
        """
        # Fetch the service to get service code
        service = Service.query.get(service_id)
        
        if not service:
            return None  # Service not found
        
        # Use target_date or default to today's date for daily token reset
        if target_date is None:
            target_date = datetime.utcnow().date()
        elif isinstance(target_date, str):
            target_date = datetime.strptime(target_date, '%Y-%m-%d').date()
        
        # =============================================
        # Count Tokens for Target Date/Service/Location
        # =============================================
        
        # Count elder queue entries for target date
        elder_count = QueueElder.query.filter(
            QueueElder.service_id == service_id,
            QueueElder.location_id == location_id,
            func.date(QueueElder.check_in_time) == target_date
        ).count()
        
        # Count normal queue entries for target date
        normal_count = QueueNormal.query.filter(
            QueueNormal.service_id == service_id,
            QueueNormal.location_id == location_id,
            func.date(QueueNormal.check_in_time) == target_date
        ).count()
        
        # Total tokens issued for that day
        total_tokens = elder_count + normal_count
        
        # Next token number (1-indexed)
        next_number = total_tokens + 1
        
        # Format token: ServiceCode + 3-digit number (e.g., H001)
        token = f"{service.service_code}{next_number:03d}"
        
        return token
    
    # =============================================
    # Join Queue
    # =============================================
    
    @staticmethod
    def join_queue(user_id, service_id, location_id, appointment_id=None, is_emergency=False):
        """
        Add a user to the appropriate queue (elder or normal).
        
        Args:
            user_id: ID of the user joining the queue
            service_id: ID of the service
            location_id: ID of the location
            appointment_id: Optional appointment ID
            is_emergency: Boolean for emergency priority
            
        Returns:
            dict: Queue entry details including token
        """
        print(f"[DEBUG] QueueEngine.join_queue: user_id={user_id}, service_id={service_id}, location_id={location_id}")
        # Fetch user and service with explicit filters
        user = db.session.query(User).filter_by(user_id=user_id).first()
        service = db.session.query(Service).filter_by(service_id=service_id).first()
        location = db.session.query(Location).filter_by(location_id=location_id).first()
        
        # Validate inputs
        if not user:
            return {'error': f'User {user_id} not found'}
        if not service or not service.is_active:
            return {'error': f'Service {service_id} not found or inactive'}
        if not location or not location.is_active:
            return {'error': f'Location {location_id} not found or inactive'}
        
        # Check if user has an appointment
        has_appointment = appointment_id is not None
        
        # Generate token
        token = QueueEngine.generate_token(service_id, location_id)
        
        # Calculate initial priority score
        priority_score = QueueEngine.calculate_priority_score(
            user, service, has_appointment, datetime.utcnow()
        )
        
        # Emergency cases get maximum priority
        if is_emergency:
            priority_score = 999  # Very high score for emergency
        
        # =============================================
        # Create Queue Entry Based on User Category
        # =============================================
        
        if user.category == 'elder':
            # Create elder queue entry
            queue_entry = QueueElder(
                user_id=user_id,
                service_id=service_id,
                location_id=location_id,
                app_id=appointment_id,
                token=token,
                priority_score=priority_score,
                is_emergency=is_emergency,
                status='waiting'
            )
        else:
            # Create normal queue entry
            queue_entry = QueueNormal(
                user_id=user_id,
                service_id=service_id,
                location_id=location_id,
                app_id=appointment_id,
                token=token,
                priority_score=priority_score,
                is_emergency=is_emergency,
                status='waiting'
            )
        
        # Add to database and commit
        db.session.add(queue_entry)
        db.session.commit()
        
        # Calculate position in queue
        position = QueueEngine.get_queue_position(queue_entry)
        
        # Return queue entry details
        return {
            'success': True,
            'token': token,
            'queue_id': queue_entry.queue_id,
            'queue_type': 'elder' if user.category == 'elder' else 'normal',
            'priority_score': priority_score,
            'position': position,
            'estimated_wait': QueueEngine.estimate_wait_time(position, service)
        }
    
    # =============================================
    # Get Queue Position
    # =============================================
    
    @staticmethod
    def get_queue_position(queue_entry):
        """
        Calculate the current position of a queue entry.
        Takes into account both elder and normal queues.
        
        Args:
            queue_entry: QueueElder or QueueNormal object
            
        Returns:
            int: Position in queue (1 = next to be served)
        """
        service_id = queue_entry.service_id
        location_id = queue_entry.location_id
        user_score = queue_entry.priority_score
        check_in_time = queue_entry.check_in_time
        
        # =============================================
        # Count People Ahead (Higher priority or earlier check-in)
        # =============================================
        
        # Count elder entries ahead (with higher score or earlier time)
        elder_ahead = QueueElder.query.filter(
            QueueElder.service_id == service_id,
            QueueElder.location_id == location_id,
            QueueElder.status == 'waiting',
            db.or_(
                QueueElder.priority_score > user_score,
                db.and_(
                    QueueElder.priority_score == user_score,
                    QueueElder.check_in_time < check_in_time
                )
            )
        ).count()
        
        # Count normal entries ahead
        normal_ahead = QueueNormal.query.filter(
            QueueNormal.service_id == service_id,
            QueueNormal.location_id == location_id,
            QueueNormal.status == 'waiting',
            db.or_(
                QueueNormal.priority_score > user_score,
                db.and_(
                    QueueNormal.priority_score == user_score,
                    QueueNormal.check_in_time < check_in_time
                )
            )
        ).count()
        
        # Total people ahead (position is 1-indexed)
        position = elder_ahead + normal_ahead + 1
        
        return position
    
    # =============================================
    # Estimate Wait Time
    # =============================================
    
    @staticmethod
    def estimate_wait_time(position, service):
        """
        Estimate the wait time based on queue position.
        
        Args:
            position: Position in queue
            service: Service object with service_duration
            
        Returns:
            str: Estimated wait time (e.g., '15-20 minutes')
        """
        # Base calculation: position * service_duration
        avg_service_time = service.service_duration  # Default: 20 minutes
        
        # Calculate estimated wait
        min_wait = max(0, (position - 1)) * avg_service_time
        max_wait = min_wait + avg_service_time
        
        # Format the estimate
        if min_wait == 0:
            return 'You are next!'
        elif min_wait < 60:
            return f'{min_wait}-{max_wait} minutes'
        else:
            hours = min_wait // 60
            remaining_mins = min_wait % 60
            return f'{hours}h {remaining_mins}m - {max_wait // 60}h {max_wait % 60}m'
    
    # =============================================
    # Get Next in Queue
    # =============================================
    
    # Track serve distribution to prevent starvation
    _serve_counts = {} # {(service_id, location_id): elder_consecutive_count}

    @staticmethod
    def get_next_in_queue(service_id=None, location_id=None, sector=None):
        """
        Get the next person to be served based on fair priority logic.
        Policy: 2 Elders for every 1 Normal user if both waiting.
        If service_id/location_id are None/0, check ALL queues.
        """
        # Update priority scores for all waiting entries
        # If specific service, only update for that service (optimization)
        QueueEngine.update_all_priorities(service_id, location_id)
        
        # Build Base Queries
        e_query = QueueElder.query.filter(QueueElder.status == 'waiting')
        n_query = QueueNormal.query.filter(QueueNormal.status == 'waiting')
        
        # Apply filters if provided
        if service_id and service_id != 0:
            e_query = e_query.filter(QueueElder.service_id == service_id)
            n_query = n_query.filter(QueueNormal.service_id == service_id)
            
        if location_id and location_id != 0:
            e_query = e_query.filter(QueueElder.location_id == location_id)
            n_query = n_query.filter(QueueNormal.location_id == location_id)

        # Ported Sector Logic (No DB change strategy - prefix based)
        if sector:
            sector_prefixes = {
                'hospital': 'H',
                'bank': 'B',
                'government': 'G',
                'restaurant': 'R',
                'transport': 'T',
                'service': 'S'
            }
            prefix = sector_prefixes.get(sector.lower())
            if prefix:
                e_query = e_query.join(Service).filter(Service.service_code.like(f'{prefix}%'))
                n_query = n_query.join(Service).filter(Service.service_code.like(f'{prefix}%'))
        
        # Get highest priority elder entry
        next_elder = e_query.order_by(
            QueueElder.is_emergency.desc(),
            QueueElder.priority_score.desc(),
            QueueElder.check_in_time.asc()
        ).first()
        
        # Get highest priority normal entry
        next_normal = n_query.order_by(
            QueueNormal.is_emergency.desc(),
            QueueNormal.priority_score.desc(),
            QueueNormal.check_in_time.asc()
        ).first()
        
        # Handle cases where only one queue has entries
        if not next_elder and not next_normal: 
            return None
        if not next_elder: 
            return {'entry': next_normal, 'queue_type': 'normal'}
        if not next_normal: 
            return {'entry': next_elder, 'queue_type': 'elder'}
        
        # Priority logic: Emergency always first
        if next_elder.is_emergency and not next_normal.is_emergency:
            return {'entry': next_elder, 'queue_type': 'elder'}
        if next_normal.is_emergency and not next_elder.is_emergency:
            return {'entry': next_normal, 'queue_type': 'normal'}
            
        # =============================================
        # Fair Distribution Logic
        # =============================================
        # Policy: 2 Elders for every 1 Normal user by default.
        # BUT if Normal priority score is significantly higher, serve Normal.
        # Threshold: If Normal Score > Elder Score + 5, normal jumps.
        # This keeps it "Fair" as requested by user.
        
        if next_normal.priority_score > (next_elder.priority_score + 5):
            return {'entry': next_normal, 'queue_type': 'normal'}
            
        # Otherwise, follow the 2:1 ratio for balanced throughput
        key = (service_id, location_id)
        count = QueueEngine._serve_counts.get(key, 0)
        
        if count < 2:
            QueueEngine._serve_counts[key] = count + 1
            return {'entry': next_elder, 'queue_type': 'elder'}
        else:
            QueueEngine._serve_counts[key] = 0 # Reset
            return {'entry': next_normal, 'queue_type': 'normal'}
    
    # =============================================
    # Call Next Token
    # =============================================
    
    @staticmethod
    def call_next(service_id, location_id, counter_number, sector=None):
        """
        Call the next person in queue.
        Updates their status to 'called'.
        
        Args:
            service_id: ID of the service
            location_id: ID of the location
            counter_number: Counter/window number calling
            sector: Optional sector filter (extracted from staff role/config)
            
        Returns:
            dict: Called entry details or None if queue empty
        """
        # Get next in queue
        # Support universal calling (None or 0)
        if service_id == 0: service_id = None
        if location_id == 0: location_id = None
        
        result = QueueEngine.get_next_in_queue(service_id, location_id, sector=sector)
        
        if not result:
            return {'error': 'Queue is empty'}
        
        entry = result['entry']
        queue_type = result['queue_type']
        
        # Update entry status
        entry.status = 'called'
        entry.called_time = datetime.utcnow()
        entry.counter_number = counter_number
        
        db.session.commit()
        
        return {
            'success': True,
            'token': entry.token,
            'queue_type': queue_type,
            'user_name': entry.user.name,
            'counter_number': counter_number,
            'queue_id': entry.queue_id
        }
    
    # =============================================
    # Call Specific Token (Manual Override)
    # =============================================
    
    @staticmethod
    def call_specific(queue_id, queue_type, counter_number):
        """
        Call a specific person in the queue, bypassing priority.
        Used when staff clicks 'Serve' on a specific row.
        
        Args:
            queue_id: ID of the queue entry
            queue_type: 'elder' or 'normal'
            counter_number: Counter/window calling
            
        Returns:
            dict: Called entry details or error
        """
        # Get the appropriate queue entry
        if queue_type == 'elder':
            entry = QueueElder.query.get(queue_id)
        elif queue_type == 'normal':
            entry = QueueNormal.query.get(queue_id)
        else:
            return {'error': 'Invalid queue type'}
        
        if not entry:
            return {'error': 'Queue entry not found'}
            
        if entry.status != 'waiting':
            return {'error': f'Entry is not waiting (Status: {entry.status})'}
        
        # Update status
        entry.status = 'called'
        entry.called_time = datetime.utcnow()
        entry.counter_number = counter_number
        
        db.session.commit()
        
        return {
            'success': True,
            'token': entry.token,
            'queue_type': queue_type,
            'user_name': entry.user.name,
            'counter_number': counter_number,
            'queue_id': entry.queue_id
        }
    
    # =============================================
    # Mark as Served
    # =============================================
    
    @staticmethod
    def mark_served(queue_id, queue_type):
        """
        Mark a queue entry as served/completed.
        
        Args:
            queue_id: ID of the queue entry
            queue_type: 'elder' or 'normal'
            
        Returns:
            dict: Success message or error
        """
        # Get the appropriate queue entry
        if queue_type == 'elder':
            entry = QueueElder.query.get(queue_id)
        else:
            entry = QueueNormal.query.get(queue_id)
        
        if not entry:
            return {'error': 'Queue entry not found'}
        
        # Update status
        entry.status = 'completed'
        entry.served_flag = True
        entry.served_time = datetime.utcnow()
        
        # Sync appointment status if linked
        if entry.app_id:
            appointment = Appointment.query.get(entry.app_id)
            if appointment:
                appointment.status = 'completed'
        
        db.session.commit()
        
        # Update analytics
        QueueEngine.update_analytics(entry)
        
        return {'success': True, 'message': 'Customer marked as served'}
    
    # =============================================
    # Mark as No-Show
    # =============================================
    
    @staticmethod
    def mark_no_show(queue_id, queue_type):
        """
        Mark a queue entry as no-show.
        
        Args:
            queue_id: ID of the queue entry
            queue_type: 'elder' or 'normal'
            
        Returns:
            dict: Success message or error
        """
        # Get the appropriate queue entry
        if queue_type == 'elder':
            entry = QueueElder.query.get(queue_id)
        else:
            entry = QueueNormal.query.get(queue_id)
        
        if not entry:
            return {'error': 'Queue entry not found'}
        
        # Update status
        entry.status = 'no_show'
        entry.served_flag = False
        
        db.session.commit()
        
        return {'success': True, 'message': 'Customer marked as no-show'}
    
    # =============================================
    # Update All Priorities
    # =============================================
    
    @staticmethod
    def update_all_priorities(service_id, location_id):
        """
        Update priority scores for all waiting entries.
        Called before getting next in queue to ensure
        wait time bonuses are applied.
        
        Args:
            service_id: ID of the service (0 or None for all)
            location_id: ID of the location (0 or None for all)
        """
        # Cache services to avoid repeated lookups
        service_cache = {}

        # 1. Update elder queue priorities
        e_query = QueueElder.query.filter(QueueElder.status == 'waiting')
        if service_id and service_id != 0:
            e_query = e_query.filter(QueueElder.service_id == service_id)
        if location_id and location_id != 0:
            e_query = e_query.filter(QueueElder.location_id == location_id)
        
        for entry in e_query.all():
            if entry.service_id not in service_cache:
                service_cache[entry.service_id] = Service.query.get(entry.service_id)
            
            srv = service_cache.get(entry.service_id)
            if srv:
                entry.priority_score = QueueEngine.calculate_priority_score(
                    entry.user, srv, entry.app_id is not None, entry.check_in_time
                )
                if entry.is_emergency:
                    entry.priority_score = 999
        
        # 2. Update normal queue priorities
        n_query = QueueNormal.query.filter(QueueNormal.status == 'waiting')
        if service_id and service_id != 0:
            n_query = n_query.filter(QueueNormal.service_id == service_id)
        if location_id and location_id != 0:
            n_query = n_query.filter(QueueNormal.location_id == location_id)
        
        for entry in n_query.all():
            if entry.service_id not in service_cache:
                service_cache[entry.service_id] = Service.query.get(entry.service_id)
            
            srv = service_cache.get(entry.service_id)
            if srv:
                entry.priority_score = QueueEngine.calculate_priority_score(
                    entry.user, srv, entry.app_id is not None, entry.check_in_time
                )
                if entry.is_emergency:
                    entry.priority_score = 999
        
        db.session.commit()
    
    # =============================================
    # Update Analytics
    # =============================================
    
    @staticmethod
    def update_analytics(queue_entry):
        """
        Update daily analytics when a customer is served.
        
        Args:
            queue_entry: The completed queue entry
        """
        try:
            today = datetime.utcnow().date()
            
            # Find or create analytics record for today
            analytics = Analytics.query.filter_by(
                service_id=queue_entry.service_id,
                location_id=queue_entry.location_id,
                date=today
            ).first()
            
            if not analytics:
                analytics = Analytics(
                    service_id=queue_entry.service_id,
                    location_id=queue_entry.location_id,
                    date=today
                )
                db.session.add(analytics)
            
            # Update counts
            analytics.total_users_served += 1
            
            # Check if elder or normal
            if isinstance(queue_entry, QueueElder):
                analytics.total_elder_served += 1
            else:
                analytics.total_normal_served += 1
            
            # Check if emergency
            if queue_entry.is_emergency:
                analytics.total_emergency += 1
            
            # Calculate wait time for this customer
            if queue_entry.called_time and queue_entry.check_in_time:
                wait_minutes = (queue_entry.called_time - queue_entry.check_in_time).total_seconds() / 60
                
                # Update average (running average formula)
                n = analytics.total_users_served
                if n > 0:
                    old_avg = analytics.avg_wait_time_minutes or 0
                    analytics.avg_wait_time_minutes = ((old_avg * (n - 1)) + wait_minutes) / n
            
            # Track peak hour
            current_hour = datetime.utcnow().hour
            analytics.peak_hour = current_hour  # Simplified - would need hour counting logic
            
            db.session.commit()
            print(f"[DEBUG] Analytics updated for queue_id {queue_entry.queue_id}")
            
        except Exception as e:
            print(f"[ERROR] Failed to update analytics: {str(e)}")
            # Do not re-raise, allow the serve action to complete
            db.session.rollback()
    
    # =============================================
    # Get Queue Statistics
    # =============================================
    
    @staticmethod
    def get_queue_stats(service_id, location_id):
        """
        Get current queue statistics for a service/location.
        
        Args:
            service_id: ID of the service
            location_id: ID of the location
            
        Returns:
            dict: Queue statistics
        """
        # Count waiting in elder queue
        elder_waiting = QueueElder.query.filter(
            QueueElder.service_id == service_id,
            QueueElder.location_id == location_id,
            QueueElder.status == 'waiting'
        ).count()
        
        # Count waiting in normal queue
        normal_waiting = QueueNormal.query.filter(
            QueueNormal.service_id == service_id,
            QueueNormal.location_id == location_id,
            QueueNormal.status == 'waiting'
        ).count()
        
        # Count currently being served
        elder_serving = QueueElder.query.filter(
            QueueElder.service_id == service_id,
            QueueElder.location_id == location_id,
            QueueElder.status.in_(['called', 'serving'])
        ).count()
        
        normal_serving = QueueNormal.query.filter(
            QueueNormal.service_id == service_id,
            QueueNormal.location_id == location_id,
            QueueNormal.status.in_(['called', 'serving'])
        ).count()
        
        # Count served today
        today = datetime.utcnow().date()
        
        e_served_q = QueueElder.query.filter(
            QueueElder.status == 'completed',
            func.date(QueueElder.served_time) == today
        )
        if service_id and service_id != 0:
            e_served_q = e_served_q.filter(QueueElder.service_id == service_id)
        if location_id and location_id != 0:
            e_served_q = e_served_q.filter(QueueElder.location_id == location_id)
        elder_served = e_served_q.count()
        
        n_served_q = QueueNormal.query.filter(
            QueueNormal.status == 'completed',
            func.date(QueueNormal.served_time) == today
        )
        if service_id and service_id != 0:
            n_served_q = n_served_q.filter(QueueNormal.service_id == service_id)
        if location_id and location_id != 0:
            n_served_q = n_served_q.filter(QueueNormal.location_id == location_id)
        normal_served = n_served_q.count()
        
        # Get service info for wait time estimate
        service = Service.query.get(service_id)
        total_waiting = elder_waiting + normal_waiting
        
        return {
            'total_waiting': total_waiting,
            'elder_waiting': elder_waiting,
            'normal_waiting': normal_waiting,
            'currently_serving': elder_serving + normal_serving,
            'served_today': elder_served + normal_served,
            'estimated_wait': QueueEngine.estimate_wait_time(total_waiting + 1, service) if service else 'Unknown'
        }

    @staticmethod
    def generate_dummy_data(service_id, location_id, count_elder=5, count_normal=5, target_date=None):
        """
        Generate dummy queue entries for a specific date.
        """
        from ..models import User
        import random
        from datetime import time as dt_time
        
        if target_date is None:
            target_date = datetime.utcnow().date()
        elif isinstance(target_date, str):
            try:
                target_date = datetime.strptime(target_date, '%Y-%m-%d').date()
            except ValueError:
                target_date = datetime.utcnow().date()

        # Get some real users to assign to dummy entries
        users = User.query.filter_by(role='user').limit(50).all()
        if not users:
            return {'error': 'No users found in database to assign dummy data'}

        # Calculate a base time (e.g., 9:00 AM on target_date)
        base_datetime = datetime.combine(target_date, dt_time(9, 0))
        
        entries_created = 0
        
        # Generate Elders
        elders = [u for u in users if u.category == 'elder'] or users
        for i in range(count_elder):
            user = random.choice(elders)
            token = QueueEngine.generate_token(service_id, location_id, target_date)
            check_in = base_datetime + timedelta(minutes=random.randint(0, 480))
            
            entry = QueueElder(
                user_id=user.user_id,
                service_id=service_id,
                location_id=location_id,
                token=token,
                status='waiting',
                check_in_time=check_in,
                priority_score=random.randint(5, 15)
            )
            db.session.add(entry)
            entries_created += 1

        # Generate Normal
        normals = [u for u in users if u.category == 'normal'] or users
        for i in range(count_normal):
            user = random.choice(normals)
            token = QueueEngine.generate_token(service_id, location_id, target_date)
            check_in = base_datetime + timedelta(minutes=random.randint(0, 480))
            
            entry = QueueNormal(
                user_id=user.user_id,
                service_id=service_id,
                location_id=location_id,
                token=token,
                status='waiting',
                check_in_time=check_in,
                priority_score=random.randint(0, 10)
            )
            db.session.add(entry)
            entries_created += 1

        db.session.commit()
        return {'success': True, 'count': entries_created}

    @staticmethod
    def cancel_call(queue_id, queue_type):
        """
        Reset a 'called' entry back to 'waiting' and clear counter.
        """
        if queue_type == 'elder':
            entry = QueueElder.query.get(queue_id)
        else:
            entry = QueueNormal.query.get(queue_id)
            
        if not entry:
            return {'error': 'Entry not found'}
            
        entry.status = 'waiting'
        entry.counter_number = None
        entry.called_time = None
        
        db.session.commit()
        return {'success': True, 'message': 'Call cancelled and returned to queue'}
