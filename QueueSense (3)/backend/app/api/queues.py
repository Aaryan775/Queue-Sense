# =============================================
# QueueSense - Queue API Routes
# =============================================
# This module handles queue operations including
# joining, status updates, calling next, etc.
# =============================================

from flask import Blueprint, request, jsonify  # Flask utilities
from datetime import datetime, timedelta  # For timestamps

# Import database and models
from .. import db
from ..models import QueueElder, QueueNormal, Service, Location, User, Appointment
from ..utils.decorators import token_required, staff_required
from ..utils.queue_engine import QueueEngine

# =============================================
# Create Queues Blueprint
# =============================================
queues_bp = Blueprint('queues', __name__)


# =============================================
# ROUTE: Join Queue
# POST /api/queues/join
# =============================================
@queues_bp.route('/join', methods=['POST'])
@token_required
def join_queue(current_user):
    """
    Join a queue for a specific service and location.
    
    Request Body (JSON):
        - service_id: ID of the service (required)
        - location_id: ID of the location (required)
        - appointment_id: Optional appointment ID
        - is_emergency: Boolean for emergency cases
    
    Returns:
        - 201: Successfully joined queue with token
        - 400: Validation error
    """
    data = request.get_json()
    
    # Validate required fields
    if not data.get('service_id'):
        return jsonify({
            'error': 'Service ID is required'
        }), 400
    
    if not data.get('location_id'):
        return jsonify({
            'error': 'Location ID is required'
        }), 400
    
    # Call queue engine to join queue
    result = QueueEngine.join_queue(
        user_id=current_user.user_id,
        service_id=data['service_id'],
        location_id=data['location_id'],
        appointment_id=data.get('appointment_id'),
        is_emergency=data.get('is_emergency', False)
    )
    
    # Check for errors
    if result.get('error'):
        return jsonify(result), 400
    
    return jsonify(result), 201


# =============================================
# ROUTE: Add Elder to Queue (Staff Only)
# POST /api/queues/add-elder
# =============================================
@queues_bp.route('/add-elder', methods=['POST'])
@token_required
@staff_required
def add_elder_to_queue(current_user):
    data = request.get_json()
    print(f"[DEBUG] add_elder_to_queue received data: {data}")
    
    # Ensure IDs are integers
    try:
        data['service_id'] = int(data['service_id'])
        data['location_id'] = int(data['location_id'])
    except (ValueError, TypeError, KeyError):
        return jsonify({'error': 'Invalid service or location ID format'}), 400

    # Validate required fields
    if not data.get('name'):
        return jsonify({
            'error': 'Elder name is required'
        }), 400
    
    if not data.get('service_id') or not data.get('location_id'):
        return jsonify({
            'error': 'Service ID and Location ID are required'
        }), 400
    
    # Create a temporary user entry for the elder
    # Or find existing user by phone
    elder_user = None
    
    if data.get('phone'):
        elder_user = User.query.filter_by(phone=data['phone']).first()
    
    if not elder_user:
        # Validate age
        age = data.get('age')
        if age is not None:
            try:
                age = int(age)
                if age < 60 or age > 120:
                    return jsonify({'error': 'Age must be between 60 and 120'}), 400
            except ValueError:
                return jsonify({'error': 'Invalid age format'}), 400
        else:
            return jsonify({'error': 'Age is required'}), 400

        # Create walk-in elder user
        elder_user = User(
            username=f"walkin_{datetime.utcnow().timestamp()}@queuesense.local",
            password_hash='walk-in-user',  # Not for login
            name=data['name'],
            phone=data.get('phone'),
            age=age,
            gender=data.get('gender'),
            category='elder',
            role='user',
            is_active=True
        )
        db.session.add(elder_user)
        db.session.flush() # Get ID without full commit yet
    
    # Handle Appointment Creation (Atomic with Queue joining)
    appointment_id = None
    if data.get('appointment_date') and data.get('time_window_start'):
        try:
            from datetime import datetime as dt_class # Avoid naming conflict
            apt_date = dt_class.strptime(data['appointment_date'], '%Y-%m-%d').date()
            win_start = dt_class.strptime(data['time_window_start'], '%H:%M').time()
            
            service = db.session.query(Service).filter_by(service_id=data['service_id']).first()
            if service:
                start_dt = dt_class.combine(apt_date, win_start)
                end_dt = start_dt + timedelta(minutes=service.service_duration)
                
                # Check availability - MAX 1 per slot (Exclusive booking as per v4)
                existing_count = Appointment.query.filter(
                    Appointment.service_id == data['service_id'],
                    Appointment.location_id == data['location_id'],
                    Appointment.appointment_date == apt_date,
                    Appointment.time_window_start == win_start,
                    Appointment.status.in_(['scheduled', 'checked_in'])
                ).count()

                if existing_count >= 1:
                    return jsonify({
                        'error': 'This time slot is already booked',
                        'message': 'Please choose a different time'
                    }), 400

                new_apt = Appointment(
                    user_id=elder_user.user_id,
                    service_id=data['service_id'],
                    location_id=data['location_id'],
                    appointment_date=apt_date,
                    time_window_start=win_start,
                    time_window_end=end_dt.time(),
                    notes=data.get('notes', 'Staff Assisted Walk-in'),
                    status='checked_in' # Direct check-in for walk-ins
                )
                db.session.add(new_apt)
                db.session.flush()
                appointment_id = new_apt.app_id
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': 'Invalid appointment data', 'details': str(e)}), 400

    # Add to queue using queue engine
    result = QueueEngine.join_queue(
        user_id=elder_user.user_id,
        service_id=data['service_id'],
        location_id=data['location_id'],
        appointment_id=appointment_id,
        is_emergency=data.get('is_emergency', False)
    )
    print(f"[DEBUG] QueueEngine result: {result}")
    
    if result.get('error'):
        db.session.rollback()
        return jsonify(result), 400
    
    db.session.commit()
    
    # Add elder name to response
    result['elder_name'] = data['name']
    
    return jsonify(result), 201


