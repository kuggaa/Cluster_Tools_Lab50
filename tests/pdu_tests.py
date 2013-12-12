import sys
sys.path.append("/home/user/_cluster/cntrl_hac")
sys.path.append("/home/user/_cluster/testutil_hac")
from exceptionz import DeviceError
from pdu import PDU

import unittest


# Working PDU.
PDU_IP = "192.168.50.110"
# Some device connected to PDU.
DUMMY_DEVICE = PDU("dummy", {"ip": None})
DUMMY_DEVICE_OUTLET = 8


class TestsForPDU(unittest.TestCase):
    def test_correct_settings(self):
        pdu = PDU("my_pdu", {"ip": PDU_IP,
                             "outlet%i" % (DUMMY_DEVICE_OUTLET): DUMMY_DEVICE.id})
        pdu.off(DUMMY_DEVICE)
        pdu.on(DUMMY_DEVICE)


    def test_wrong_ip(self):
        pdu = PDU("my_pdu", {"ip": "127.0.0.1",
                             "outlet%i" % (DUMMY_DEVICE_OUTLET): DUMMY_DEVICE.id})
        with self.assertRaises(DeviceError):
            pdu.off(DUMMY_DEVICE)


    def test_wrong_outlets_config(self):
        pdu = PDU("my_pdu", {"ip": PDU_IP})
        with self.assertRaises(DeviceError):
            pdu.off(DUMMY_DEVICE)


if (__name__ == '__main__'):
    unittest.main()
