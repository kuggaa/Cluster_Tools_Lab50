from exceptionz import DeviceError
import netsnmp


class Router(object):
    CMD = ".1.3.6.1.2.1.2.2.1.7.%i"
    SUCCESS_CODE = 1
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
        result = netsnmp.snmpset(cmd, Version=1, DestHost=self._ip, Community="private")
        if (Router.SUCCESS_CODE != result):
            raise DeviceError(self.id)


    def disable_port(self, device):
        port = self._ports.get(device.id, None)
        if (port is None):
            raise DeviceError(self.id)
        self._perform_cmd(Router.action.DISABLE, port)


    def enable_port(self, device):
        port = self._ports.get(device.id, None)
        if (port is None):
            raise DeviceError(self.id)
        self._perform_cmd(Router.action.ENABLE, port)
