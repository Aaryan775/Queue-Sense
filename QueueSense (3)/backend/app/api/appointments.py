# =============================================
# QueueSense - Appointments API Routes
# =============================================
# This module handles appointment booking with
# flexible service windows instead of fixed slots.
# =============================================

from flask import Blueprint, request, jsonify  # Flask utilities
from datetime import datetime, timedelta, time  # For date/time handling

# Import database and models
from .. import db
from ..models import Appointment, Service, Location, User
from ..utils.decorators import token_required, staff_required, admin_required

# =============================================
# Create Appointments Blueprint
# =============================================
appointments_bp = Blueprint('appointments', __name__)


# =============================================
# ROUTE: Get Available Slots
# GET /api/appointments/slots/<service_id>/<location_id>
# =============================================
@appointments_bp.route('/slots/<int:service_id>/<int:location_id>', methods=['GET'])
def get_available_slots(service_id, location_id):
    """
    Get available appointment slots for a service/location.
    Uses service windows (e.g., 10:00-10:20) instead of fixed times.
    
    Query Parameters:
        - date: Date in YYYY-MM-DD format (default: today)
    
    Returns:
        - 200: List of available time windows
        - 404: Service or location not found
    """
    # Get the date parameter
    date_str = request.args.get('date')
    
    if date_str:
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({
                'error': 'Invalid date format. Use YYYY-MM-DD'
            }), 400
    else:
        target_date = datetime.utcnow().date()
    
    # Fetch service and location
    service = Service.query.get(service_id)
    location = Location.query.get(location_id)
    
    if not service or not location:
        return jsonify({
            'error': 'Service or location not found'
        }), 404
    
    # Get operating hours from location
    start_time = location.operating_hours_start or time(9, 0)  # Default 9 AM
    end_time = location.operating_hours_end or time(17, 0)  # Default 5 PM
    
    # Get service window duration - Hardcoded to 30 minutes as requested
    window_duration = 30
    
    # Get all scheduled appointments for the day to check capacity
    existing_appointments = Appointment.query.filter(
        Appointment.service_id == service_id,
        Appointment.location_id == location_id,
        Appointment.appointment_date == target_date,
        Appointment.status.in_(['scheduled', 'checked_in'])
    ).all()
    
    # Create a lookup for existing appointment counts per start time
    slot_counts = {}
    for app in existing_appointments:
        t_str = str(app.time_window_start)
        slot_counts[t_str] = slot_counts.get(t_str, 0) + 1
        
    slots = []
    
    # Generate slots from start_time to end_time
    current_dt = datetime.combine(datetime(2000, 1, 1), start_time)
    end_dt = datetime.combine(datetime(2000, 1, 1), end_time)
    
    # Don't show past slots if date is today
    now = datetime.utcnow()
    is_today = target_date == now.date()
    current_time_dt = datetime.combine(datetime(2000, 1, 1), now.time()) if is_today else None

    while current_dt + timedelta(minutes=window_duration) <= end_dt:
        slot_start = current_dt.time()
        slot_end = (current_dt + timedelta(minutes=window_duration)).time()
        
        # Check if slot is in the past for today
        if is_today and current_dt <= current_time_dt:
            current_dt += timedelta(minutes=window_duration)
            continue
            
        t_str = str(slot_start)
        count = slot_counts.get(t_str, 0)
        
        # Max capacity is 1 per slot (Exclusive booking)
        if count < 1:
            slots.append({
                'window_start': str(slot_start),
                'window_end': str(slot_end),
                'display': f"{slot_start.strftime('%I:%M %p')} - {slot_end.strftime('%I:%M %p')}",
                'available': True,
                'spots_left': 1 - count
            })
        else:
            # Include unavailable slots for frontend hiding/styling
            slots.append({
                'window_start': str(slot_start),
                'window_end': str(slot_end),
                'display': f"{slot_start.strftime('%I:%M %p')} - {slot_end.strftime('%I:%M %p')}",
                'available': False,
                'spots_left': 0
            })
            
        current_dt += timedelta(minutes=window_duration)
        
    # Return structure compatible with frontend
    return jsonify({
        'date': str(target_date),
        'service': service.to_dict(),
        'location': location.to_dict(),
        'slots': slots,
        'next_slot': slots[0] if slots else None, # For compatibility
        'window_duration_minutes': window_duration
    }), 200


