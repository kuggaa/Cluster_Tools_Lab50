import netsnmp


class PDU(object):
    CMD = ".1.3.6.1.4.1.318.1.1.12.3.3.1.1.4.%i"
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
        netsnmp.snmpset(cmd, Version=1, DestHost=self._ip, Community="private")


    def off(self, device):
        outlet = self._outlets.get(device.id, None)
        assert(outlet is not None)
        self._perform_cmd(PDU.action.OFF, outlet)


    def on(self, device):
        outlet = self._outlets.get(device.id, None)
        assert(outlet is not None)
        self._perform_cmd(PDU.action.ON, outlet)


    def reboot(self, device):
        outlet = self._outlets.get(device.id, None)
        assert(outlet is not None)
        self._perform_cmd(PDU.action.REBOOT, outlet)


class Device(object):
    def __init__(self, id):
        self.id = id


#kvg1 = Device("kvg1")
#pdu1 = PDU("pdu1", "192.168.50.111", {"kvg1": 1})
#pdu2 = PDU("pdu2", "192.168.50.110", {"kvg1": 1})

#pdu1.on(kvg1)
#pdu2.on(kvg1)
