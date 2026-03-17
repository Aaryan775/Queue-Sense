# =============================================
# QueueSense - Configuration Module
# =============================================
# Contains all configuration settings for the
# Flask application including database, JWT,
# and other environment-specific settings.
# =============================================

import os  # Operating system interface for environment variables
from datetime import timedelta  # For JWT expiration time

class Config:
    """
    Base configuration class containing all application settings.
    These settings can be overridden by environment variables.
    """
    
    # =============================================
    # Flask Core Settings
    # =============================================
    
    # Secret key for session management and CSRF protection
    # IMPORTANT: Change this in production!
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'queuesense-super-secret-key-change-in-production'
    
    # =============================================
    # Database Configuration (MySQL)
    # =============================================
    
    # MySQL connection settings
    MYSQL_HOST = os.environ.get('MYSQL_HOST') or 'localhost'  # Database host
    MYSQL_PORT = os.environ.get('MYSQL_PORT') or 3306          # Database port
    MYSQL_USER = os.environ.get('MYSQL_USER') or 'root'        # Database username
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD') or ''    # Database password
    MYSQL_DB = os.environ.get('MYSQL_DB') or 'queuesense'      # Database name
    
    # SQLAlchemy database URI constructed from MySQL settings
    # Format: mysql+pymysql://username:password@host:port/database
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@"
        f"{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
    )
    
    # Disable SQLAlchemy event tracking for better performance
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # =============================================
    # JWT (JSON Web Token) Configuration
    # =============================================
    
    # Secret key specifically for JWT signing
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key-change-in-production'
    
    # JWT token expiration time (24 hours by default)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    
    # Algorithm used for JWT encoding/decoding
    JWT_ALGORITHM = 'HS256'
    
    # =============================================
    # QueueSense Specific Settings
    # =============================================
    
    # Default age threshold to classify user as elder
    ELDER_AGE_THRESHOLD = 60
    
    # Default service window duration in minutes
    DEFAULT_SERVICE_WINDOW = 20
    
    # Queue status refresh interval in milliseconds
    QUEUE_REFRESH_INTERVAL = 5000  # 5 seconds
    
    # Voice announcement settings
    VOICE_ENABLED = True           # Enable/disable voice notifications
    VOICE_REPEAT_COUNT = 2         # Number of times to repeat announcement
    
    # =============================================
    # Priority Weights (Default Values)
    # =============================================
    
    # These can be modified by admin in the database
    DEFAULT_ELDER_WEIGHT = 3       # Priority weight for elderly users
    DEFAULT_APPOINTMENT_WEIGHT = 2  # Priority weight for appointment holders
    DEFAULT_WAIT_TIME_WEIGHT = 1   # Priority weight per 10 minutes of waiting
    
    # =============================================
    # Operating Hours (Default Values)
    # =============================================
    
    DEFAULT_OPENING_TIME = '09:00'  # Default opening time
    DEFAULT_CLOSING_TIME = '17:00'  # Default closing time
    
    # =============================================
    # CORS (Cross-Origin Resource Sharing) Settings
    # =============================================
    
    # Allow requests from any origin during development
    CORS_ORIGINS = ['*']


class DevelopmentConfig(Config):
    """
    Development-specific configuration.
    Enables debug mode and verbose logging.
    """
    DEBUG = True  # Enable Flask debug mode
    

class ProductionConfig(Config):
    """
    Production-specific configuration.
    Disables debug mode for security.
    """
    DEBUG = False  # Disable Flask debug mode


# Dictionary mapping environment names to config classes
# Used by app factory to select appropriate configuration
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
