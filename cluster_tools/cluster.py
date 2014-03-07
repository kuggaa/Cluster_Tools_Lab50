import const
from cib import CIB

import socket
import subprocess


class Node(object):
    def __init__(self, node_id, cib):
        self._cib = cib
        self.id = node_id
        self.state = cib.get_node_state(node_id)
        if (const.node_state.OFF == self.state):
            self.ip = None
        else:
            # TODO: hmmmmmmmmmmmmmmmmmmmmmm...
            self.ip = socket.gethostbyname(self.id)


    def enable_standby_mode(self):
        self._cib.enable_standby_mode(self.id)
    def cancel_standby_mode(self):
        self._cib.cancel_standby_mode(self.id)


    def __str__(self):
        return "[%s] %s" % (const.node_state.to_str(self.state), self.id)
    def __repr__(self):
        return self.__str__()


class BaseResource(object):
    def start(self):
        self._cib.start(self.id)

    def stop(self):
        self._cib.stop(self.id)

    def manage(self):
        self._cib.manage(self.id)

    def unmanage(self):
        self._cib.unmanage(self.id)

    def migrate(self, node):
        self._cib.migrate_resource(self.id, node.id)

    def get_loc_constraints(self):
        return self._cib.get_loc_constraints(self.id)

    def create_loc_constraint(self, node):
        self._cib.create_loc_constraint(self.id, node.id)

    def remove_loc_constraints(self):
        self._cib.remove_loc_constraints_by_resource(self.id)


class PrimitiveResource(BaseResource):
    def __init__(self, resource_id, resource_type, cib):
        self._cib = cib
        self.id = resource_id
        self.type = resource_type
        self.state = cib.get_primitive_resource_state(self.id)
        self.nodes_ids = []
        if (const.resource_state.ON == self.state):
            self.nodes_ids = [cib.get_resource_node(self.id)]


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
        if (len(err) > 0):
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
        states_priority = [const.resource_state.ON,
                           const.resource_state.STARTING,
                           const.resource_state.STOPPING,
                           const.resource_state.FAILED,
                           const.resource_state.UNMANAGED]
        for state in states_priority:
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

    def set_running_state(self, resource_is_running):
        for resource in self._resources.values():
            if (const.resource_state.NO_MONITORING == resource.state):
                continue
            resource.set_running_state(resource_is_running)


    def cleanup(self):
        for resource in self._resources.values():
            resource.cleanup()


class Clone(BaseResource):
    def __init__(self, clone_id, cib, nodes):
        self._cib = cib
        self.id = clone_id
        self.type = const.resource_type.CLONE
        self.children_type = cib.get_clone_type(self.id)

        children = {}
        for child_id in cib.get_clone_children(self.id):
            children[child_id] = build_primitive_resource(child_id, self.children_type, cib)
        self.state = self._get_state(children)

        self.nodes_ids = []
        for child in children.values():
            for node_id in child.nodes_ids:
                if (node_id not in self.nodes_ids):
                    self.nodes_ids.append(node_id)

        self.failed_nodes_ids = []
        for node in nodes.values():
            if node.id not in self.nodes_ids:
                self.failed_nodes_ids.append(node.id)

        # TODO: get rid of it.
        self.node_id = None


    def _get_state(self, children):
        states_priority = [const.resource_state.ON,
                           const.resource_state.STARTING,
                           const.resource_state.STOPPING,
                           const.resource_state.FAILED,
                           const.resource_state.UNMANAGED]
        for state in states_priority:
            for child in children.values():
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

    def set_running_state(self, resource_is_running):
        for resource in self._resources.values():
            if (const.resource_state.NO_MONITORING == resource.state):
                continue
            resource.set_running_state(resource_is_running)


    def cleanup(self):
        for resource in self._resources.values():
            resource.cleanup()


def build_primitive_resource(resource_id, resource_type, cib):
    if (const.resource_type.VM == resource_type):
        return VM(resource_id, cib)
    else:
        return PrimitiveResource(resource_id, resource_type, cib)    


def build_resource(resource_id, cib, nodes):
    resource_type = cib.get_resource_type(resource_id)
    if (const.resource_type.GROUP == resource_type):
        return Group(resource_id, cib)
    elif (const.resource_type.CLONE == resource_type):
        return Clone(resource_id, cib, nodes)
    else:
        return build_primitive_resource(resource_id, resource_type, cib)


class Cluster(object):
    def __init__(self, host, login, password):
        self._cib = CIB(host, login, password)


    def update(self):
        self._cib.update()

        nodes = {}
        for node_id in self._cib.get_nodes_ids():
            nodes[node_id] = Node(node_id, self._cib)
        self._nodes = nodes

        resources = {}
        resources_ids = self._cib.get_root_resources_ids()
        for resource_id in resources_ids:
            resources[resource_id] = build_resource(resource_id, self._cib, self._nodes)
        self._resources = resources


    def get_nodes(self):
        for node in self._nodes.values():
            yield node


    def get_node(self, node_id):
        return self._nodes.get(node_id, None)


    def get_resources(self):
        for resource in self._resources.values():
            yield resource


    def get_resource(self, resource_id):
        """ Returns None in case of fail. """
        resource = self._resources.get(resource_id, None)
        if (resource is not None):
            return resource

        # Search in groups.
        for resource in self._resources.values():
            if (const.resource_type.GROUP == resource.type):
                child_resource = resource.get_resource(resource_id)
                if (child_resource is not None):
                    return child_resource
        return None

    def create_vm(self, id, conf_file_path):
        self._cib.create_vm(id, conf_file_path)

    def create_dummy(self, id, started=True):
        self._cib.create_dummy(id, started)

    def create_group(self, group_id, children_ids, started=True):
        self._cib.create_group(group_id, children_ids, started)

    def move_resources_to_group(self, group_id, resources_ids):
        self._cib.move_resources_to_group(group_id, resources_ids)
