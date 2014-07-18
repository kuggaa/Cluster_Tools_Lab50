import const
import xml.etree.ElementTree as ET
import socket
import ssl


server_addr = "astra-cluster-1"
password = "user"


class CommunicatorError(Exception):
    pass


class Communicator(object):
    SUCCESS = "o"
    MGMT_PROTOCOL_VER = "2.1"
    LOGIN_CMD = "login\n%s\n%s\n%s"
    LOGOUT_CMD = "logout"
    STANDBY_MODE_CMD = "crm_attribute\nnodes\nset\nstandby\n%s\n%s\n\n"


    def __init__(self):
        self._connected = False
        self._sock = None

    def __del__(self):
        self.disconnect()


    def is_connected(self):
        return self._connected


    def connect(self, host=server_addr, login="user", password=password, port=5560, timeout=60.0):
        assert(not self._connected)
        self._sock = ssl.wrap_socket(socket.socket(socket.AF_INET, socket.SOCK_STREAM),
                                     ssl_version=ssl.PROTOCOL_TLSv1,
                                     ciphers="HIGH:+ADH",
                                     do_handshake_on_connect=True)
        self._sock.settimeout(timeout)
        self._connected = True
        self._sock.connect((host, port))

        login_cmd = Communicator.LOGIN_CMD % (login,
                                              password,
                                              Communicator.MGMT_PROTOCOL_VER)
        result = self._communicate(login_cmd)
        if (Communicator.SUCCESS != result):
            print("No connect =(")
            self.disconnect()


    def disconnect(self):
        if (not self._connected):
            return
        #self._communicate(Communicator.LOGOUT_CMD)
        self._sock.close()
        self._connected = False


    def _communicate(self, cmd):
        assert(self._connected)
        self._sock.write(cmd + b'\x00')
        response = ""
        while True:
            response += self._sock.read()
            if (len(response) > 0) and (response[-1] == b'\x00'):
                break
        return response.strip(b'\x00')


    def _perform_cmd(self, cmd):
        """ Wrap around _communicate() method. """
        response = self._communicate(cmd)
        if (response is None):
            print("OH SHI~")
            return []
        else:
            response_list = response.split("\n")
            if (Communicator.SUCCESS != response_list[0]):
                print("mgmt response:", response)
                #if (len(response_list) > 1):
                #    err_msg = response_list[1]
                #    raise "OLOLO"
            else:
                return response_list[1:]


    def enable_standby_mode(self, node_id):
        self._perform_cmd(Communicator.STANDBY_MODE_CMD % ("on", node_id))

    def cancel_standby_mode(self, node_id):
        self._perform_cmd(Communicator.STANDBY_MODE_CMD % ("off", node_id))


    def modify_attr(self, resource_id, attr, val):
        cmd = "set_rsc_attr\n%s\nmeta\n%s\n%s" % (resource_id, attr, val)
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
        cmd = "migrate\n%s\n%s\nfalse\n" % (resource_id, node_id)
        self._perform_cmd(cmd)


    # Param `resource_xml` is instance of ET.Element.
    def remove_resource(self, resource_xml):
        cmd = "cib_delete\nresources\n" + ET.tostring(resource_xml).replace("\n", "")
        self._perform_cmd(cmd)


    # Param `constraint_xml` is instance of ET.Element.
    def remove_constraint(self, constraint_xml):
        cmd = "cib_delete\nconstraints\n" + ET.tostring(constraint_xml).replace("\n", "")
        self._perform_cmd(cmd)
