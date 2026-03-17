# =============================================
# QueueSense - Flask Application Factory
# =============================================
# This module creates and configures the Flask
# application using the factory pattern for
# better testability and configuration management.
# =============================================

import os  # For environment variable access
from flask import Flask  # Main Flask class
from flask_sqlalchemy import SQLAlchemy  # Database ORM
from flask_cors import CORS  # Cross-Origin Resource Sharing

# Import configuration classes
from .config import config

# =============================================
# Initialize Flask Extensions
# =============================================
# Extensions are initialized without app context
# and bound to the app in create_app function

# SQLAlchemy instance for database operations
db = SQLAlchemy()


def create_app(config_name=None):
    """
    Application factory function that creates and configures
    a Flask application instance.
    
    Args:
        config_name (str): Name of configuration to use
                          ('development', 'production', or 'default')
    
    Returns:
        Flask: Configured Flask application instance
    """
    
    # Create Flask application instance
    # __name__ helps Flask locate resources relative to this module
    # We configure it to serve the frontend directory as static files
    base_dir = os.path.abspath(os.path.dirname(__file__))
    frontend_dir = os.path.join(base_dir, '..', '..', 'frontend')
    
    app = Flask(__name__, 
                static_folder=frontend_dir,
                static_url_path='')
    
    # =============================================
    # Load Configuration
    # =============================================
    
    # Determine which configuration to use
    # Priority: argument > environment variable > default
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')
    
    # Apply configuration to the Flask app
    app.config.from_object(config[config_name])
    
    # =============================================
    # Initialize Extensions with App Context
    # =============================================
    
    # Initialize SQLAlchemy with the app
    db.init_app(app)
    
    # Enable CORS for all routes
    # This allows the frontend to make requests to the API
    CORS(app, resources={r"/*": {"origins": "*"}}, 
         supports_credentials=True,
         allow_headers=["Content-Type", "Authorization", "Access-Control-Allow-Credentials"],
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
    
    # =============================================
    # Register Blueprints (Route Modules)
    # =============================================
    
    # Import and register authentication routes
    from .auth.routes import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    
    # Import and register API routes
    from .api.users import users_bp
    app.register_blueprint(users_bp, url_prefix='/api/users')
    
    from .api.services import services_bp
    app.register_blueprint(services_bp, url_prefix='/api/services')
    
    from .api.queues import queues_bp
    app.register_blueprint(queues_bp, url_prefix='/api/queues')
    
    from .api.appointments import appointments_bp
    app.register_blueprint(appointments_bp, url_prefix='/api/appointments')
    
    from .api.staff import staff_bp
    app.register_blueprint(staff_bp, url_prefix='/api/staff')
    
    from .api.analytics import analytics_bp
    app.register_blueprint(analytics_bp, url_prefix='/api/analytics')

    from .api.settings import settings_bp
    app.register_blueprint(settings_bp, url_prefix='/api/settings')
    
    # =============================================
    # Create Database Tables
    # =============================================
    
    # Create all database tables if they don't exist
    # This is useful for development, but in production
    # you should use migrations
    with app.app_context():
        db.create_all()
    
    # =============================================
    # Register Error Handlers
    # =============================================
    
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 Not Found errors"""
        return {'error': 'Resource not found', 'status': 404}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 Internal Server errors"""
        db.session.rollback()  # Rollback any failed transactions
        return {'error': 'Internal server error', 'status': 500}, 500
    
    # =============================================
    # Health Check Route
    # =============================================
    
    @app.route('/health')
    def health_check():
        """
        Health check endpoint to verify the API is running.
        Used by monitoring tools and load balancers.
        """
        return {
            'status': 'healthy',
            'message': 'QueueSense API is running',
            'version': '1.0.0'
        }

    @app.route('/')
    def index():
        """
        Serve the frontend application.
        """
        return app.send_static_file('index.html')
    
    # Return the configured application
    return app
