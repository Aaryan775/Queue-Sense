# =============================================
# QueueSense - Authentication Decorators
# =============================================
# This module provides decorator functions for
# protecting routes with JWT authentication and
# role-based access control.
# =============================================

from functools import wraps  # For preserving function metadata in decorators
from flask import request, jsonify, current_app  # Flask utilities
import jwt  # JSON Web Token library

# Import database models
from ..models import User


def token_required(f):
    """
    Decorator that requires a valid JWT token to access the route.
    
    Usage:
        @app.route('/protected')
        @token_required
        def protected_route(current_user):
            return {'message': f'Hello, {current_user.name}'}
    
    The decorator extracts the JWT from the Authorization header,
    validates it, and passes the current user to the decorated function.
    """
    @wraps(f)  # Preserve the original function's metadata
    def decorated(*args, **kwargs):
        token = None  # Initialize token variable
        
        # =============================================
        # Extract Token from Authorization Header
        # =============================================
        # Check if Authorization header exists
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']  # Get header value
            
            # Expected format: "Bearer <token>"
            # Split and get the token part
            parts = auth_header.split()
            
            # Validate header format
            if len(parts) == 2 and parts[0] == 'Bearer':
                token = parts[1]  # Extract the actual token
        
        # If no token found, return error
        if not token:
            return jsonify({
                'error': 'Authentication token is missing',
                'message': 'Please provide a valid JWT token in the Authorization header'
            }), 401  # 401 Unauthorized
        
        # =============================================
        # Validate and Decode JWT Token
        # =============================================
        try:
            # Decode the JWT token using the secret key
            payload = jwt.decode(
                token,
                current_app.config['JWT_SECRET_KEY'],  # Secret key from config
                algorithms=[current_app.config['JWT_ALGORITHM']]  # Algorithm used
            )
            
            # Extract user_id from the token payload
            user_id = payload.get('user_id')
            
            # Fetch the user from database
            current_user = User.query.filter_by(user_id=user_id).first()
            
            # Check if user exists
            if not current_user:
                return jsonify({
                    'error': 'User not found',
                    'message': 'The user associated with this token no longer exists'
                }), 401
            
            # Check if user account is active
            if not current_user.is_active:
                return jsonify({
                    'error': 'Account disabled',
                    'message': 'This user account has been disabled'
                }), 401
                
        except jwt.ExpiredSignatureError:
            # Token has expired
            return jsonify({
                'error': 'Token expired',
                'message': 'Your session has expired. Please login again.'
            }), 401
            
        except jwt.InvalidTokenError:
            # Token is invalid (malformed, wrong signature, etc.)
            return jsonify({
                'error': 'Invalid token',
                'message': 'The provided token is invalid'
            }), 401
        
        # =============================================
        # Call the Original Function
        # =============================================
        # Pass the current_user to the decorated function
        return f(current_user, *args, **kwargs)
    
    return decorated


def admin_required(f):
    """
    Decorator that requires the user to be an admin.
    Must be used AFTER @token_required decorator.
    
    Usage:
        @app.route('/admin-only')
        @token_required
        @admin_required
        def admin_route(current_user):
            return {'message': 'Welcome, admin!'}
    """
    @wraps(f)
    def decorated(current_user, *args, **kwargs):
        # Check if user has admin role
        if current_user.role != 'admin':
            return jsonify({
                'error': 'Admin access required',
                'message': 'You do not have permission to access this resource'
            }), 403  # 403 Forbidden
        
        # User is admin, proceed with the function
        return f(current_user, *args, **kwargs)
    
    return decorated


def staff_required(f):
    """
    Decorator that requires the user to be staff or admin.
    Must be used AFTER @token_required decorator.
    
    Usage:
        @app.route('/staff-only')
        @token_required
        @staff_required
        def staff_route(current_user):
            return {'message': 'Welcome, staff member!'}
    """
    @wraps(f)
    def decorated(current_user, *args, **kwargs):
        # Check if user has staff or admin role
        if current_user.role not in ['staff', 'admin']:
            return jsonify({
                'error': 'Staff access required',
                'message': 'You do not have permission to access this resource'
            }), 403  # 403 Forbidden
        
        # User is staff or admin, proceed with the function
        return f(current_user, *args, **kwargs)
    
    return decorated
