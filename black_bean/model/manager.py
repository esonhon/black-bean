import os
import time
import json

from ..util.logger import logged, Logger
from .device import Device
from .command_manager import CommandManager
from .group_manager import GroupManager

logger = Logger("manager")

class Manager:
    def __init__(self, config_path, ir_path):
        self.ir_path = ir_path
        self.config_path = config_path
        self.deviceUnit = Device()
        data = fetch_data(config_path)
        self.commandManager = CommandManager(data, ir_path)
        self.groupManager = GroupManager(data)

    @logged(__qualname__)
    def merge_data(self, lock):
        logger.debug("Merging data")
        starttime = time.time()
        lock.acquire()
        wipe_folder(self.ir_path)
        dict = {}
        dict["device"] = {
            "host": self.deviceUnit.device.host,
            "devtype": self.deviceUnit.device.devtype
        }
        dict["commands"] = list(map(lambda x: {"name": x}, self.commandManager.get_all()))
        dict["groups"] = self.groupManager.get_all()

        for cmd in self.commandManager.list:
            name = cmd["name"]
            cmd_path = self.ir_path + "/" + name
            try:
                file = open(cmd_path, "wb+")
                file.write(cmd["sequence"])
                file.close()
            except FileNotFoundError:
                logger.error("IR file not found")
                return
        jdict = json.dumps(dict, indent=4)
        file = open(self.config_path, "w")
        file.write(jdict)
        file.close()
        lock.release()
        elapsed = time.time() - starttime
        logger.debug(jdict)
        logger.info("Merging data took: " + str(elapsed) + "s")

def wipe_folder(path):
    for the_file in os.listdir(path):
        file_path = os.path.join(path, the_file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(e)

def fetch_data(path):
    try:
        json_data = open(path).read()
        return json.loads(json_data)
    except Exception as e:
        logger.error("Data fetching error: " + str(e))
        return None
