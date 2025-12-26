# wsgi.py
from newZRL import create_app
import os

# Forcing 'production' to diagnose environment variable issue
application = create_app('production')
