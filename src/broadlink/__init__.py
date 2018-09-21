#!/usr/bin/python

from datetime import datetime
from src import logger

try:
    from Crypto.Cipher import AES
except ImportError as e:
    import pyaes

import time
import random
import socket
import sys
import threading
import codecs

# logger
logger = logger.Logger("broadlink")

def gendevice(devtype, host, mac):
  devices = {

          rm: [0x2712,  # RM2
               0x2737,  # RM Mini
               0x273d,  # RM Pro Phicomm
               0x2783,  # RM2 Home Plus
               0x277c,  # RM2 Home Plus GDT
               0x272a,  # RM2 Pro Plus
               0x2787,  # RM2 Pro Plus2
               0x279d,  # RM2 Pro Plus3
               0x27a9,  # RM2 Pro Plus_300
               0x278b,  # RM2 Pro Plus BL
               0x2797,  # RM2 Pro Plus HYC
               0x27a1,  # RM2 Pro Plus R1
               0x27a6,  # RM2 Pro PP
               0x278f   # RM Mini Shate
               ],
          }

  # Look for the class associated to devtype in devices
  [deviceClass] = [dev for dev in devices if devtype in devices[dev]] or [None]
  if deviceClass is None:
    return device(host=host, mac=mac, devtype=devtype)
  logger.info("Discovered: "+str(deviceClass))
  return deviceClass(host=host, mac=mac, devtype=devtype)

def discover(timeout=None, local_ip_address=None):
  logger.debug('discover starts')
  logger.debug('local IP: '+str(local_ip_address))

  if local_ip_address is None:
      s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
      s.connect(('8.8.8.8', 53))  # connecting to a UDP address doesn't send packets
      local_ip_address = s.getsockname()[0]
  address = local_ip_address.split('.')
  cs = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  cs.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
  cs.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
  cs.bind((local_ip_address,0))
  port = cs.getsockname()[1]
  starttime = time.time()

  devices = []

  timezone = int(time.timezone/-3600)
  packet = bytearray(0x30)

  year = datetime.now().year

  if timezone < 0:
    packet[0x08] = 0xff + timezone - 1
    packet[0x09] = 0xff
    packet[0x0a] = 0xff
    packet[0x0b] = 0xff
  else:
    packet[0x08] = timezone
    packet[0x09] = 0
    packet[0x0a] = 0
    packet[0x0b] = 0
  packet[0x0c] = year & 0xff
  packet[0x0d] = year >> 8
  packet[0x0e] = datetime.now().minute
  packet[0x0f] = datetime.now().hour
  subyear = str(year)[2:]
  packet[0x10] = int(subyear)
  packet[0x11] = datetime.now().isoweekday()
  packet[0x12] = datetime.now().day
  packet[0x13] = datetime.now().month
  packet[0x18] = int(address[0])
  packet[0x19] = int(address[1])
  packet[0x1a] = int(address[2])
  packet[0x1b] = int(address[3])
  packet[0x1c] = port & 0xff
  packet[0x1d] = port >> 8
  packet[0x26] = 6
  checksum = 0xbeaf

  for i in range(len(packet)):
      checksum += packet[i]
  checksum = checksum & 0xffff
  packet[0x20] = checksum & 0xff
  packet[0x21] = checksum >> 8

  cs.sendto(packet, ('255.255.255.255', 80))
  if timeout is None:
    response = cs.recvfrom(1024)
    responsepacket = bytearray(response[0])
    host = response[1]
    mac = responsepacket[0x3a:0x40]
    devtype = responsepacket[0x34] | responsepacket[0x35] << 8
    logger.debug("timeout none")
    device =  gendevice(devtype, host, mac)
    logger.info("Created device: "+str(device))
    return device if device else None
  else:
    logger.debug("timeout is sth")
    while (time.time() - starttime) < timeout:
      cs.settimeout(timeout - (time.time() - starttime))
      try:
        response = cs.recvfrom(1024)
      except socket.timeout:
        return devices
      responsepacket = bytearray(response[0])
      host = response[1]
      devtype = responsepacket[0x34] | responsepacket[0x35] << 8
      mac = responsepacket[0x3a:0x40]
      dev = gendevice(devtype, host, mac)
      devices.append(dev)
    return devices



