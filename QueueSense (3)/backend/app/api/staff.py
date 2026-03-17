# =============================================
# QueueSense - Staff API Routes
# =============================================
# This module handles staff management including
# assignments, availability, and counter management.
# =============================================

import bcrypt
from flask import Blueprint, request, jsonify  # Flask utilities

# Import database and models
from .. import db
from ..models import Staff, User, Service, QueueElder, QueueNormal
from ..utils.decorators import token_required, admin_required, staff_required

# =============================================
# Create Staff Blueprint
# =============================================
staff_bp = Blueprint('staff', __name__)


# =============================================
# ROUTE: Get All Staff (Admin Only)
# GET /api/staff
# =============================================
@staff_bp.route('/', methods=['GET'])
@token_required
@admin_required
def get_all_staff(current_user):
    """
    Get a list of all staff members.
    Only accessible by admin users.
    
    Returns:
        - 200: List of staff members with user details
    """
    # Query all staff members
    staff_list = Staff.query.all()
    
    # Convert to list with full details
    result = []
    for staff in staff_list:
        staff_data = staff.to_dict()
        
        # Flatten user data for easier frontend access
        if staff.user:
            staff_data['user_name'] = staff.user.name
            staff_data['username'] = staff.user.username
        else:
            staff_data['user_name'] = "Unknown"
            staff_data['username'] = "N/A"
            
        # Get assigned service names
        if staff.assigned_services:
            services = Service.query.filter(
                Service.service_id.in_(staff.assigned_services)
            ).all()
            staff_data['service_names'] = [s.service_name for s in services]
        else:
            staff_data['service_names'] = []
        
        result.append(staff_data)
    
    return jsonify({
        'staff': result,
        'total': len(result)
    }), 200


# =============================================
# ROUTE: Get Single Staff Member
# GET /api/staff/<staff_id>
# =============================================
@staff_bp.route('/<int:staff_id>', methods=['GET'])
@token_required
@staff_required
def get_staff(current_user, staff_id):
    """
    Get a single staff member by ID.
    
    Returns:
        - 200: Staff member details
        - 404: Staff not found
    """
    staff = Staff.query.get(staff_id)
    
    if not staff:
        return jsonify({
            'error': 'Staff member not found'
        }), 404
    
    staff_data = staff.to_dict()
    
    # Get assigned service names
    if staff.assigned_services:
        services = Service.query.filter(
            Service.service_id.in_(staff.assigned_services)
        ).all()
        staff_data['service_names'] = [s.service_name for s in services]
    
    return jsonify({
        'staff': staff_data
    }), 200


