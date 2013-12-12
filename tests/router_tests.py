import sys
sys.path.append("/home/user/_cluster/cntrl_hac")
sys.path.append("/home/user/_cluster/testutil_hac")
from exceptionz import DeviceError
from router import Router

import unittest


# Working router.
ROUTER_IP = "192.168.50.174"
# Some device connected to router.
DUMMY_DEVICE = Router("dummy", {"ip": None})
DUMMY_DEVICE_PORT = 13


class TestsForRouter(unittest.TestCase):
    def test_correct_settings(self):
        router = Router("my_router", {"ip": ROUTER_IP,
                                      "port%i" % (DUMMY_DEVICE_PORT): DUMMY_DEVICE.id})
        router.disable_port(DUMMY_DEVICE)
        router.enable_port(DUMMY_DEVICE)


    def test_wrong_ip(self):
        router = Router("my_router", {"ip": "127.0.0.1",
                                      "port%i" % (DUMMY_DEVICE_PORT): DUMMY_DEVICE.id})
        with self.assertRaises(DeviceError):
            router.disable_port(DUMMY_DEVICE)


    def test_wrong_ports_config(self):
        router = Router("my_router", {"ip": ROUTER_IP})
        with self.assertRaises(DeviceError):
            router.disable_port(DUMMY_DEVICE)


if (__name__ == '__main__'):
    unittest.main()
