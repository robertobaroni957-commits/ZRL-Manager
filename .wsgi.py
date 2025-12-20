import sys
import os

# Add your project directory to the sys.path
# IMPORTANT: Replace with your actual project path
project_home = '/home/robario/ZRL-Manager' 
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Set the FLASK_APP environment variable
os.environ['FLASK_APP'] = 'newZRL'
os.environ['FLASK_CONFIG'] = 'production' # Ensure production config is used

# Set environment variables from your .env file content
# These must match what you had in your local .env file.
os.environ['PA_DB_HOST'] = 'robario.mysql.pythonanywhere-services.com'
os.environ['PA_DB_USER'] = 'robario'
os.environ['PA_DB_PASSWORD'] = 'Lollipop9999'
os.environ['PA_DB_NAME'] = 'robario$zrl_db'
os.environ['SECRET_KEY'] = 'aba3b9004538271230efdbe4b1d2cebc'
os.environ['WTRL_API_COOKIE'] = """eyJpYXQiOjE3NjYwNTEzNzQsImVhdCI6MTc2ODY0MzM3NCwicHJvZmlsZV9waWMiOiJodHRwczpcL1wvd3d3Lnd0cmwucmFjaW5nXC91cGxvYWRzX
m9maWxlX3BpY3R1cmVcL2RlZmF1bHQucG5nIiwiZmlyc3RfbmFtZSI6IlN0cmVldCIsImxhc3RfbmFtZSI6Ikhhd2siLCJlbWFpbCI6ImZyYW5jZXN
yYXZhc2lAaG90bWFpbC5jb20iLCJ1c2VyQ2xhc3MiOiIxIiwiendpZnRJZCI6IjcwNzI3MjciLCJ1dWlkIjoiNjA3NWJiM2YtYWRkNS00NWM1LWEzN
Dk2NDU4YzQ5MTdhIiwidXNlcklkIjoiODc2ODUiLCJjb3VudHJ5X2lkIjoiMzgwIiwiZ2VuZGVyIjoiTWFsZSIsInJhY2VUZWFtIjoiMCJ9.c06da
d79b793c865d890e594fde8b7; _ga_SL0YM0MYT3=GS2.1.s1766051367$o15$g1$t1766051384$j43$l0$h0"""

from newZRL import create_app
application = create_app(os.environ.get("FLASK_CONFIG", "production"))
