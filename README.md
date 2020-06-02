# Black bean
Server api for controlling broadlink rm device.
Based on https://github.com/mjg59/python-broadlink

##### **Server setup**(from source files):
1. Go to setup.py location
2. Install requirements listed in setup.py file
3. Export flask env:
> export FLASK_APP=black_bean

4. Start server. From setup.py location type:
> flask run

Server should launch on http://127.0.0.1:5000 by default

**Device setup:**
1. Get wifi credentials (note: ssid can't contain polish letters)
	- Use wifi_connector.py
2. Put device in AP mode : 
	- Hold reset until light blinks fast
	- Hold again, light should blink slowly
3. Connect to BroadlinkProv network
4.  Launch wifi_setup.py with ssid, pass,** wpa+1** args
5. Connect to your network.
6. Start server. Server should detect your device at startup (may take several times)


### API:

[GET]

**/commands** -get all commands

[POST, GET, DELETE]

**/commands/|name| **-add/delete command or get existing
  
[GET]

**/groups** -get all groups

[POST, GET, DELETE]

**/groups/|name| **-create/remove group or get existing group

[POST, DELETE]

**/groups/|name|/|command|** -add/remove command from group


Creating wheel file from source code:
- pip install wheel
- python setup.py bdist_wheel


