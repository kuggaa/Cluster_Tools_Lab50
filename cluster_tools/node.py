import const
from exceptions import DeviceError

import socket
import time


class Node(object):
    def __init__(self, id, cib, devices_rep):
        self.id = id
        self._cib = cib
        self._devices_rep = devices_rep

        self.state = cib.get_state_of_node(id)
        self.is_unclean = cib.is_unclean(id)
        if (const.node_state.OFF == self.state):
            self.ip_addrs = []
        else:
            self.ip_addrs = socket.gethostbyname_ex(self.id)[2]


    def on_with_ipmi(self):
        """ Returns False in case of fail."""
        ipmi = self._devices_rep.get_ipmi_for_node(self.id)
        if (ipmi is None):
            return False
        try:
            ipmi.on()
            return True
        except DeviceError:
            print("IPMI fail while switching ON.")
            return False


    def on_with_pdu(self):
        """ Returns False in case of fail. """
        # Off.
        for pdu in self._devices_rep.pdu_devices.values():
            if (pdu.is_connected(self.id)):
                try:
                    pdu.off(self.id)
                except DeviceError:
                    pass
        time.sleep(0.5)

        # Now on.
        ok = False
        for pdu in self._devices_rep.pdu_devices.values():
            if (pdu.is_connected(self.id)):
                try:
                    pdu.on(self.id)
                    ok = True
                except DeviceError:
                    pass
        return ok


    def on(self):
        """ Throws DeviceError in case of fail. """
        if (const.node_state.OFF == self.state):
            if not (self.on_with_ipmi() or self.on_with_pdu()):
                raise DeviceError()


    def off_with_ipmi(self):
        """ Returns False in case of fail. """
        ipmi = self._devices_rep.get_ipmi_for_node(self.id)
        if (ipmi is None):
            return False

        try:
            ipmi.off()
            return True
        except DeviceError:
            print("IPMI fail while switching OFF.")
            return False


    def off_with_pdu(self):
        """ Returns False in case of fail. """
        ok = False
        for pdu in self._devices_rep.pdu_devices.values():
            if (pdu.is_connected(self.id)):
                try:
                    pdu.off(self.id)
                    ok = True
                except DeviceError:
                    pass
        return ok


    def off(self):
        """ Throws DeviceError in case of fail. """
        if (const.node_state.OFF != self.state):
            if not (self.off_with_ipmi() or self.off_with_pdu()):
                raise DeviceError()


    def enable_standby_mode(self):
        if (const.node_state.ON == self.state):
            self._cib.enable_standby_mode(self.id)

    def cancel_standby_mode(self):
        if (const.node_state.STANDBY == self.state):
            self._cib.cancel_standby_mode(self.id)


    def is_rdp_available(self, port=3389, timeout=0.5):
        if (0 == len(self.ip_addrs)):
            return False

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            sock.connect((self.ip_addrs[0], port))
            sock.close()
        except socket.error:
            return False
        return True


    def __str__(self):
        return "[%s] %s" % (const.node_state.to_str(self.state), self.id)
    def __repr__(self):
        return self.__str__()
