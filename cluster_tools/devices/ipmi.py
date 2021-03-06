"""
IPMI device.
Just a wrap for ipmitool.
"""

from ..exceptions import DeviceError, ProcessError
from .. import process


class IPMI(object):
    CMD = "ipmitool -H %s -I lanplus -U %s -P %s chassis power %s"

    class action:
        ON = "on"
        OFF = "soft"
        REBOOT = "cycle"


    def __init__(self, id, settings):
        self.id = id
        self.node_id = settings["node_id"]
        self._ip = settings["ip"]
        self._login = settings["login"]
        self._password = settings["password"]


    def _perform_cmd(self, action):
        cmd_str = IPMI.CMD % (self._ip, self._login, self._password, action)
        try:
            process.call(cmd_str.split(" "))
        except ProcessError as e:
            raise DeviceError(self.id, e.err_output)


    def on(self):
        self._perform_cmd(IPMI.action.ON)

    def off(self):
        self._perform_cmd(IPMI.action.OFF)

    def reboot(self):
        self._perform_cmd(IPMI.action.REBOOT)
