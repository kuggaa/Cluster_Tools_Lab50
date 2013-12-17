import sys
sys.path.append("/usr/share/heartbeat-gui")
sys.path.append("/usr/lib/heartbeat-gui")

import const
import xml.etree.ElementTree as ET
import socket
from pymgmt import *
import string

server_addr = "astra-cluster-1"
password = "user"

#server_addr = "neptune"
#password = "password"


class Communicator(object):
    def __init__(self):
        self._connected = False
    def __del__(self):
        self.disconnect()


    def is_connected(self):
        return self._connected


    def connect(self, server_addr=server_addr, password=password, user_name="user", port=""):
        assert(not self._connected)
        server_ip = socket.gethostbyname(server_addr)
        result = mgmt_connect(server_ip, user_name, password, port)
        if (0 != result):
            print("No connect =(")
            return
        self._connected = True


    def disconnect(self):
        if (not self._connected):
            return
        mgmt_disconnect()
        self._connected = False


    def _perform_cmd(self, cmd):
        assert(self._connected)
        response = mgmt_sendmsg(cmd)
        if (response is None):
            print("OH SHI~")
            return []
        response_list = string.split(response, "\n")
        if ("o" != response_list[0]):
            print("OH SHI~")
            return []
        return response_list[1:]


    def get_cib(self):
        response_str = mgmt_sendmsg("cib_query\ncib")[2:]
        return ET.fromstring(response_str)


    def get_node_state(self, node_id):
        ONLINE_ATTR_IND = 1
        STANDBY_ATTR_IND = 2
        response = self._perform_cmd("node_config\n%s" % (node_id))
        online = ("True" == response[ONLINE_ATTR_IND])
        standby = ("True" == response[STANDBY_ATTR_IND])

        if (not online):
            return const.node_state.OFF
        elif (standby):
            return const.node_state.STANDBY
        else:
            return const.node_state.ON


    def set_standby_mode(self, node_id, standby_mode_enabled):
        cmd = "crm_attribute\nnodes\nset\nstandby\n%s\n%s\n\n"
        state_str = "on" if (standby_mode_enabled) else "off"
        return self._perform_cmd(cmd % (state_str, node_id))


    # Result is a list of nodes ids.
    def get_resource_nodes(self, resource_id):
        return self._perform_cmd("rsc_running_on\n" + resource_id)


    def get_resource_state(self, resource_id):
        state = self._perform_cmd("rsc_status\n" + resource_id)[0]
        if ("unmanaged" in state) or ("unclean" in state) or ("failure ignored" in state):
            return const.resource_state.UNMANAGED
        elif ("failed" in state):
            return const.resource_state.FAILED
        elif ("stopping" in state):
            return const.resource_state.STOPPING
        elif ("not running" in state):
            return const.resource_state.OFF
        elif ("running" in state):
            return const.resource_state.ON
        else:
            assert(False, "Unknown state.")


    def modify_managed_attr(self, resource_id, is_managed):
        state_str = "true" if (is_managed) else "false"
        cmd = "set_rsc_attr\n%s\nmeta\nis-managed\n%s" % (resource_id, state_str)
        self._perform_cmd(cmd)


    # You can modify following CIB elements using this method:
    #     resources;
    #     primitive;
    #     group;
    #     constraints.
    def modify(self, xml_element):
        cmd = "cib_replace\n%s\n%s" % (xml_element.tag,
                                       ET.tostring(xml_element).replace("\n", ""))
        self._perform_cmd(cmd)


    def migrate_resource(self, resource_id, node_id):
        cmd = "migrate\n%s\n%s\nfalse\n" % (resource_name, node_name)
        self._perform_cmd(cmd)


    def cleanup(self, resource_id, node_id):
        cmd = "crm_rsc_cmd\n%s\ncleanup\n%s" % (resource_id, node_id)
        self._perform_cmd(cmd)


    # Param `resource_xml` is instance of ET.Element.
    def remove_resource(self, resource_xml):
        cmd = "cib_delete\nresources\n" + ET.tostring(resource_xml).replace("\n", "")
        self._perform_cmd(cmd)


    # Param `constraint_xml` is instance of ET.Element.
    def remove_constraint(self, constraint_xml):
        cmd = "cib_delete\nconstraints\n" + ET.tostring(constraint_xml).replace("\n", "")
        self._perform_cmd(cmd)
