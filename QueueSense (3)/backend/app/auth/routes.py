# =============================================
# QueueSense - Authentication Routes
# =============================================
# This module handles user authentication including
# registration, login, forgot password, and JWT token management.
# =============================================

import re  # For password validation regex
from flask import Blueprint, request, jsonify, current_app  # Flask utilities
from datetime import datetime, timedelta  # For token expiration
import jwt  # JSON Web Token library
import bcrypt  # Password hashing library

# Import database and models
from .. import db
from ..models import User, Staff
from ..utils.decorators import token_required

# =============================================
# Create Auth Blueprint
# =============================================
# Blueprint groups related routes under /api/auth prefix
auth_bp = Blueprint('auth', __name__)


# =============================================
# Password Validation Helper
# =============================================
def validate_password(password):
    """
    Validate password meets requirements:
    - 8 to 16 characters
    - At least 1 special character (!@#$%^&*(),.?":{}|<>)
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if len(password) < 8:
        return False, 'Password must be at least 8 characters long'
    
    if len(password) > 16:
        return False, 'Password must not exceed 16 characters'
    
    # Check for at least one special character
    special_chars = r'[!@#$%^&*(),.?":{}|<>]'
    if not re.search(special_chars, password):
        return False, 'Password must contain at least 1 special character (!@#$%^&*(),.?":{}|<>)'
    
    return True, None


# =============================================
# ROUTE: Register New User
# POST /api/auth/register
# =============================================
@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Register a new user account.
    """
    try:
        # Get JSON data from request
        data = request.get_json()
        
        # =============================================
        # Validate Required Fields
        # =============================================
        
        # Check if username is provided
        if not data or not data.get('username'):
            return jsonify({
                'error': 'Username is required',
                'field': 'username'
            }), 400
        
        # Check if password is provided
        if not data.get('password'):
            return jsonify({
                'error': 'Password is required',
                'field': 'password'
            }), 400
        
        # Check if name is provided
        if not data.get('name'):
            return jsonify({
                'error': 'Name is required',
                'field': 'name'
            }), 400
        
        # =============================================
        # Validate Password Requirements
        # =============================================
        
        is_valid, error_msg = validate_password(data['password'])
        if not is_valid:
            return jsonify({
                'error': error_msg,
                'field': 'password'
            }), 400
        
        # =============================================
        # Check if Username Already Exists
        # =============================================
        
        existing_user = User.query.filter_by(username=data['username']).first()
        
        if existing_user:
            return jsonify({
                'error': 'Username already taken',
                'message': 'An account with this username already exists'
            }), 409
        
        # =============================================
        # Hash Password Using Bcrypt
        # =============================================
        
        password_bytes = data['password'].encode('utf-8')
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(password_bytes, salt)
        password_hash_str = password_hash.decode('utf-8')
        
        # =============================================
        # Validate Age and Phone
        # =============================================
        
        age = data.get('age')
        phone = data.get('phone')
        
        # Age validation: 1 to 120
        if age is not None:
            try:
                age_int = int(age)
                if age_int < 1 or age_int > 120:
                    return jsonify({
                        'error': 'Age must be between 1 and 120',
                        'field': 'age'
                    }), 400
            except (ValueError, TypeError):
                return jsonify({
                    'error': 'Invalid age format',
                    'field': 'age'
                }), 400
        
        # Phone validation: Exactly 10 digits
        if phone:
            # Remove any non-digit characters if they exist, but the requirement is "exactly 10 digits"
            # so we'll check if it's 10 digits and only digits.
            if not str(phone).isdigit() or len(str(phone)) != 10:
                return jsonify({
                    'error': 'Phone number must be exactly 10 digits',
                    'field': 'phone'
                }), 400
        
        # =============================================
        # Determine User Category Based on Age
        # =============================================
        
        category = 'normal'
        
        if age and age >= current_app.config.get('ELDER_AGE_THRESHOLD', 60):
            category = 'elder'
        
        # =============================================
        # Create New User Record
        # =============================================
        
        new_user = User(
            username=data['username'],
            password_hash=password_hash_str,
            name=data['name'],
            phone=data.get('phone'),
            age=age,
            category=category,
            role='user',
            is_active=True
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        # =============================================
        # Generate JWT Token for New User
        # =============================================
        
        token = generate_jwt_token(new_user)
        
        return jsonify({
            'message': 'Registration successful',
            'user': new_user.to_dict(),
            'token': token
        }), 201

    except Exception as e:
        db.session.rollback()
        print(f"Registration error: {str(e)}")
        # If it's a database error, it might be due to schema mismatch
        if "Unknown column" in str(e):
             return jsonify({
                'error': 'Database Error',
                'message': 'Database schema mismatch. Please re-import queuesense.sql'
            }), 500
            
        return jsonify({
            'error': 'Registration failed',
            'message': str(e)
        }), 500


# =============================================
# ROUTE: User Login
# POST /api/auth/login
# =============================================
@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Authenticate user with username and password.
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or not data.get('username') or not data.get('password'):
            return jsonify({
                'error': 'Username and password are required'
            }), 400
        
        # Find user by username
        user = User.query.filter_by(username=data['username']).first()
        
        if not user:
            return jsonify({
                'error': 'Invalid credentials',
                'message': 'Username or password is incorrect'
            }), 401
        
        # Check if account is active
        if not user.is_active:
            return jsonify({
                'error': 'Account disabled',
                'message': 'This account has been disabled'
            }), 401
        
        # Verify password
        stored_hash = user.password_hash.encode('utf-8')
        input_password = data['password'].encode('utf-8')
        
        if not bcrypt.checkpw(input_password, stored_hash):
            return jsonify({
                'error': 'Invalid credentials',
                'message': 'Username or password is incorrect'
            }), 401
        
        # Generate JWT Token
        token = generate_jwt_token(user)
        
        # Get staff info if user is staff
        staff_info = None
        if user.role == 'staff':
            staff = Staff.query.filter_by(user_id=user.user_id).first()
            if staff:
                staff_info = staff.to_dict()
        
        return jsonify({
            'message': 'Login successful',
            'user': user.to_dict(),
            'staff_info': staff_info,
            'token': token
        }), 200

    except Exception as e:
        print(f"Login error: {str(e)}")
        if "Unknown column" in str(e):
             return jsonify({
                'error': 'Database Error',
                'message': 'Database schema mismatch. Please re-import queuesense.sql'
            }), 500
            
        return jsonify({
            'error': 'Login failed',
            'message': str(e)
        }), 500





# =============================================
# ROUTE: Get Current User
# GET /api/auth/me
# =============================================
@auth_bp.route('/me', methods=['GET'])
@token_required
def get_current_user(current_user):
    """
    Get the currently authenticated user's information.
    """
    staff_info = None
    if current_user.role == 'staff':
        staff = Staff.query.filter_by(user_id=current_user.user_id).first()
        if staff:
            staff_info = staff.to_dict()
    
    return jsonify({
        'user': current_user.to_dict(),
        'staff_info': staff_info
    }), 200


# =============================================
# ROUTE: Forgot Password
# POST /api/auth/forgot-password
# =============================================
@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    """
    Reset user password using username (Demo version - no email/OTP).
    """
    try:
        data = request.get_json()
        
        if not data or not data.get('username') or not data.get('newPassword'):
            return jsonify({'error': 'Missing required fields'}), 400
            
        user = User.query.filter_by(username=data['username']).first()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
            
        # Update password
        password_bytes = data['newPassword'].encode('utf-8')
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(password_bytes, salt)
        user.password_hash = password_hash.decode('utf-8')
        
        db.session.commit()
        
        return jsonify({'message': 'Password reset successful'}), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Password reset error: {str(e)}")
        return jsonify({'error': 'Password reset failed', 'details': str(e)}), 500


# =============================================
# ROUTE: Update User Profile
# PUT /api/auth/profile
# =============================================
@auth_bp.route('/profile', methods=['PUT'])
@token_required
def update_profile(current_user):
    """
    Update the current user's profile information.
    """
    data = request.get_json()
    
    if data.get('name'):
        current_user.name = data['name']
    
    if data.get('phone'):
        current_user.phone = data['phone']
    
    if data.get('age'):
        current_user.age = data['age']
        if data['age'] >= current_app.config.get('ELDER_AGE_THRESHOLD', 60):
            current_user.category = 'elder'
        else:
            current_user.category = 'normal'
    
    db.session.commit()
    
    return jsonify({
        'message': 'Profile updated successfully',
        'user': current_user.to_dict()
    }), 200


# =============================================
# ROUTE: Change Password (Authenticated)
# PUT /api/auth/password
# =============================================
@auth_bp.route('/password', methods=['PUT'])
@token_required
def change_password(current_user):
    """
    Change the current user's password (requires authentication).
    """
    data = request.get_json()
    
    if not data.get('current_password') or not data.get('new_password'):
        return jsonify({
            'error': 'Current password and new password are required'
        }), 400
    
    # Validate new password
    is_valid, error_msg = validate_password(data['new_password'])
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    # Verify current password
    stored_hash = current_user.password_hash.encode('utf-8')
    current_password = data['current_password'].encode('utf-8')
    
    if not bcrypt.checkpw(current_password, stored_hash):
        return jsonify({
            'error': 'Current password is incorrect'
        }), 401
    
    # Hash new password
    new_password_bytes = data['new_password'].encode('utf-8')
    salt = bcrypt.gensalt()
    new_hash = bcrypt.hashpw(new_password_bytes, salt)
    
    current_user.password_hash = new_hash.decode('utf-8')
    db.session.commit()
    
    return jsonify({
        'message': 'Password changed successfully'
    }), 200


# =============================================
# Helper Function: Generate JWT Token
# =============================================
def generate_jwt_token(user):
    """
    Generate a JWT token for a user.
    """
    payload = {
        'user_id': user.user_id,
        'username': user.username,
        'role': user.role,
        'exp': datetime.utcnow() + current_app.config['JWT_ACCESS_TOKEN_EXPIRES']
    }
    
    token = jwt.encode(
        payload,
        current_app.config['JWT_SECRET_KEY'],
        algorithm=current_app.config['JWT_ALGORITHM']
    )
    
    return token
