# wsgi.py
from newZRL import create_app
import os

# The FLASK_CONFIG environment variable will be set to 'production' on the deployment platform.
application = create_app(os.getenv('FLASK_CONFIG', 'production'))