# =============================================
# ROUTE: Get Queue Status
# GET /api/queues/status/<service_id>/<location_id>
# =============================================
@queues_bp.route('/status/<int:service_id>/<int:location_id>', methods=['GET'])
def get_queue_status(service_id, location_id):
    """
    Get real-time queue status for a service/location.
    Use 0 for service_id or location_id to get ALL.
    """
    sector = request.args.get('sector')
    
    # Build query for elder waitings
    elder_q = QueueElder.query.filter(QueueElder.status == 'waiting')
    
    # Sector filtering (No DB change strategy - prefix based)
    if sector:
        sector_prefixes = {'hospital': 'H', 'bank': 'B', 'government': 'G', 'restaurant': 'R', 'transport': 'T', 'service': 'S'}
        prefix = sector_prefixes.get(sector.lower())
        if prefix:
            elder_q = elder_q.join(Service).filter(Service.service_code.like(f'{prefix}%'))

    if service_id > 0: elder_q = elder_q.filter(QueueElder.service_id == service_id)
    if location_id > 0: elder_q = elder_q.filter(QueueElder.location_id == location_id)
    
    # Build query for normal waitings
    normal_q = QueueNormal.query.filter(QueueNormal.status == 'waiting')
    if sector:
        prefix = sector_prefixes.get(sector.lower())
        if prefix:
            normal_q = normal_q.join(Service).filter(Service.service_code.like(f'{prefix}%'))

    if service_id > 0: normal_q = normal_q.filter(QueueNormal.service_id == service_id)
    if location_id > 0: normal_q = normal_q.filter(QueueNormal.location_id == location_id)
    
    # Calculate counts BEFORE limit
    elder_total = elder_q.count()
    normal_total = normal_q.count()
    
    # Get limited lists for display
    elder_waiting = elder_q.order_by(
        QueueElder.is_emergency.desc(), QueueElder.priority_score.desc(), QueueElder.check_in_time.asc()
    ).limit(20).all()
    
    normal_waiting = normal_q.order_by(
        QueueNormal.is_emergency.desc(), QueueNormal.priority_score.desc(), QueueNormal.check_in_time.asc()
    ).limit(20).all()
    
    # Serving logic
    e_serving_q = QueueElder.query.filter(QueueElder.status.in_(['called', 'serving']))
    n_serving_q = QueueNormal.query.filter(QueueNormal.status.in_(['called', 'serving']))

    if sector:
        prefix = sector_prefixes.get(sector.lower())
        if prefix:
            e_serving_q = e_serving_q.join(Service).filter(Service.service_code.like(f'{prefix}%'))
            n_serving_q = n_serving_q.join(Service).filter(Service.service_code.like(f'{prefix}%'))

    if service_id > 0: 
        e_serving_q = e_serving_q.filter(QueueElder.service_id == service_id)
        n_serving_q = n_serving_q.filter(QueueNormal.service_id == service_id)
    if location_id > 0: 
        e_serving_q = e_serving_q.filter(QueueElder.location_id == location_id)
        n_serving_q = n_serving_q.filter(QueueNormal.location_id == location_id)

    currently_serving = []
    for entry in e_serving_q.all():
        data = entry.to_dict()
        data['queue_type'] = 'elder' # Ensure explicit type
        currently_serving.append(data)
        
    for entry in n_serving_q.all():
        data = entry.to_dict()
        data['queue_type'] = 'normal' # Ensure explicit type
        currently_serving.append(data)
    
    # Statistics use TOTAL counts
    total_waiting = elder_total + normal_total
    
    return jsonify({
        'elder_queue': [e.to_dict() for e in elder_waiting],
        'normal_queue': [n.to_dict() for n in normal_waiting],
        'currently_serving': currently_serving,
        'total_waiting_count': total_waiting,
        'elder_waiting_count': elder_total,
        'normal_waiting_count': normal_total
    }), 200


