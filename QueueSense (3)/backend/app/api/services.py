# =============================================
# QueueSense - Services API Routes
# =============================================
# This module handles service and location
# management endpoints for the queue system.
# =============================================

from flask import Blueprint, request, jsonify  # Flask utilities

# Import database and models
from .. import db
from ..models import Service, Location, Appointment, QueueElder, QueueNormal, Analytics
from ..utils.decorators import token_required, admin_required, staff_required

# =============================================
# Create Services Blueprint
# =============================================
services_bp = Blueprint('services', __name__)


# =============================================
# ROUTE: Get All Services
# GET /api/services
# =============================================
@services_bp.route('/', methods=['GET'])
def get_all_services():
    """
    Get a list of all active services.
    This endpoint is public (no auth required).
    
    Query Parameters:
        - include_inactive: Include inactive services (admin only)
    
    Returns:
        - 200: List of services
    """
    # Get query parameters
    include_inactive = request.args.get('include_inactive', 'false').lower() == 'true'
    
    # Build query
    query = Service.query
    
    # Filter out inactive services by default
    if not include_inactive:
        query = query.filter(Service.is_active == True)
    
    # Execute query
    services = query.order_by(Service.service_name).all()
    
    # Convert to dictionaries
    services_list = [service.to_dict() for service in services]
    
    return jsonify({
        'services': services_list,
        'total': len(services_list)
    }), 200


# =============================================
# ROUTE: Get Single Service with Locations
# GET /api/services/<service_id>
# =============================================
@services_bp.route('/<int:service_id>', methods=['GET'])
def get_service(service_id):
    """
    Get a single service with its locations.
    This endpoint is public.
    
    Returns:
        - 200: Service with locations
        - 404: Service not found
    """
    # Fetch service from database
    service = Service.query.get(service_id)
    
    if not service:
        return jsonify({
            'error': 'Service not found'
        }), 404
    
    # Get locations for this service
    locations = Location.query.filter(
        Location.service_id == service_id,
        Location.is_active == True
    ).all()
    
    # Build response
    service_data = service.to_dict()
    service_data['locations'] = [loc.to_dict() for loc in locations]
    
    return jsonify({
        'service': service_data
    }), 200


# =============================================
# ROUTE: Create New Service (Admin Only)
# POST /api/services
# =============================================
@services_bp.route('/', methods=['POST'])
@token_required
@admin_required
def create_service(current_user):
    """
    Create a new service type.
    Only accessible by admin users.
    
    Request Body (JSON):
        - service_name: Name of the service (required)
        - service_code: Short code for tokens (required)
        - description: Service description (optional)
        - icon: Font Awesome icon class (optional)
        - service_duration: Default duration in minutes (optional)
    
    Returns:
        - 201: Service created successfully
        - 400: Validation error
        - 409: Service code already exists
    """
    data = request.get_json()
    
    # Validate required fields
    if not data.get('service_name'):
        return jsonify({
            'error': 'Service name is required'
        }), 400
    
    if not data.get('service_code'):
        return jsonify({
            'error': 'Service code is required'
        }), 400
    
    # Service codes are now category-based (H, B, R, G)
    # Multiple services can share the same code
    
    # Create new service
    service = Service(
        service_name=data['service_name'],
        service_code=data['service_code'].upper(),  # Uppercase code
        description=data.get('description', ''),
        icon=data.get('icon', 'fa-building'),
        service_duration=data.get('service_duration', 20),
        elder_weight=data.get('elder_weight', 3),
        appointment_weight=data.get('appointment_weight', 2),
        wait_time_weight=data.get('wait_time_weight', 1),
        is_active=True
    )
    
    # Add to database
    db.session.add(service)
    db.session.commit()
    
    return jsonify({
        'message': 'Service created successfully',
        'service': service.to_dict()
    }), 201