# =============================================
# ROUTE: Create Staff Member (Admin Only)
# POST /api/staff
# =============================================
@staff_bp.route('/', methods=['POST'])
@token_required
@admin_required
def create_staff(current_user):
    """
    Create a new staff member.
    If user_id is provided, promotes existing user.
    If name/email/password is provided, creates user first.
    
    Request Body (JSON):
        - user_id: ID of existing user (optional)
        - name: Full name (required if user_id missing and new user)
        - email: Email address (required if user_id missing)
        - password: Password (required if user_id missing and new user)
        - assigned_services: Array of service IDs (optional)
        - counter_number: Assigned counter number (optional)
    """
    data = request.get_json()
    user_id = data.get('user_id')
    user = None

    try:
        if not user_id:
            # Streamlined creation: create or find user first
            name = data.get('name')
            email = data.get('email')
            password = data.get('password')

            if not email:
                return jsonify({'error': 'Email is required'}), 400

            # Check if user already exists
            user = User.query.filter_by(username=email).first()
            if user:
                # If user exists, check if they are already staff
                existing_staff = Staff.query.filter_by(user_id=user.user_id).first()
                if existing_staff:
                    return jsonify({'error': 'A staff member with this email address is already registered'}), 409
                
                # Promote existing user to staff role
                user.role = 'staff'
                if name: user.name = name
            else:
                # Create new user
                if not name or not password:
                    return jsonify({'error': 'Full Name and Password are required to create a new staff account'}), 400

                if len(password) < 6:
                    return jsonify({'error': 'Password must be at least 6 characters long'}), 400

                password_bytes = password.encode('utf-8')
                salt = bcrypt.gensalt()
                password_hash = bcrypt.hashpw(password_bytes, salt)

                user = User(
                    username=email,
                    name=name,
                    password_hash=password_hash.decode('utf-8'),
                    role='staff',
                    is_active=True
                )
                db.session.add(user)
                db.session.flush() # Get user_id before commit
        else:
            # Promote existing user by ID
            user = User.query.get(user_id)
            if not user:
                return jsonify({'error': 'User not found'}), 404
            
            # Check if already staff
            existing_staff = Staff.query.filter_by(user_id=user_id).first()
            if existing_staff:
                return jsonify({'error': 'User is already a staff member'}), 409
            
            user.role = 'staff'

        # Ported Validation (exactly one service)
        services = data.get('assigned_services', [])
        if not services or len(services) != 1:
            return jsonify({'error': 'Each staff member must have exactly one assigned service'}), 400

        # Ported Validation (counter 1-4)
        counter = data.get('counter_number')
        if counter is not None:
            try:
                counter = int(counter)
                if counter < 1 or counter > 4:
                    return jsonify({'error': 'Counter number must be between 1 and 4'}), 400
            except (ValueError, TypeError):
                return jsonify({'error': 'Invalid counter number format'}), 400

        # Create staff record
        staff = Staff(
            user_id=user.user_id,
            assigned_services=data.get('assigned_services', []),
            counter_number=counter,
            is_available=True
        )
        
        db.session.add(staff)
        db.session.commit()
        
        return jsonify({
            'message': 'Staff member created successfully',
            'staff': staff.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        print(f"Error in create_staff: {str(e)}")
        return jsonify({'error': f'Database error: {str(e)}'}), 500


# =============================================
# ROUTE: Update Staff Member (Admin Only)
# PUT /api/staff/<staff_id>
# =============================================
@staff_bp.route('/<int:staff_id>', methods=['PUT'])
@token_required
@admin_required
def update_staff(current_user, staff_id):
    """
    Update a staff member's information.
    
    Request Body (JSON):
        - assigned_services: Array of service IDs (optional)
        - counter_number: New counter number (optional)
        - is_available: Availability status (optional)
    
    Returns:
        - 200: Staff member updated
        - 404: Staff not found
    """
    staff = Staff.query.get(staff_id)
    
    if not staff:
        return jsonify({
            'error': 'Staff member not found'
        }), 404
    
    data = request.get_json()
    
    # Update fields if provided with ported validation
    if 'assigned_services' in data:
        services = data['assigned_services']
        if not services or len(services) != 1:
            return jsonify({'error': 'Each staff member must have exactly one assigned service'}), 400
        staff.assigned_services = services
    
    if 'counter_number' in data:
        counter = data['counter_number']
        if counter is not None:
            try:
                counter = int(counter)
                if counter < 1 or counter > 4:
                    return jsonify({'error': 'Counter number must be between 1 and 4'}), 400
            except (ValueError, TypeError):
                return jsonify({'error': 'Invalid counter number format'}), 400
        staff.counter_number = counter
    
    if 'is_available' in data:
        staff.is_available = data['is_available']

    # Update associated user name if provided
    if 'name' in data:
        user = User.query.get(staff.user_id)
        if user:
            user.name = data['name']
    
    db.session.commit()
    
    return jsonify({
        'message': 'Staff member updated successfully',
        'staff': staff.to_dict()
    }), 200


# =============================================
# ROUTE: Delete Staff Member (Admin Only)
# DELETE /api/staff/<staff_id>
# =============================================
@staff_bp.route('/<int:staff_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_staff(current_user, staff_id):
    """
    Remove staff privileges from a user.
    
    Returns:
        - 200: Staff privileges removed
        - 404: Staff not found
    """
    staff = Staff.query.get(staff_id)
    
    if not staff:
        return jsonify({
            'error': 'Staff member not found'
        }), 404
    
    # Update user role back to 'user'
    user = User.query.get(staff.user_id)
    if user:
        user.role = 'user'
    
    # Note: staff_id nullification skipped because columns don't exist in v3 schema
    # (Virtual linking via counter_number is used instead)
    
    # Delete staff record
    db.session.delete(staff)
    db.session.commit()
    
    return jsonify({
        'message': 'Staff privileges removed successfully'
    }), 200


# =============================================
# ROUTE: Update My Availability (Staff)
# PUT /api/staff/availability
# =============================================
@staff_bp.route('/availability', methods=['PUT'])
@token_required
@staff_required
def update_availability(current_user):
    """
    Update current staff member's availability status.
    
    Request Body (JSON):
        - is_available: Boolean availability status
        - counter_number: Current counter number
    
    Returns:
        - 200: Availability updated
        - 404: Staff record not found
    """
    staff = Staff.query.filter_by(user_id=current_user.user_id).first()
    
    if not staff:
        return jsonify({
            'error': 'Staff record not found'
        }), 404
    
    data = request.get_json()
    
    if 'is_available' in data:
        staff.is_available = data['is_available']
    
    if 'counter_number' in data:
        staff.counter_number = data['counter_number']
    
    db.session.commit()
    
    return jsonify({
        'message': 'Availability updated',
        'staff': staff.to_dict()
    }), 200


# =============================================
# ROUTE: Get Available Staff for Service
# GET /api/staff/available/<service_id>
# =============================================
@staff_bp.route('/available/<int:service_id>', methods=['GET'])
@token_required
@staff_required
def get_available_staff(current_user, service_id):
    """
    Get available staff members for a specific service.
    
    Returns:
        - 200: List of available staff
    """
    # Get all staff assigned to this service and available
    all_staff = Staff.query.filter(
        Staff.is_available == True
    ).all()
    
    # Filter by assigned services (JSON array contains service_id)
    available_staff = []
    
    for staff in all_staff:
        if staff.assigned_services and service_id in staff.assigned_services:
            available_staff.append(staff.to_dict())
    
    return jsonify({
        'available_staff': available_staff,
        'total': len(available_staff)
    }), 200
