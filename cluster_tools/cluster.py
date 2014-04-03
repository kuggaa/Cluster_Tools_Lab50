import const
from cib import CIB
from exceptions import DeviceError

import socket
import subprocess
import time


class Node(object):
    def __init__(self, id, cib, devices_rep):
        self.id = id
        self._cib = cib
        self._devices_rep = devices_rep

        self.state = cib.get_node_state(id)
        if (const.node_state.OFF == self.state):
            self.ip = None
        else:
            # TODO: hmmmmmmmmmmmmmmmmmmmmmm...
            self.ip = socket.gethostbyname(self.id)


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


STATES_PRIORITY = [const.resource_state.ON,
                   const.resource_state.STARTING,
                   const.resource_state.STOPPING,
                   const.resource_state.FAILED,
                   const.resource_state.UNMANAGED]


class BaseResource(object):
    def start(self):
        if (const.resource_state.OFF == self.state):
            self._cib.start(self.id)

    def stop(self):
        if (const.resource_state.OFF != self.state):
            self._cib.stop(self.id)

    def manage(self):
        if (const.resource_state.UNMANAGED == self.state):
            self._cib.manage(self.id)

    def unmanage(self):
        if (const.resource_state.UNMANAGED != self.state):
            self._cib.unmanage(self.id)

    def migrate(self, node):
        self._cib.migrate_resource(self.id, node.id)

    def get_loc_constraints(self):
        return self._cib.get_loc_constraints(self.id)

    def create_loc_constraint(self, node):
        self._cib.create_loc_constraint(self.id, node.id)

    def remove_loc_constraints(self):
        self._cib.remove_loc_constraints_by_resource(self.id)

    def is_group(self):
        return (const.resource_type.GROUP == self.type)

    def is_clone(self):
        return (const.resource_type.CLONE == self.type)


class PrimitiveResource(BaseResource):
    def __init__(self, resource_id, resource_type, cib):
        self._cib = cib
        self.id = resource_id
        self.type = resource_type
        self.state = cib.get_primitive_resource_state(self.id)
        self.nodes_ids = []
        if (const.resource_state.ON == self.state):
            self.nodes_ids = [cib.get_resource_node(self.id)]

    def get_raw_type(self):
        for raw_type, type in CIB.RAW_TYPES.iteritems():
            if (type == self.type):
                return raw_type
        return None

    def cleanup(self):
        self._cib.cleanup(self.id)

    def set_group(self, group):
        self._cib.set_group(self.id, group.id)

    def move_to_root(self):
        self._cib.move_to_root(self.id)

    def remove(self):
        self._cib.remove_primitive_resource(self.id)

    def __str__(self):
        return "Resource " + self.id
    def __repr__(self):
        return "Resource " + self.id