# =============================================
# ROUTE: Get My Queue Position
# GET /api/queues/my-position
# =============================================
@queues_bp.route('/my-position', methods=['GET'])
@token_required
def get_my_position(current_user):
    """
    Get the current user's position in any active queues.
    
    Returns:
        - 200: User's queue positions
    """
    active_entries = []
    
    # Check elder queue
    elder_entries = QueueElder.query.filter(
        QueueElder.user_id == current_user.user_id,
        QueueElder.status.in_(['waiting', 'called'])
    ).all()
    
    for entry in elder_entries:
        position = QueueEngine.get_queue_position(entry)
        service = Service.query.get(entry.service_id)
        location = Location.query.get(entry.location_id)
        
        active_entries.append({
            'queue_type': 'elder',
            'queue_id': entry.queue_id,
            'token': entry.token,
            'position': position,
            'status': entry.status,
            'counter_number': entry.counter_number,
            'service_name': service.service_name if service else 'Unknown',
            'location_name': location.location_name if location else 'Unknown',
            'estimated_wait': QueueEngine.estimate_wait_time(position, service) if service else 'Unknown',
            'check_in_time': entry.check_in_time.isoformat() if entry.check_in_time else None
        })
    
    # Check normal queue
    normal_entries = QueueNormal.query.filter(
        QueueNormal.user_id == current_user.user_id,
        QueueNormal.status.in_(['waiting', 'called'])
    ).all()
    
    for entry in normal_entries:
        position = QueueEngine.get_queue_position(entry)
        service = Service.query.get(entry.service_id)
        location = Location.query.get(entry.location_id)
        
        active_entries.append({
            'queue_type': 'normal',
            'queue_id': entry.queue_id,
            'token': entry.token,
            'position': position,
            'status': entry.status,
            'counter_number': entry.counter_number,
            'service_name': service.service_name if service else 'Unknown',
            'location_name': location.location_name if location else 'Unknown',
            'estimated_wait': QueueEngine.estimate_wait_time(position, service) if service else 'Unknown',
            'check_in_time': entry.check_in_time.isoformat() if entry.check_in_time else None
        })
    
    return jsonify({
        'active_queues': active_entries
    }), 200


