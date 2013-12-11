import os


class PDU(object):
    class action(object):
        ON = 1
        OFF = 2
        REBOOT = 3


    def __init__(self, id, ip, outlets):
        self.id = id
        self._ip = ip
        self._outlets = outlets


    # TODO: get rid of os.system().
    def _perform_cmd(self, action, outlet):
        CMD = "snmpset -v 1 -c private %s 1.3.6.1.4.1.318.1.1.12.3.3.1.1.4.%i i %i"
        os.system(CMD % (self._ip, outlet, action))


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