class device:
  def __init__(self, host, mac, devtype, timeout=10):
    logger.debug("Creating new device")
    self.host = host
    self.mac = mac
    self.devtype = devtype
    self.timeout = timeout
    self.count = random.randrange(0xffff)
    self.key = bytearray([0x09, 0x76, 0x28, 0x34, 0x3f, 0xe9, 0x9e, 0x23, 0x76, 0x5c, 0x15, 0x13, 0xac, 0xcf, 0x8b, 0x02])
    self.iv = bytearray([0x56, 0x2e, 0x17, 0x99, 0x6d, 0x09, 0x3d, 0x28, 0xdd, 0xb3, 0xba, 0x69, 0x5a, 0x2e, 0x6f, 0x58])
    self.id = bytearray([0, 0, 0, 0])
    self.cs = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    self.cs.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    self.cs.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    self.cs.bind(('',0))
    self.type = "Unknown"
    self.lock = threading.Lock()

    if 'pyaes' in globals():
        self.encrypt = self.encrypt_pyaes
        self.decrypt = self.decrypt_pyaes
    else:
        self.encrypt = self.encrypt_pycrypto
        self.decrypt = self.decrypt_pycrypto

  def encrypt_pyaes(self, payload):
    aes = pyaes.AESModeOfOperationCBC(self.key, iv = bytes(self.iv))
    return b"".join([aes.encrypt(bytes(payload[i:i+16])) for i in range(0, len(payload), 16)])

  def decrypt_pyaes(self, payload):
    aes = pyaes.AESModeOfOperationCBC(self.key, iv = bytes(self.iv))
    return b"".join([aes.decrypt(bytes(payload[i:i+16])) for i in range(0, len(payload), 16)])

  def encrypt_pycrypto(self, payload):
    aes = AES.new(bytes(self.key), AES.MODE_CBC, bytes(self.iv))
    return aes.encrypt(bytes(payload))

  def decrypt_pycrypto(self, payload):
    aes = AES.new(bytes(self.key), AES.MODE_CBC, bytes(self.iv))
    return aes.decrypt(bytes(payload))

  def auth(self):
    payload = bytearray(0x50)
    payload[0x04] = 0x31
    payload[0x05] = 0x31
    payload[0x06] = 0x31
    payload[0x07] = 0x31
    payload[0x08] = 0x31
    payload[0x09] = 0x31
    payload[0x0a] = 0x31
    payload[0x0b] = 0x31
    payload[0x0c] = 0x31
    payload[0x0d] = 0x31
    payload[0x0e] = 0x31
    payload[0x0f] = 0x31
    payload[0x10] = 0x31
    payload[0x11] = 0x31
    payload[0x12] = 0x31
    payload[0x1e] = 0x01
    payload[0x2d] = 0x01
    payload[0x30] = ord('T')
    payload[0x31] = ord('e')
    payload[0x32] = ord('s')
    payload[0x33] = ord('t')
    payload[0x34] = ord(' ')
    payload[0x35] = ord(' ')
    payload[0x36] = ord('1')

    response = self.send_packet(0x65, payload)

    payload = self.decrypt(response[0x38:])

    if not payload:
     return False

    key = payload[0x04:0x14]
    if len(key) % 16 != 0:
     return False

    self.id = payload[0x00:0x04]
    self.key = key
    logger.info(key)

    return True

  def get_type(self):
    return self.type

  def send_packet(self, command, payload):
    logger.debug("Device sending packet")
    self.count = (self.count + 1) & 0xffff
    packet = bytearray(0x38)
    packet[0x00] = 0x5a
    packet[0x01] = 0xa5
    packet[0x02] = 0xaa
    packet[0x03] = 0x55
    packet[0x04] = 0x5a
    packet[0x05] = 0xa5
    packet[0x06] = 0xaa
    packet[0x07] = 0x55
    packet[0x24] = 0x2a
    packet[0x25] = 0x27
    packet[0x26] = command
    packet[0x28] = self.count & 0xff
    packet[0x29] = self.count >> 8
    packet[0x2a] = self.mac[0]
    packet[0x2b] = self.mac[1]
    packet[0x2c] = self.mac[2]
    packet[0x2d] = self.mac[3]
    packet[0x2e] = self.mac[4]
    packet[0x2f] = self.mac[5]
    packet[0x30] = self.id[0]
    packet[0x31] = self.id[1]
    packet[0x32] = self.id[2]
    packet[0x33] = self.id[3]

    # pad the payload for AES encryption
    if len(payload)>0:
      numpad=(len(payload)//16+1)*16
      payload=payload.ljust(numpad, b"\x00")

    checksum = 0xbeaf
    for i in range(len(payload)):
      checksum += payload[i]
      checksum = checksum & 0xffff

    payload = self.encrypt(payload)

    packet[0x34] = checksum & 0xff
    packet[0x35] = checksum >> 8

    for i in range(len(payload)):
      packet.append(payload[i])

    checksum = 0xbeaf
    for i in range(len(packet)):
      checksum += packet[i]
      checksum = checksum & 0xffff
    packet[0x20] = checksum & 0xff
    packet[0x21] = checksum >> 8

    starttime = time.time()
    with self.lock:
      while True:
        try:
          self.cs.sendto(packet, self.host)
          self.cs.settimeout(1)
          response = self.cs.recvfrom(2048)
          break
        except socket.timeout:
          if (time.time() - starttime) > self.timeout:
            raise
    return bytearray(response[0])

class rm(device):
  def __init__ (self, host, mac, devtype):
    logger.debug("Creating rm device")
    device.__init__(self, host, mac, devtype)
    self.type = "RM2"

  def check_data(self):
    packet = bytearray(16)
    packet[0] = 4
    response = self.send_packet(0x6a, packet)
    err = response[0x22] | (response[0x23] << 8)
    if err == 0:
      payload = self.decrypt(bytes(response[0x38:]))
      return payload[0x04:]

  def send_data(self, data):
    logger.debug("RM device sending data")
    packet = bytearray([0x02, 0x00, 0x00, 0x00])
    packet += data
    self.send_packet(0x6a, packet)

  def enter_learning(self):
    logger.info("RM device entering learning")
    packet = bytearray(16)
    packet[0] = 3
    self.send_packet(0x6a, packet)

  def check_temperature(self):
    packet = bytearray(16)
    packet[0] = 1
    response = self.send_packet(0x6a, packet)
    err = response[0x22] | (response[0x23] << 8)
    if err == 0:
      payload = self.decrypt(bytes(response[0x38:]))
      if type(payload[0x4]) == int:
        temp = (payload[0x4] * 10 + payload[0x5]) / 10.0
      else:
        temp = (ord(payload[0x4]) * 10 + ord(payload[0x5])) / 10.0
      return temp


# Setup a new Broadlink device via AP Mode. Review the README to see how to enter AP Mode.
# Only tested with Broadlink RM3 Mini (Blackbean)
def setup(ssid, password, security_mode):
  # Security mode options are (0 - none, 1 = WEP, 2 = WPA1, 3 = WPA2, 4 = WPA1/2)
  payload = bytearray(0x88)
  payload[0x26] = 0x14  # This seems to always be set to 14
  # Add the SSID to the payload
  ssid_start = 68
  ssid_length = 0
  for letter in ssid:
    payload[(ssid_start + ssid_length)] = ord(letter)
    ssid_length += 1
  # Add the WiFi password to the payload
  pass_start = 100
  pass_length = 0
  for letter in password:
    payload[(pass_start + pass_length)] = ord(letter)
    pass_length += 1

  payload[0x84] = ssid_length  # Character length of SSID
  payload[0x85] = pass_length  # Character length of password
  payload[0x86] = security_mode  # Type of encryption (00 - none, 01 = WEP, 02 = WPA1, 03 = WPA2, 04 = WPA1/2)

  checksum = 0xbeaf
  for i in range(len(payload)):
    checksum += payload[i]
    checksum = checksum & 0xffff

  payload[0x20] = checksum & 0xff  # Checksum 1 position
  payload[0x21] = checksum >> 8  # Checksum 2 position

  sock = socket.socket(socket.AF_INET,  # Internet
                       socket.SOCK_DGRAM)  # UDP
  sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
  sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
  sock.sendto(payload, ('255.255.255.255', 80))
