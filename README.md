# black_bean
Server api for controlling broadlink rm device.
Based on https://github.com/mjg59/python-broadlink

Setup (from .whl file):
- create new virtual env
- pip install waitress
- waitress-serve --call 'black_bean:create_app'

Server should launch on http://0.0.0.0:8080 by default


API:

[GET]

/commands -get all commands

[POST, GET, DELETE]

/commands/|name| -add/delete command or get existing
  
[GET]

/groups -get all groups

[POST, GET, DELETE]

/groups/|name| -create/remove group or get existing group

[POST, DELETE]

/groups/|name|/|command| -add/remove command from group


Creating wheel file from source code:
- pip install wheel
- python setup.py bdist_wheel


