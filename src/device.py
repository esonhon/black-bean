from src import broadlink
from src import logger

import time

logger = logger.Logger("device")

class Device:

    def __init__(self, data, timeout=10):
        self.device=None
        try:
            device_args = data["device"]
            host = device_args["host"]
            mac = device_args["mac"]
            devtype = device_args["devtype"]
            self.device = broadlink.device(host, mac, devtype)
        except KeyError:
            self.device = broadlink.discover()

    def send_command(self, command):
        try:
            if self.__auth():
                self.device.send_data(command["sequence"])
                return True
        except:
            return False


    def learn_command(self, timeout=10):
        logger.debug("Learning command")
        if not self.__auth():
            return False

        starttime = time.time()
        self.device.enter_learning()
        interval = timeout
        while (time.time() - starttime) < timeout:
            time.sleep(1)
            ir_packet = self.device.check_data()
            if ir_packet:
                break
                # print("Learning ended: " + str(ir_packet))
                # return ir_packet

        ir_packet = self.device.check_data()
        logger.debug("Learning ended: " + str(ir_packet))
        return ir_packet

    def __auth(self):
        if not isinstance(self.device, broadlink.rm):
            return False
        if not self.device.auth():
            logger.error("No auth")
            return False
        return True