# =============================================
# ROUTE: Update Service (Admin Only)
# PUT /api/services/<service_id>
# =============================================
@services_bp.route('/<int:service_id>', methods=['PUT'])
@token_required
@admin_required
def update_service(current_user, service_id):
    """
    Update an existing service.
    Only accessible by admin users.
    
    Returns:
        - 200: Service updated successfully
        - 404: Service not found
    """
    # Fetch service
    service = Service.query.get(service_id)
    
    if not service:
        return jsonify({
            'error': 'Service not found'
        }), 404
    
    data = request.get_json()
    
    # Update fields if provided
    if data.get('service_name'):
        service.service_name = data['service_name']
        
    if data.get('service_code'):
        service.service_code = data['service_code'].upper()
    
    if data.get('description'):
        service.description = data['description']
    
    if data.get('icon'):
        service.icon = data['icon']
    
    if data.get('service_duration'):
        service.service_duration = data['service_duration']
    
    if data.get('elder_weight') is not None:
        service.elder_weight = data['elder_weight']
    
    if data.get('appointment_weight') is not None:
        service.appointment_weight = data['appointment_weight']
    
    if data.get('wait_time_weight') is not None:
        service.wait_time_weight = data['wait_time_weight']
    
    if 'is_active' in data:
        service.is_active = data['is_active']
    
    # Save changes
    db.session.commit()
    
    return jsonify({
        'message': 'Service updated successfully',
        'service': service.to_dict()
    }), 200