# =============================================
# ROUTE: Call Next Token (Staff Only)
# POST /api/queues/call-next
# =============================================
@queues_bp.route('/call-next', methods=['POST'])
@token_required
@staff_required
def call_next_token(current_user):
    """
    Call the next person in the queue.
    Uses weighted priority to determine next.
    
    Request Body (JSON):
        - service_id: Service ID (required)
        - location_id: Location ID (required)
        - counter_number: Counter calling (required)
    
    Returns:
        - 200: Next token called
        - 400: Queue empty or validation error
    """
    data = request.get_json()
    
    # Validate required fields
    if data.get('service_id') is None or data.get('location_id') is None:
        return jsonify({
            'error': 'Service ID and Location ID are required'
        }), 400
    
    if data.get('counter_number') is None:
        return jsonify({
            'error': 'Counter number is required'
        }), 400
    
    # Call next using queue engine
    result = QueueEngine.call_next(
        service_id=data['service_id'],
        location_id=data['location_id'],
        counter_number=data['counter_number'],
        sector=data.get('sector') # Pass sector
    )
    
    if result.get('error'):
        return jsonify(result), 400
    
    return jsonify(result), 200


# =============================================
# ROUTE: Call Specific Token (Staff Only)
# POST /api/queues/call-specific
# =============================================
@queues_bp.route('/call-specific', methods=['POST'])
@token_required
@staff_required
def call_specific_token(current_user):
    """
    Call a specific person in the queue.
    Used when clicking 'Serve' on a specific row.
    """
    data = request.get_json()
    
    # Validate required fields
    if not data.get('queue_id') or not data.get('queue_type'):
        return jsonify({
            'error': 'Queue ID and Queue Type are required'
        }), 400
    
    if data.get('counter_number') is None:
        return jsonify({
            'error': 'Counter number is required'
        }), 400
        
    # Call specific using queue engine
    result = QueueEngine.call_specific(
        queue_id=data['queue_id'],
        queue_type=data['queue_type'],
        counter_number=data['counter_number']
    )
    
    if result.get('error'):
        return jsonify(result), 400
    
    return jsonify(result), 200


# =============================================
# ROUTE: Mark as Served (Staff Only)
# POST /api/queues/serve/<queue_type>/<queue_id>
# =============================================
@queues_bp.route('/serve/<queue_type>/<int:queue_id>', methods=['POST'])
@token_required
@staff_required
def mark_served(current_user, queue_type, queue_id):
    """
    Mark a queue entry as served/completed.
    
    Returns:
        - 200: Marked as served
        - 400: Invalid queue type
        - 404: Queue entry not found
    """
    if queue_type not in ['elder', 'normal']:
        return jsonify({
            'error': 'Invalid queue type. Use "elder" or "normal"'
        }), 400
    
    result = QueueEngine.mark_served(queue_id, queue_type)
    
    if result.get('error'):
        return jsonify(result), 404
    
    return jsonify(result), 200


# =============================================
# ROUTE: Mark as No-Show (Staff Only)
# POST /api/queues/no-show/<queue_type>/<queue_id>
# =============================================
@queues_bp.route('/no-show/<queue_type>/<int:queue_id>', methods=['POST'])
@token_required
@staff_required
def mark_no_show(current_user, queue_type, queue_id):
    """
    Mark a queue entry as no-show.
    
    Returns:
        - 200: Marked as no-show
        - 400: Invalid queue type
        - 404: Queue entry not found
    """
    if queue_type not in ['elder', 'normal']:
        return jsonify({
            'error': 'Invalid queue type. Use "elder" or "normal"'
        }), 400
    
    result = QueueEngine.mark_no_show(queue_id, queue_type)
    
    if result.get('error'):
        return jsonify(result), 404
    
    return jsonify(result), 200


