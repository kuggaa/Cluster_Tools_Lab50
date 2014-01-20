"""
PDU device.
Tested on APC AP7920.
"""

from ..exceptions import DeviceError
import netsnmp


class PDU(object):
    CMD = ".1.3.6.1.4.1.318.1.1.12.3.3.1.1.4.%i"
    SUCCESS_CODE = 1
    class action(object):
        ON = 1
        OFF = 2
        REBOOT = 3


    def __init__(self, id, settings):
        self.id = id
        self._ip = settings["ip"]

        self._outlets = {}
        for param, val in settings.iteritems():
            if ("outlet" in param):
                outlet = int(param.replace("outlet", ""))
                self._outlets[val] = outlet


    def _perform_cmd(self, action, outlet):
        cmd = netsnmp.Varbind(PDU.CMD % (outlet), val=action, type="INTEGER")
        result = netsnmp.snmpset(cmd, Version=1, DestHost=self._ip, Community="private")
        if (PDU.SUCCESS_CODE != result):
            raise DeviceError(self.id)


    def is_connected(self, device):
        return (device.id in self._outlets)


    def off(self, device):
        outlet = self._outlets.get(device.id, None)
        if (outlet is None):
            raise DeviceError(self.id)
        self._perform_cmd(PDU.action.OFF, outlet)


    def on(self, device):
        outlet = self._outlets.get(device.id, None)
        if (outlet is None):
            raise DeviceError(self.id)
        self._perform_cmd(PDU.action.ON, outlet)


    def reboot(self, device):
        outlet = self._outlets.get(device.id, None)
        if (outlet is None):
            raise DeviceError(self.id)
        self._perform_cmd(PDU.action.REBOOT, outlet)
