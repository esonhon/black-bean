# black_bean
Server api for controlling broadlink rm device.

Setup (python 2.7):
- create new virtual env
- install dependencies from reqirements.txt
- fill data in config.ini 
- launch black_bean.sh script for server launch 


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



