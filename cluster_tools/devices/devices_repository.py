from ..configuraster import Configuraster
from ipmi import IPMI
from pdu import PDU
from router import Router


class DevicesRepository(object):
    # Param `infrastructure_conf` - path to file with infrastructure config.
    def __init__(self,
                 infrastructure_conf,
                 ipmi_required=False,
                 pdu_required=False,
                 routers_required=False):
        self._conf = Configuraster(infrastructure_conf)
        self.ipmi_devices = {}
        self.pdu_devices = {}
        self.routers = {}

        if (ipmi_required):
            self._load_ipmi_devices()
        if (pdu_required):
            self._load_pdu_devices()
        if (routers_required):
            self._load_routers()


    def _load_ipmi_devices(self):
        self.ipmi_devices = {}
        for id, settings in self._conf.get_sections_by_prefix("ipmi"):
            self.ipmi_devices[id] = IPMI(id, settings)

    def get_ipmi(self, ipmi_id):
        return self.ipmi_devices.get(ipmi_id, None)

    def get_ipmi_for_node(self, node_id):
        for ipmi in self.ipmi_devices.values():
            if (ipmi.node_id == node_id):
                return ipmi
        return None


    def _load_pdu_devices(self):
        self.pdu_devices = {}
        for id, settings in self._conf.get_sections_by_prefix("pdu"):
            self.pdu_devices[id] = PDU(id, settings)

    def get_pdu(self, pdu_id):
        return self.pdu_devices.get(pdu_id, None)


    def _load_routers(self):
        self.routers = {}
        for id, settings in self._conf.get_sections_by_prefix("router"):
            self.routers[id] = Router(id, settings)

    def get_router(self, router_id):
        return self.routers.get(router_id, None)
