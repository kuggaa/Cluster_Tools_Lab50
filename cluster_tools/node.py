import const
from exceptions import DeviceError

import socket
import time


class Node(object):
    def __init__(self, id, cib, devices_rep):
        self.id = id
        self._cib = cib
        self._devices_rep = devices_rep

        self.state = cib.get_node_state(id)
        if (const.node_state.OFF == self.state):
            self.ip_addrs = []
        else:
            self.ip_addrs = socket.gethostbyname_ex(self.id)[2]


    def _on_with_ipmi(self):
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


    def _on_with_pdu(self):
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
        if (const.node_state.OFF == self.state):
            if not (self._on_with_ipmi() or self._on_with_pdu()):
                raise DeviceError()


    def _off_with_ipmi(self):
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


    # Returns False in case of fail.
    def _off_with_pdu(self):
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
        if (const.node_state.OFF != self.state):
            if not (self._off_with_ipmi() or self._off_with_pdu()):
                raise DeviceError()


    def enable_standby_mode(self):
        if (const.node_state.ON == self.state):
            self._cib.enable_standby_mode(self.id)

    def cancel_standby_mode(self):
        if (const.node_state.STANDBY == self.state):
            self._cib.cancel_standby_mode(self.id)


    def __str__(self):
        return "[%s] %s" % (const.node_state.to_str(self.state), self.id)
    def __repr__(self):
        return self.__str__()