# =============================================
# ROUTE: Book Appointment
# POST /api/appointments
# =============================================
@appointments_bp.route('/', methods=['POST'])
@token_required
def book_appointment(current_user):
    """
    Book a new appointment with a flexible service window.
    
    Request Body (JSON):
        - service_id: ID of the service (required)
        - location_id: ID of the location (required)
        - date: Date in YYYY-MM-DD format (required)
        - time_window_start: Start time HH:MM (required)
        - notes: Optional notes
    
    Returns:
        - 201: Appointment booked successfully
        - 400: Validation error or slot unavailable
    """
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['service_id', 'location_id', 'date', 'time_window_start']
    
    for field in required_fields:
        if not data.get(field):
            return jsonify({
                'error': f'{field} is required'
            }), 400
    
    # Parse date and time
    try:
        appointment_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        window_start = datetime.strptime(data['time_window_start'], '%H:%M').time()
    except ValueError as e:
        return jsonify({
            'error': 'Invalid date or time format',
            'details': str(e)
        }), 400
    
    # Get service for window duration
    service = Service.query.get(data['service_id'])
    
    if not service:
        return jsonify({
            'error': 'Service not found'
        }), 404
    
    # Calculate window end - Hardcoded to 30 minutes as requested
    window_start_dt = datetime.combine(appointment_date, window_start)
    window_end_dt = window_start_dt + timedelta(minutes=30)
    window_end = window_end_dt.time()
    
    # Check availability
    existing_count = Appointment.query.filter(
        Appointment.service_id == data['service_id'],
        Appointment.location_id == data['location_id'],
        Appointment.appointment_date == appointment_date,
        Appointment.time_window_start == window_start,
        Appointment.status.in_(['scheduled', 'checked_in'])
    ).count()
    
    if existing_count >= 1:  # Max 1 per slot (Exclusive booking)
        return jsonify({
            'error': 'This time slot is fully booked',
            'message': 'Please choose a different time'
        }), 400
    
    # Create appointment
    appointment = Appointment(
        user_id=current_user.user_id,
        service_id=data['service_id'],
        location_id=data['location_id'],
        appointment_date=appointment_date,
        time_window_start=window_start,
        time_window_end=window_end,
        notes=data.get('notes', ''),
        status='scheduled'
    )
    
    db.session.add(appointment)
    db.session.commit()
    
    return jsonify({
        'message': 'Appointment booked successfully',
        'appointment': appointment.to_dict()
    }), 201


# =============================================
# ROUTE: Get My Appointments
# GET /api/appointments/my
# =============================================
@appointments_bp.route('/my', methods=['GET'])
@token_required
def get_my_appointments(current_user):
    """
    Get the current user's appointments.
    
    Query Parameters:
        - status: Filter by status (optional)
        - upcoming: If 'true', only future appointments
    
    Returns:
        - 200: List of user's appointments
    """
    # Build query
    query = Appointment.query.filter(Appointment.user_id == current_user.user_id)
    
    # Filter by status if provided
    status_filter = request.args.get('status')
    if status_filter:
        query = query.filter(Appointment.status == status_filter)
    
    # Filter for upcoming only
    if request.args.get('upcoming', '').lower() == 'true':
        today = datetime.utcnow().date()
        query = query.filter(Appointment.appointment_date >= today)
    
    # Order by date
    appointments = query.order_by(
        Appointment.appointment_date.asc(),
        Appointment.time_window_start.asc()
    ).all()
    
    return jsonify({
        'appointments': [apt.to_dict() for apt in appointments],
        'total': len(appointments)
    }), 200


# =============================================
# ROUTE: Get Single Appointment
# GET /api/appointments/<app_id>
# =============================================
@appointments_bp.route('/<int:app_id>', methods=['GET'])
@token_required
def get_appointment(current_user, app_id):
    """
    Get a specific appointment by ID.
    
    Returns:
        - 200: Appointment details
        - 403: Not authorized
        - 404: Appointment not found
    """
    appointment = Appointment.query.get(app_id)
    
    if not appointment:
        return jsonify({
            'error': 'Appointment not found'
        }), 404
    
    # Check authorization
    if appointment.user_id != current_user.user_id and current_user.role not in ['staff', 'admin']:
        return jsonify({
            'error': 'Not authorized to view this appointment'
        }), 403
    
    return jsonify({
        'appointment': appointment.to_dict()
    }), 200