# =============================================
# ROUTE: Emergency Queue Insert (Staff Only)
# POST /api/queues/emergency
# =============================================
@queues_bp.route('/emergency', methods=['POST'])
@token_required
@staff_required
def add_emergency(current_user):
    """
    Add a user to the emergency queue (highest priority).
    
    Request Body (JSON):
        - name: Person's name (required)
        - phone: Phone number (optional)
        - service_id: Service ID (required)
        - location_id: Location ID (required)
    
    Returns:
        - 201: Emergency entry added
        - 400: Validation error
    """
    data = request.get_json()
    
    # Validate required fields
    if not data.get('name'):
        return jsonify({
            'error': 'Name is required'
        }), 400
    
    if not data.get('service_id') or not data.get('location_id'):
        return jsonify({
            'error': 'Service ID and Location ID are required'
        }), 400
    
    # Create emergency user entry
    emergency_user = User(
        username=f"emergency_{datetime.utcnow().timestamp()}@queuesense.local",
        password_hash='emergency-user',
        name=data['name'],
        phone=data.get('phone'),
        age=0,
        category='normal',
        role='user',
        is_active=True
    )
    db.session.add(emergency_user)
    db.session.commit()
    
    # Add to queue with emergency flag
    result = QueueEngine.join_queue(
        user_id=emergency_user.user_id,
        service_id=data['service_id'],
        location_id=data['location_id'],
        appointment_id=None,
        is_emergency=True  # Emergency flag
    )
    
    if result.get('error'):
        return jsonify(result), 400
    
    result['emergency'] = True
    result['person_name'] = data['name']
    
    return jsonify(result), 201


# =============================================
# ROUTE: Generate Dummy Data (Staff Only)
# POST /api/queues/generate-dummy
# =============================================
@queues_bp.route('/generate-dummy', methods=['POST'])
@token_required
@staff_required
def generate_dummy(current_user):
    data = request.get_json()
    sid = data.get('service_id', 1)
    lid = data.get('location_id', 1)
    count_e = data.get('count_elder', 5)
    count_n = data.get('count_normal', 5)
    date_str = data.get('date') # YYYY-MM-DD
    
    result = QueueEngine.generate_dummy_data(sid, lid, count_e, count_n, date_str)
    if result.get('error'):
        return jsonify(result), 400
    return jsonify(result), 200


# =============================================
# ROUTE: Cancel Call / Remove Serving (Staff Only)
# POST /api/queues/cancel-call/<queue_type>/<queue_id>
# =============================================
@queues_bp.route('/cancel-call/<queue_type>/<int:queue_id>', methods=['POST'])
@token_required
@staff_required
def cancel_call(current_user, queue_type, queue_id):
    if queue_type not in ['elder', 'normal']:
        return jsonify({'error': 'Invalid queue type'}), 400
    
    result = QueueEngine.cancel_call(queue_id, queue_type)
    if result.get('error'):
        return jsonify(result), 404
    return jsonify(result), 200


# =============================================
# ROUTE: Cancel Queue Entry
# DELETE /api/queues/cancel/<queue_type>/<queue_id>
# =============================================
@queues_bp.route('/cancel/<queue_type>/<int:queue_id>', methods=['DELETE'])
@token_required
def cancel_queue_entry(current_user, queue_type, queue_id):
    """
    Cancel a queue entry.
    Users can cancel their own entries, staff can cancel any.
    
    Returns:
        - 200: Queue entry cancelled
        - 403: Not authorized
        - 404: Queue entry not found
    """
    if queue_type not in ['elder', 'normal']:
        return jsonify({
            'error': 'Invalid queue type. Use "elder" or "normal"'
        }), 400
    
    # Get the queue entry
    if queue_type == 'elder':
        entry = QueueElder.query.get(queue_id)
    else:
        entry = QueueNormal.query.get(queue_id)
    
    if not entry:
        return jsonify({
            'error': 'Queue entry not found'
        }), 404
    
    # Check authorization
    if entry.user_id != current_user.user_id and current_user.role not in ['staff', 'admin']:
        return jsonify({
            'error': 'Not authorized to cancel this entry'
        }), 403
    
    # Delete the entry
    db.session.delete(entry)
    db.session.commit()
    
    return jsonify({
        'message': 'Queue entry cancelled successfully'
    }), 200