# =============================================
# ROUTE: Delete Service (Admin Only)
# DELETE /api/services/<service_id>
# =============================================
@services_bp.route('/<int:service_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_service(current_user, service_id):
    """
    Delete a service.
    Only accessible by admin users.
    
    Returns:
        - 200: Service deleted successfully
        - 404: Service not found
        - 500: Database error
    """
    service = Service.query.get(service_id)
    
    if not service:
        return jsonify({
            'error': 'Service not found'
        }), 404
    
    try:
        # Delete related records (manual cascade + location cleanup)
        
        # 0. Get all locations for this service
        service_locations = Location.query.filter_by(service_id=service_id).all()
        location_ids = [loc.location_id for loc in service_locations]
        
        # Helper queries for cleanup
        # We delete by service_id AND location_ids to catch inconsistent data
        
        # 1. Delete queue entries
        if location_ids:
            QueueElder.query.filter(QueueElder.location_id.in_(location_ids)).delete(synchronize_session=False)
            QueueNormal.query.filter(QueueNormal.location_id.in_(location_ids)).delete(synchronize_session=False)
        
        QueueElder.query.filter_by(service_id=service_id).delete()
        QueueNormal.query.filter_by(service_id=service_id).delete()
        
        # 2. Delete appointments
        if location_ids:
            Appointment.query.filter(Appointment.location_id.in_(location_ids)).delete(synchronize_session=False)
        Appointment.query.filter_by(service_id=service_id).delete()
        
        # 3. Delete analytics
        if location_ids:
            Analytics.query.filter(Analytics.location_id.in_(location_ids)).delete(synchronize_session=False)
        Analytics.query.filter_by(service_id=service_id).delete()
        
        # 4. Delete locations
        # (Already have the list, but delete by ID to be safe)
        if location_ids:
            Location.query.filter(Location.location_id.in_(location_ids)).delete(synchronize_session=False)
        Location.query.filter_by(service_id=service_id).delete()
        
        # 5. Delete service
        db.session.delete(service)
        db.session.commit()
        
        return jsonify({
            'message': 'Service deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': 'Failed to delete service',
            'details': str(e)
        }), 500


# =============================================
# LOCATIONS ROUTES
# =============================================

# =============================================
# ROUTE: Get All Locations for a Service
# GET /api/services/<service_id>/locations
# =============================================
@services_bp.route('/<int:service_id>/locations', methods=['GET'])
def get_locations(service_id):
    """
    Get all locations for a specific service.
    This endpoint is public.
    
    Returns:
        - 200: List of locations
        - 404: Service not found
    """
    # Check if service exists
    service = Service.query.get(service_id)
    
    if not service:
        return jsonify({
            'error': 'Service not found'
        }), 404
    
    # Get locations
    locations = Location.query.filter(
        Location.service_id == service_id,
        Location.is_active == True
    ).all()
    
    return jsonify({
        'locations': [loc.to_dict() for loc in locations],
        'total': len(locations)
    }), 200


# =============================================
# ROUTE: Create Location (Admin Only)
# POST /api/services/<service_id>/locations
# =============================================
@services_bp.route('/<int:service_id>/locations', methods=['POST'])
@token_required
@admin_required
def create_location(current_user, service_id):
    """
    Create a new location for a service.
    Only accessible by admin users.
    
    Request Body (JSON):
        - location_name: Name of location (required)
        - address: Physical address (optional)
        - operating_hours_start: Opening time (optional)
        - operating_hours_end: Closing time (optional)
        - max_capacity: Maximum queue capacity (optional)
    
    Returns:
        - 201: Location created successfully
        - 400: Validation error
        - 404: Service not found
    """
    # Check if service exists
    service = Service.query.get(service_id)
    
    if not service:
        return jsonify({
            'error': 'Service not found'
        }), 404
    
    data = request.get_json()
    
    # Validate required fields
    if not data.get('location_name'):
        return jsonify({
            'error': 'Location name is required'
        }), 400
    
    # Parse operating hours if provided
    from datetime import datetime
    
    hours_start = None
    hours_end = None
    
    if data.get('operating_hours_start'):
        hours_start = datetime.strptime(data['operating_hours_start'], '%H:%M').time()
    
    if data.get('operating_hours_end'):
        hours_end = datetime.strptime(data['operating_hours_end'], '%H:%M').time()
    
    # Create location
    location = Location(
        service_id=service_id,
        location_name=data['location_name'],
        address=data.get('address', ''),
        operating_hours_start=hours_start,
        operating_hours_end=hours_end,
        max_capacity=data.get('max_capacity', 50),
        is_active=True
    )
    
    # Add to database
    db.session.add(location)
    db.session.commit()
    
    return jsonify({
        'message': 'Location created successfully',
        'location': location.to_dict()
    }), 201


# =============================================
# ROUTE: Update Location (Admin Only)
# PUT /api/services/locations/<location_id>
# =============================================
@services_bp.route('/locations/<int:location_id>', methods=['PUT'])
@token_required
@admin_required
def update_location(current_user, location_id):
    """
    Update a location's information.
    Only accessible by admin users.
    
    Returns:
        - 200: Location updated successfully
        - 404: Location not found
    """
    location = Location.query.get(location_id)
    
    if not location:
        return jsonify({
            'error': 'Location not found'
        }), 404
    
    data = request.get_json()
    
    # Update fields if provided
    if data.get('location_name'):
        location.location_name = data['location_name']
    
    if data.get('address'):
        location.address = data['address']
    
    if data.get('max_capacity'):
        location.max_capacity = data['max_capacity']
    
    if 'is_active' in data:
        location.is_active = data['is_active']
    
    # Parse and update operating hours if provided
    from datetime import datetime
    
    if data.get('operating_hours_start'):
        location.operating_hours_start = datetime.strptime(
            data['operating_hours_start'], '%H:%M'
        ).time()
    
    if data.get('operating_hours_end'):
        location.operating_hours_end = datetime.strptime(
            data['operating_hours_end'], '%H:%M'
        ).time()
    
    # Save changes
    db.session.commit()
    
    return jsonify({
        'message': 'Location updated successfully',
        'location': location.to_dict()
    }), 200


# =============================================
# ROUTE: Delete Location (Admin Only)
# DELETE /api/services/locations/<location_id>
# =============================================
@services_bp.route('/locations/<int:location_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_location(current_user, location_id):
    """
    Delete a location.
    Only accessible by admin users.
    
    Returns:
        - 200: Location deleted successfully
        - 404: Location not found
    """
    location = Location.query.get(location_id)
    
    if not location:
        return jsonify({
            'error': 'Location not found'
        }), 404
    
    db.session.delete(location)
    db.session.commit()
    
    return jsonify({
        'message': 'Location deleted successfully'
    }), 200
