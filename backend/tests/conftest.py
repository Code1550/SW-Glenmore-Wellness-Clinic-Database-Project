import pytest
import sys
import os

# Add the root directory to the Python path
# This assumes 'app.py' is in the directory above 'tests/'
# If 'app.py' is in the same directory as the 'tests/' folder, use os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Now we can import the app
try:
    from app import app as flask_app
except ImportError:
    print("Error: 'app.py' not found. Make sure 'app.py' is in the parent directory of this 'tests' folder.")
    sys.exit(1)

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    flask_app.config['TESTING'] = True
    # You might want to configure a separate test database here
    # For example: flask_app.config['DATABASE_URI'] = 'mongodb://localhost:27017/test_clinic_db'
    
    with flask_app.app_context():
        # This will use the app context created by the fixture
        pass

    yield flask_app

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()