# =============================================
# ROUTE: Update Appointment
# PUT /api/appointments/<app_id>
# =============================================
@appointments_bp.route('/<int:app_id>', methods=['PUT'])
@token_required
def update_appointment(current_user, app_id):
    """
    Update an existing appointment.
    
    Request Body (JSON):
        - date: New date (optional)
        - time_window_start: New start time (optional)
        - notes: Updated notes (optional)
    
    Returns:
        - 200: Appointment updated
        - 403: Not authorized
        - 404: Appointment not found
    """
    appointment = Appointment.query.get(app_id)
    
    if not appointment:
        return jsonify({
            'error': 'Appointment not found'
        }), 404
    
    # Check authorization
    if appointment.user_id != current_user.user_id and current_user.role not in ['staff', 'admin']:
        return jsonify({
            'error': 'Not authorized to update this appointment'
        }), 403
    
    # Can only update scheduled appointments
    if appointment.status not in ['scheduled']:
        return jsonify({
            'error': 'Cannot update this appointment',
            'message': f'Appointment status is {appointment.status}'
        }), 400
    
    data = request.get_json()
    
    # Update date if provided
    if data.get('date'):
        try:
            appointment.appointment_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({
                'error': 'Invalid date format'
            }), 400
    
    # Update time if provided
    if data.get('time_window_start'):
        try:
            new_start = datetime.strptime(data['time_window_start'], '%H:%M').time()
            service = Service.query.get(appointment.service_id)
            start_dt = datetime.combine(appointment.appointment_date, new_start)
            end_dt = start_dt + timedelta(minutes=service.service_duration)
            
            appointment.time_window_start = new_start
            appointment.time_window_end = end_dt.time()
        except ValueError:
            return jsonify({
                'error': 'Invalid time format'
            }), 400
    
    # Update notes if provided
    if data.get('notes'):
        appointment.notes = data['notes']
    
    db.session.commit()
    
    return jsonify({
        'message': 'Appointment updated successfully',
        'appointment': appointment.to_dict()
    }), 200


# =============================================
# ROUTE: Cancel Appointment
# DELETE /api/appointments/<app_id>
# =============================================
@appointments_bp.route('/<int:app_id>', methods=['DELETE'])
@token_required
def cancel_appointment(current_user, app_id):
    """
    Cancel an appointment.
    
    Returns:
        - 200: Appointment cancelled
        - 403: Not authorized
        - 404: Appointment not found
    """
    appointment = Appointment.query.get(app_id)
    
    if not appointment:
        return jsonify({
            'error': 'Appointment not found'
        }), 404
    
    # Check authorization
    if appointment.user_id != current_user.user_id and current_user.role not in ['staff', 'admin']:
        return jsonify({
            'error': 'Not authorized to cancel this appointment'
        }), 403
    
    # Update status to cancelled
    appointment.status = 'cancelled'
    db.session.commit()
    
    return jsonify({
        'message': 'Appointment cancelled successfully'
    }), 200


# =============================================
# ROUTE: Check-In for Appointment (Staff)
# POST /api/appointments/<app_id>/check-in
# =============================================
@appointments_bp.route('/<int:app_id>/check-in', methods=['POST'])
@token_required
def check_in_appointment(current_user, app_id):
    """
    Check in for an appointment and auto-join queue.
    
    Returns:
        - 200: Checked in and added to queue
        - 400: Already checked in or invalid status
        - 404: Appointment not found
    """
    appointment = Appointment.query.get(app_id)
    
    if not appointment:
        return jsonify({
            'error': 'Appointment not found'
        }), 404
    
    # Check authorization
    if appointment.user_id != current_user.user_id and current_user.role not in ['staff', 'admin']:
        return jsonify({
            'error': 'Not authorized'
        }), 403
    
    # Check status
    if appointment.status != 'scheduled':
        return jsonify({
            'error': f'Cannot check in. Status is {appointment.status}'
        }), 400
    
    # Update status
    appointment.status = 'checked_in'
    db.session.commit()
    
    # Auto-join queue
    from ..utils.queue_engine import QueueEngine
    
    queue_result = QueueEngine.join_queue(
        user_id=appointment.user_id,
        service_id=appointment.service_id,
        location_id=appointment.location_id,
        appointment_id=appointment.app_id,
        is_emergency=False
    )
    
    return jsonify({
        'message': 'Checked in successfully',
        'appointment': appointment.to_dict(),
        'queue': queue_result
    }), 200


# =============================================
# ROUTE: Get All Appointments (Staff/Admin)
# GET /api/appointments/all
# =============================================
@appointments_bp.route('/all', methods=['GET'])
@token_required
@staff_required
def get_all_appointments(current_user):
    """
    Get all appointments (staff/admin only).
    
    Query Parameters:
        - date: Filter by date YYYY-MM-DD
        - service_id: Filter by service
        - location_id: Filter by location
        - status: Filter by status
    
    Returns:
        - 200: List of appointments
    """
    query = Appointment.query
    
    # Apply filters
    if request.args.get('date'):
        try:
            filter_date = datetime.strptime(request.args.get('date'), '%Y-%m-%d').date()
            query = query.filter(Appointment.appointment_date == filter_date)
        except ValueError:
            pass
    
    if request.args.get('service_id'):
        query = query.filter(Appointment.service_id == request.args.get('service_id', type=int))
    
    if request.args.get('location_id'):
        query = query.filter(Appointment.location_id == request.args.get('location_id', type=int))
    
    if request.args.get('status'):
        query = query.filter(Appointment.status == request.args.get('status'))
    
    # Order and execute
    appointments = query.order_by(
        Appointment.appointment_date.desc(),
        Appointment.time_window_start.asc()
    ).limit(100).all()
    
    return jsonify({
        'appointments': [apt.to_dict() for apt in appointments],
        'total': len(appointments)
    }), 200
