import netsnmp


class Router(object):
    CMD = ".1.3.6.1.2.1.2.2.1.7.%i"
    class action(object):
        ENABLE = 1
        DISABLE = 2


    def __init__(self, id, settings):
        self.id = id
        self._ip = settings["ip"]

        self._ports = {}
        for param, val in settings.iteritems():
            if ("port" in param):
                port = int(param.replace("port", ""))
                self._ports[val] = port


    def _perform_cmd(self, action, port):
        cmd = netsnmp.Varbind(Router.CMD % (port), val=action, type="INTEGER")
        netsnmp.snmpset(cmd, Version=1, DestHost=self._ip, Community="private")


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
#router = Router("router", "192.168.50.174", {"kvg1": 20})
#router.enable_port(kvg1)