class VM(PrimitiveResource):
    def __init__(self, resource_id, cib):
        PrimitiveResource.__init__(self, resource_id, const.resource_type.VM, cib)


    def get_vnc_id(self):
        if (1 != len(self.nodes_ids)):
            raise "OLOLO"
        p = subprocess.Popen(args=["virsh",
                                   "-c",
                                   "qemu+tcp://%s/system" % (self.nodes_ids[0]),
                                   "vncdisplay",
                                   self.id],
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        out, err = p.communicate()
        if (0 != p.returncode):
            return None
        return int(out.strip().replace(":", ""))


class Group(BaseResource):
    def __init__(self, group_id, cib):
        self._cib = cib
        self.id = group_id
        self.type = const.resource_type.GROUP

        self._resources = {}
        children_ids = cib.get_group_children(self.id)
        for child_id in children_ids:
            resource_type = cib.get_resource_type(child_id)
            self._resources[child_id] = build_primitive_resource(child_id, resource_type, cib)

        self.state = self._get_state()
        self.nodes_ids = []
        for child in self._resources.values():
            if (len(child.nodes_ids) > 0):
                self.nodes_ids.append(child.nodes_ids[0])
                break


    # TODO: it can be done with 2 passes.
    def _get_state(self):
        for state in STATES_PRIORITY:
            for child in self._resources.values():
                if (state == child.state):
                    return state
        return const.resource_state.OFF


    def get_resources(self):
        for resource in self._resources.values():
            yield resource

    def get_resource(self, resource_id):
        return self._resources.get(resource_id, None)

    def get_resources_qty(self):
        return len(self._resources)

    def check_vm_childs(self):
        if len(self._resources) == 0:
            return False
        else:
            return self._resources.values()[0].type == const.resource_type.VM

    def set_running_state(self, resource_is_running):
        for resource in self._resources.values():
            if (const.resource_state.NO_MONITORING == resource.state):
                continue
            resource.set_running_state(resource_is_running)


    def cleanup(self):
        for resource in self._resources.values():
            resource.cleanup()


class BaseClone(object):
    pass


class ClonedPrimitive(BaseClone):
    def __init__(self, clone_id, type_of_cloned_resource, cib, nodes):
        self._cib = cib
        self.id = clone_id
        self.type = const.resource_type.CLONE
        self.type_of_cloned_resource = type_of_cloned_resource

        children = {}
        for child_id in cib.get_clone_children(self.id):
            children[child_id] = build_primitive_resource(child_id,
                                                          self.type_of_cloned_resource,
                                                          cib)
        self.state = self._get_state(children)

        self.nodes_ids = []
        for child in children.values():
            for node_id in child.nodes_ids:
                if (node_id not in self.nodes_ids):
                    self.nodes_ids.append(node_id)

        self.failed_nodes_ids = [n.id for n in nodes.values() if (n.id not in self.nodes_ids)]


    def _get_state(self, children):
        for state in STATES_PRIORITY:
            for child in children.values():
                if (state == child.state):
                    return state
        return const.resource_state.OFF


class ChildOfClonedGroup(object):
    def __init__(self, id, cib, nodes, indexes_of_cloned_groups):
        self.id = id
        self.type = cib.get_resource_type(self.id)

        states = {}
        for ind in indexes_of_cloned_groups:
            cloned_child_id = self.id + ":" + ind
            state = cib.get_primitive_resource_state(cloned_child_id)
            states[cloned_child_id] = state
        self.state = self._get_state(states)

        self.nodes_ids = []
        for cloned_child_id, state in states.iteritems():
            if (const.resource_state.ON == state):
                self.nodes_ids.append(cib.get_resource_node(cloned_child_id))
        self.failed_nodes_ids = [n.id for n in nodes.values() if (n.id not in self.nodes_ids)]


    def _get_state(self, states):
        for state in STATES_PRIORITY:
            for clone_state in states.values():
                if (state == clone_state):
                    return state
        return const.resource_state.OFF


class ClonedGroup(BaseClone):
    def __init__(self, clone_id, cib, nodes):
        self._cib = cib
        self.id = clone_id
        self.type = const.resource_type.CLONE
        self.type_of_cloned_resource = const.resource_type.GROUP

        indexes_of_cloned_groups = []
        for cloned_group_id in cib.get_clone_children(self.id):
            id, index = cloned_group_id.split(":")
            indexes_of_cloned_groups.append(index)

        self.children = []
        for id in cib.get_children_of_cloned_group(self.id):
            self.children.append(ChildOfClonedGroup(id,
                                                    cib,
                                                    nodes,
                                                    indexes_of_cloned_groups))

        self.state = self._get_state()


    def _get_state(self):
        for state in STATES_PRIORITY:
            for child in self.children:
                if (state == child.state):
                    return state
        return const.resource_state.OFF


def build_primitive_resource(resource_id, resource_type, cib):
    if (const.resource_type.VM == resource_type):
        return VM(resource_id, cib)
    else:
        return PrimitiveResource(resource_id, resource_type, cib)


def build_resource(id, cib, nodes):
    """ Build any resource: group, clone or primitive. """
    resource_type = cib.get_resource_type(id)
    if (resource_type is None):
        return None
    elif (const.resource_type.GROUP == resource_type):
        return Group(id, cib)
    elif (const.resource_type.CLONE == resource_type):
        type_of_cloned_resource = cib.get_clone_type(id)
        if (const.resource_type.GROUP == type_of_cloned_resource):
            return ClonedGroup(id, cib, nodes)
        else:
            return ClonedPrimitive(id, type_of_cloned_resource, cib, nodes)
    else:
        return build_primitive_resource(id, resource_type, cib)


class Cluster(object):
    def __init__(self, host, login, password, devices_rep):
        self._cib = CIB(host, login, password)
        self._cib.update()

        nodes = {}
        for node_id in self._cib.get_nodes_ids():
            nodes[node_id] = Node(node_id, self._cib, devices_rep)
        self._nodes = nodes


    def get_nodes(self):
        for node in self._nodes.values():
            yield node

    def get_node(self, id):
        return self._nodes.get(id, None)


    def get_resources(self):
        resources_ids = self._cib.get_root_resources_ids()
        for resource_id in resources_ids:
            res = build_resource(resource_id, self._cib, self._nodes)
            if (res is not None):
                yield res

    def get_resource(self, id):
        return build_resource(id, self._cib, self._nodes)


    def update(self):
        pass


    def create_vm(self, id, conf_file_path):
        self._cib.create_vm(id, conf_file_path)

    def create_dummy(self, id, started=True):
        self._cib.create_dummy(id, started)

    def create_group(self, group_id, children_ids, started=True):
        self._cib.create_group(group_id, children_ids, started)
