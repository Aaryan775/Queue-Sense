# =============================================
# QueueSense - Staff API Routes
# =============================================
# This module handles staff management including
# assignments, availability, and counter management.
# =============================================

from flask import Blueprint, request, jsonify  # Flask utilities

# Import database and models
from .. import db
from ..models import Staff, User, Service
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
    Create a new staff member from existing user.
    
    Request Body (JSON):
        - user_id: ID of user to promote to staff (required)
        - assigned_services: Array of service IDs (optional)
        - counter_number: Assigned counter number (optional)
    
    Returns:
        - 201: Staff member created
        - 400: Validation error
        - 404: User not found
        - 409: User is already staff
    """
    data = request.get_json()
    
    # Validate required fields
    if not data.get('user_id'):
        return jsonify({
            'error': 'User ID is required'
        }), 400
    
    # Check if user exists
    user = User.query.get(data['user_id'])
    
    if not user:
        return jsonify({
            'error': 'User not found'
        }), 404
    
    # Check if already staff
    existing_staff = Staff.query.filter_by(user_id=data['user_id']).first()
    
    if existing_staff:
        return jsonify({
            'error': 'User is already a staff member'
        }), 409
    
    # Update user role
    user.role = 'staff'
    
    # Create staff record
    staff = Staff(
        user_id=data['user_id'],
        assigned_services=data.get('assigned_services', []),
        counter_number=data.get('counter_number'),
        is_available=True
    )
    
    db.session.add(staff)
    db.session.commit()
    
    return jsonify({
        'message': 'Staff member created successfully',
        'staff': staff.to_dict()
    }), 201


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
    
    # Update fields if provided
    if 'assigned_services' in data:
        staff.assigned_services = data['assigned_services']
    
    if 'counter_number' in data:
        staff.counter_number = data['counter_number']
    
    if 'is_available' in data:
        staff.is_available = data['is_available']
    
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
