import os
import subprocess

try:
    import flask
except ImportError as e:
    print(str(e))
    exit(1)

os.environ['FLASK_APP'] = "src/app"
os.environ['FLASK_ENV'] = "dev"

command = ['flask','run']
subprocess.check_call(command)
