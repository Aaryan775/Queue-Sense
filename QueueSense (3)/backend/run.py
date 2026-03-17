# =============================================
# QueueSense - Flask Application Entry Point
# =============================================
# This file serves as the main entry point for
# running the Flask application server.
# =============================================

# Import the Flask application factory
from app import create_app

# Create the Flask application instance using factory pattern
app = create_app()

# Run the application when this file is executed directly
if __name__ == '__main__':
    # Start the Flask development server
    # - debug=True enables auto-reload and detailed error pages
    # - host='0.0.0.0' allows external connections
    # - port=5000 is the default Flask port
    app.run(
        debug=True,      # Enable debug mode for development
        host='0.0.0.0',  # Listen on all network interfaces
        port=5000        # Port number for the server
    )
