import const
from cib import CIB
import socket


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
        self._cib.remove_loc_constraints(self.id)

    def remove(self):
        self._cib.remove_resource(self.id)


class Resource(BaseResource):
    def __init__(self, resource_id, resource_type, cib):
        self._cib = cib
        self.id = resource_id
        self.type = resource_type
        self.state = cib.get_resource_state(self.id)
        if (const.resource_state.ON == self.state):
            self.nodes_ids = cib.get_resource_nodes(self.id)
        else:
            self.nodes_ids = []
  

    def cleanup(self):
        self._cib.cleanup(self.id)

    def set_group(self, group):
        self._cib.set_group(self.id, group.id)

    def move_to_root(self):
        self._cib.move_to_root(self.id)

    def __str__(self):
        return "Resource " + self.id
    def __repr__(self):
        return "Resource " + self.id


class Group(BaseResource):
    def __init__(self, group_id, cib):
        self._cib = cib
        self.id = group_id
        self.type = const.resource_type.GROUP

        self._resources = {}
        children_ids = cib.get_children(self.id)
        for child_id in children_ids:
            child_type = cib.get_resource_type(child_id)
            self._resources[child_id] = Resource(child_id, child_type, cib)

        self.state = self._get_state()


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


def build_resource(resource_id, cib):
    resource_type = cib.get_resource_type(resource_id)
    if (const.resource_type.GROUP == resource_type):
        return Group(resource_id, cib)
    else:
        return Resource(resource_id, resource_type, cib)


class Cluster(object):
    def __init__(self, host):
        self._cib = CIB(host)


    def update(self):
        self._cib.update()

        nodes = {}
        nodes_ids = self._cib.get_nodes()
        for node_id in nodes_ids:
            nodes[node_id] = Node(node_id, self._cib)
        self._nodes = nodes

        resources = {}
        resources_ids = self._cib.get_root_resources()
        for resource_id in resources_ids:
            resources[resource_id] = build_resource(resource_id, self._cib)
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


    def create_dummy(self, id, started=True):
        self._cib.create_dummy(id, started)

    def create_group(self, group_id, children_ids, started=True):
        self._cib.create_group(group_id, children_ids, started)

    def move_resources_to_group(self, group_id, resources_ids):
        self._cib.move_resources_to_group(group_id, resources_ids)
