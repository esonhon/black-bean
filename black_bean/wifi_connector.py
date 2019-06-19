import subprocess
import re

from functional import seq

COMMAND_LINUX = "sudo grep -r '^psk=' /etc/NetworkManager/system-connections/"
RE_LINUX = '/etc/NetworkManager/system-connections/(.*)'
WPA_COMMAND = "nmcli device wifi list"
SAVED_PASSWORDS = dict()


def get_ssid():
    arg_list = ['/sbin/iwgetid', '-r']
    proc = subprocess.Popen(arg_list, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                            universal_newlines=True)
    (output, dummy) = proc.communicate()
    return output.rstrip()


def get_wpa(name):
    output = (seq(subprocess.check_output(WPA_COMMAND, shell=True)
                  .decode('UTF-8')
                  .split("\n")
                  )
              .filter(lambda x: name in x)
              .flat_map(lambda x: x.split())
              .filter(lambda x: re.match('^WPA', x, flags=0))
              .last()
              )
    return [int(s) for s in list(output) if s.isdigit()].pop()


def get_password(name):
    output = subprocess.check_output(COMMAND_LINUX, shell=True).decode('UTF-8').split("\n")
    for pair in output:
        try:
            pair = re.findall(RE_LINUX, pair)[0].split(':')
            Name = pair[0]
            Pass = pair[1].split('=')[1]
            SAVED_PASSWORDS[Name] = Pass
        except:
            pass
    return SAVED_PASSWORDS[name]


def get_configuration():
    name = get_ssid()
    return name, get_password(name), get_wpa(name)


if __name__ == '__main__':
    print(get_configuration())
