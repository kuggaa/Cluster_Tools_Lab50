import sys
sys.path.append("/home/user/_cluster/cntrl_hac")
from exceptionz import DeviceError
from ipmi import IPMI

import unittest


# Working IPMI device.
IPMI_IP = "192.168.50.220"
IPMI_LOGIN = "ADMIN"
IPMI_PASSWORD = "ADMIN"


class TestsForIPMI(unittest.TestCase):
    def test_correct_settings(self):
        ipmi = IPMI("my_ipmi", {"ip": IPMI_IP,
                                "login": IPMI_LOGIN,
                                "password": IPMI_PASSWORD})
        ipmi.off()
        ipmi.on()


    def test_wrong_ip(self):
        ipmi = IPMI("my_ipmi", {"ip": "127.0.0.1",
                                "login": IPMI_LOGIN,
                                "password": IPMI_PASSWORD})
        with self.assertRaises(DeviceError):
            ipmi.off()


    def test_wrong_login(self):
        ipmi = IPMI("my_ipmi", {"ip": IPMI_IP,
                                "login": "OLOLOLOLOLOLOLOLOLOLOLOLOLO",
                                "password": IPMI_PASSWORD})
        with self.assertRaises(DeviceError):
            ipmi.off()


    def test_wrong_password(self):
        ipmi = IPMI("my_ipmi", {"ip": IPMI_IP,
                                "login": IPMI_LOGIN,
                                "password": "OLOLOLOLOLOLOLOLOLOLOLOLOLO"})
        with self.assertRaises(DeviceError):
            ipmi.off()


if (__name__ == '__main__'):
    unittest.main()
