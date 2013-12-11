import os


class Router(object):
    class action(object):
        ENABLE = 1
        DISABLE = 2


    def __init__(self, id, ip, ports):
        self.id = id
        self._ip = ip
        self._ports = ports


    # TODO: get rid of os.system().
    def _perform_cmd(self, action, port):
        CMD = "snmpset -v 1 -c private %s 1.3.6.1.2.1.2.2.1.7.%i i %i"
        os.system(CMD % (self._ip, port, action))


    def disable_port(self, device):
        port = self._ports.get(device.id, None)
        assert(port is not None)
        self._perform_cmd(Router.action.DISABLE, port)


    def enable_port(self, device):
        port = self._ports.get(device.id, None)
        assert(port is not None)
        self._perform_cmd(Router.action.ENABLE, port)


class Device(object):
    def __init__(self, id):
        self.id = id


#kvg1 = Device("kvg1")
#router = Router("router", "192.168.50.174", {"kvg1": 13})
#router.enable_port(kvg1)
