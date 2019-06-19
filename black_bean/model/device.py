import time

from ..util import broadlink
from ..util.logger import logged

class Device:

    def __init__(self):
        try:
            self.device = self.__discover().pop()
        except IndexError:
            self.device = None

    @logged(__qualname__)
    def send_command(self, command):
        try:
            if self.__auth():
                self.device.send_data(command["sequence"])
                return True
        except:
            return False

    @logged(__qualname__)
    def learn_command(self, timeout=10):
        if not self.__auth():
            return False

        start_time = time.time()
        self.device.enter_learning()
        while (time.time() - start_time) < timeout:
            time.sleep(1)
            ir_packet = self.device.check_data()
            if ir_packet:
                break

        ir_packet = self.device.check_data()
        return ir_packet

    def __auth(self):
        return self.device.auth()

    def __discover(self):
        return broadlink.discover()
