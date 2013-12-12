import sys
sys.path.append("/home/user/_cluster/cntrl_hac")

from cluster import Cluster
from pdu import PDU
from router import Router


class Ololobster(Cluster):
    def __init__(self):
        Cluster.__init__(self)
        self._load_pdu_devices()
        self._load_routers()


    def _load_pdu_devices(self):
        self._pdu_devices = {}
        for id, settings in self._conf.get_sections_by_prefix("pdu"):
            self._pdu_devices[id] = PDU(id, settings)
    def _load_routers(self):
        self._routers = {}
        for id, settings in self._conf.get_sections_by_prefix("router"):
            self._routers[id] = Router(id, settings)


    def get_pdu(self, pdu_id):
        return self._pdu_devices.get(pdu_id, None)


    def get_router(self, router_id):
        return self._routers.get(router_id, None)


ololobster = Ololobster()
ololobster.update()
pdu_1 = ololobster.get_pdu("pdu_1")
hp2530_1 = ololobster.get_router("hp2530_1")

#hp2530_1.enable_port(pdu_1)
#pdu_1.on(hp2530_1)
