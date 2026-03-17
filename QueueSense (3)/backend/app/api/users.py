# =============================================
# QueueSense - Users API Routes
# =============================================
# This module handles user management endpoints
# including listing, updating, and managing users.
# =============================================

from flask import Blueprint, request, jsonify  # Flask utilities

# Import database and models
from .. import db
from ..models import User
from ..utils.decorators import token_required, admin_required

# =============================================
# Create Users Blueprint
# =============================================
users_bp = Blueprint('users', __name__)


# =============================================
# ROUTE: Get All Users (Admin Only)
# GET /api/users
# =============================================
@users_bp.route('/', methods=['GET'])
@token_required
@admin_required
def get_all_users(current_user):
    """
    Get a list of all users in the system.
    Only accessible by admin users.
    
    Query Parameters:
        - page: Page number (default: 1)
        - per_page: Items per page (default: 20)
        - role: Filter by role (optional)
        - category: Filter by category (optional)
    
    Returns:
        - 200: List of users with pagination
    """
    # Get query parameters for pagination
    page = request.args.get('page', 1, type=int)  # Current page number
    per_page = request.args.get('per_page', 20, type=int)  # Items per page
    
    # Get filter parameters
    role_filter = request.args.get('role')  # Filter by role
    category_filter = request.args.get('category')  # Filter by category
    search_query = request.args.get('search', '').strip() # Search string
    
    # Build query
    query = User.query
    
    # Apply standard filters
    if role_filter and role_filter != 'all':
        query = query.filter(User.role == role_filter)
    if category_filter and category_filter != 'all':
        query = query.filter(User.category == category_filter)
        
    # Apply Search Logic
    if search_query:
        search_pattern = f"%{search_query}%"
        query = query.filter(
            (User.name.ilike(search_pattern)) |
            (User.username.ilike(search_pattern)) |
            (User.phone.ilike(search_pattern))
        )
    
    # Execute paginated query
    pagination = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Convert users to dictionaries
    users_list = []
    for user in pagination.items:
        users_list.append(user.to_dict())
    
    # Return response with pagination and metadata
    return jsonify({
        'users': users_list,
        'metadata': {
            'total_users': User.query.filter_by(role='user').count(),
            'active_users': User.query.filter_by(role='user', is_active=True).count(),
            'elder_users': User.query.filter_by(role='user', category='elder').count(),
        },
        'pagination': {
            'page': pagination.page,
            'per_page': pagination.per_page,
            'total_pages': pagination.pages,
            'total_items': pagination.total,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev
        }
    }), 200


# =============================================
# ROUTE: Get Single User
# GET /api/users/<user_id>
# =============================================
@users_bp.route('/<int:user_id>', methods=['GET'])
@token_required
def get_user(current_user, user_id):
    """
    Get a single user by ID.
    Users can only view their own profile unless admin.
    
    Returns:
        - 200: User information
        - 403: Forbidden (not authorized)
        - 404: User not found
    """
    # Check authorization (user can view self, admin can view anyone)
    if current_user.user_id != user_id and current_user.role != 'admin':
        return jsonify({
            'error': 'Access denied',
            'message': 'You can only view your own profile'
        }), 403
    
    # Fetch user from database
    user = User.query.get(user_id)
    
    # Check if user exists
    if not user:
        return jsonify({
            'error': 'User not found'
        }), 404
    
    return jsonify({
        'user': user.to_dict()
    }), 200


# =============================================
# ROUTE: Update User (Admin Only)
# PUT /api/users/<user_id>
# =============================================
@users_bp.route('/<int:user_id>', methods=['PUT'])
@token_required
@admin_required
def update_user(current_user, user_id):
    """
    Update a user's information.
    Only accessible by admin users.
    
    Request Body (JSON):
        - name: New name (optional)
        - phone: New phone (optional)
        - role: New role (optional)
        - is_active: Active status (optional)
    
    Returns:
        - 200: User updated successfully
        - 404: User not found
    """
    # Fetch user from database
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({
            'error': 'User not found'
        }), 404
    
    # Get request data
    data = request.get_json()
    
    # Update fields if provided
    if data.get('name'):
        user.name = data['name']
    
    if data.get('phone'):
        user.phone = data['phone']
    
    if data.get('role'):
        user.role = data['role']
        
    if data.get('category'):
        user.category = data['category']
    
    if 'is_active' in data:
        user.is_active = data['is_active']
    
    # Save changes
    db.session.commit()
    
    return jsonify({
        'message': 'User updated successfully',
        'user': user.to_dict()
    }), 200


# =============================================
# ROUTE: Delete User (Admin Only)
# DELETE /api/users/<user_id>
# =============================================
@users_bp.route('/<int:user_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_user(current_user, user_id):
    """
    Delete a user from the system.
    Only accessible by admin users.
    
    Returns:
        - 200: User deleted successfully
        - 400: Cannot delete self
        - 404: User not found
    """
    # Prevent admin from deleting themselves
    if current_user.user_id == user_id:
        return jsonify({
            'error': 'Cannot delete yourself',
            'message': 'You cannot delete your own account'
        }), 400
    
    # Fetch user from database
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({
            'error': 'User not found'
        }), 404
    
    # Delete user
    db.session.delete(user)
    db.session.commit()
    
    return jsonify({
        'message': 'User deleted successfully'
    }), 200


# =============================================
# ROUTE: Export Users (Admin Only)
# GET /api/users/export
# =============================================
@users_bp.route('/export', methods=['GET'])
@token_required
@admin_required
def export_users(current_user):
    """
    Export all users to CSV.
    Only accessible by admin users.
    """
    import csv
    import io
    from flask import Response
    from datetime import datetime
    
    # Get parameters
    role_filter = request.args.get('role', 'user')
    category_filter = request.args.get('category', 'all')
    search_query = request.args.get('search', '').strip()
    
    # Build query
    query = User.query
    if role_filter != 'all':
        query = query.filter(User.role == role_filter)
    if category_filter != 'all':
        query = query.filter(User.category == category_filter)
        
    # Apply Search Logic (Matching get_all_users)
    if search_query:
        search_pattern = f"%{search_query}%"
        query = query.filter(
            (User.name.ilike(search_pattern)) |
            (User.username.ilike(search_pattern)) |
            (User.phone.ilike(search_pattern))
        )
        
    users = query.all()
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow(['User ID', 'Name', 'Email/Username', 'Phone', 'Category', 'Status', 'Total Tokens', 'Last Active', 'Joined Date'])
    
    # Data rows
    for user in users:
        d = user.to_dict()
        writer.writerow([
            d['user_id'],
            d['name'],
            d['username'],
            d['phone'] or 'N/A',
            d['category_display'],
            'Active' if d['is_active'] else 'Inactive',
            d['total_tokens'],
            d['last_active_human'],
            d['created_at']
        ])
        
    filename = f"queuesense_users_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename={filename}"}
    )
