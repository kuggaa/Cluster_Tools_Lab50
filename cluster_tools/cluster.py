import const
from cib import CIB
from node import Node

import subprocess
from cluster_tools import process


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
        if (self.state not in [const.resource_state.OFF, const.resource_state.UNMANAGED]):
            self._cib.stop(self.id)

    def manage(self):
        if (const.resource_state.UNMANAGED == self.state):
            self._cib.manage(self.id)

    def unmanage(self):
        if (const.resource_state.UNMANAGED != self.state):
            self._cib.unmanage(self.id)

    #def migrate(self, node):
    #    if (0 == len(self.get_loc_constraints())):
    #        self._cib.migrate_resource(self.id, node.id)

    def get_loc_constraints(self):
        return self._cib.get_loc_constraints(self.id)

    def remove_loc_constraints(self):
        if (const.resource_state.UNMANAGED != self.state):
            self._cib.remove_loc_constraints_by_resource(self.id)

    def is_group(self):
        return (const.resource_type.GROUP == self.type)

    def is_clone(self):
        return False


class Primitive(BaseResource):
    def __init__(self, id, resource_type, cib, group=None):
        self._cib = cib
        self.id = id
        self.type = resource_type
        self._group = group

        self.state = cib.get_state_of_primitive(self.id)
        self.nodes_ids = []
        if (const.resource_state.ON == self.state):
            self.nodes_ids = [cib.get_location_of_primitive(self.id)]

    def get_raw_type(self):
        return CIB.get_raw_type(self.type)

    def create_loc_constraint(self, node):
        if (self._group is None) or (0 == len(self._group.get_loc_constraints())):
            if (const.resource_state.UNMANAGED != self.state):
                self._cib.create_loc_constraint(self.id, node.id)

    def cleanup(self):
        self._cib.cleanup(self.id)

    def set_group(self, group):
        self._cib.set_group(self.id, group.id)

    def move_to_root(self):
        self._cib.move_to_root(self.id)

    def is_fails_overflow(self, node):
        return self._cib.is_fails_overflow(self.id, node.id)

    def remove(self):
        self._cib.remove_primitive_resource(self.id)

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
        children_ids = cib.get_group_children(self.id)
        for child_id in children_ids:
            resource_type = cib.get_resource_type(child_id)
            self._resources[child_id] = Primitive(child_id,
                                                  resource_type,
                                                  cib,
                                                  self)

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


    def get_children(self):
        return self._resources.values()

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

    def create_loc_constraint(self, node):
        if (const.resource_state.UNMANAGED != self.state):
            for child in self._resources.values():
                child.remove_loc_constraints()
            self._cib.create_loc_constraint(self.id, node.id)

    def cleanup(self):
        for child in self._resources.values():
            child.cleanup()

    def is_fails_overflow(self, node):
        for resource in self._resources.values():
            if (resource.is_fails_overflow(node)):
                return True
        return False


class BaseClone(object):
    def is_group(self):
        return False
    def is_clone(self):
        return True


class ClonedPrimitive(BaseClone):
    def __init__(self,
                 id,
                 type_of_produced_primitives,
                 cib,
                 nodes,
                 ids_of_produced_primitives=None):
        self._cib = cib
        self.id = id
        self.type = const.resource_type.CLONE
        self.type_of_cloned_resource = type_of_produced_primitives
        if (ids_of_produced_primitives is None):
            ids_of_produced_primitives = cib.get_produced_resources(id)
        self._ids_of_produced_primitives = ids_of_produced_primitives

        # Calculate `self.state`.
        states = {}
        for produced_primitive_id in self._ids_of_produced_primitives:
            states[produced_primitive_id] = cib.get_state_of_primitive(produced_primitive_id)
        self.state = self._get_state(states)

        # Build `self.nodes_ids` and `self.failed_nodes_ids`.
        self.nodes_ids = []
        self.failed_nodes_ids = []
        if (const.resource_state.UNMANAGED != self.state):
            for produced_primitive_id, state in states.iteritems():
                if (const.resource_state.ON == state):
                    self.nodes_ids.append(cib.get_location_of_primitive(produced_primitive_id))
            self.failed_nodes_ids = [n.id for n in nodes.values() if (n.id not in self.nodes_ids)]


    def _get_state(self, states):
        for state in STATES_PRIORITY:
            for clone_state in states.values():
                if (state == clone_state):
                    return state
        return const.resource_state.OFF


    def cleanup(self):
        self._cib.cleanup(self.id)


    def is_fails_overflow(self, node):
        for produced_primitive_id in self._ids_of_produced_primitives:
            if (self._cib.is_fails_overflow(produced_primitive_id, node.id)):
                return True
        return False


class ClonedGroup(BaseClone):
    def __init__(self, id, cib, nodes):
        self._cib = cib
        self.id = id
        self.type = const.resource_type.CLONE
        self.type_of_cloned_resource = const.resource_type.GROUP

        indexes = []
        for produced_group_id in cib.get_produced_resources(self.id):
            id, index = produced_group_id.split(":")
            indexes.append(index)

        # Build list of children and calculate state.
        self.children = []
        for child_id in cib.get_children_of_cloned_group(self.id):
            resource_type = cib.get_resource_type(child_id)
            self.children.append(ClonedPrimitive(child_id,
                                                 resource_type,
                                                 cib,
                                                 nodes,
                                                 [child_id + ":" + i for i in indexes]))
        self.state = self._get_state()
        self.nodes_ids = []


    def _get_state(self):
        for state in STATES_PRIORITY:
            for child in self.children:
                if (state == child.state):
                    return state
        return const.resource_state.OFF

    def get_children(self):
        return self.children

    def cleanup(self):
        self._cib.cleanup(self.id)

    def is_fails_overflow(self, node):
        for child in self.children:
            if (child.is_fails_overflow(node)):
                return True
        return False


class Cluster(object):
    def __init__(self, host, login, password, devices_rep):
        self._cib = CIB(host, login, password)
        self._devices_rep = devices_rep
        self.update()


    def get_nodes(self):
        for node in self._nodes.values():
            yield node

    def get_node(self, id):
        return self._nodes.get(id, None)


    def _build_resource(self, id, cib, nodes):
        """ Build any resource: group, clone or primitive. """
        resource_type = cib.get_resource_type(id)
        if (resource_type is None):
            return None
        elif (const.resource_type.GROUP == resource_type):
            return Group(id, cib)
        elif (const.resource_type.CLONE == resource_type):
            type_of_produced_resources = cib.get_clone_type(id)
            if (const.resource_type.GROUP == type_of_produced_resources):
                return ClonedGroup(id, cib, nodes)
            else:
                return ClonedPrimitive(id, type_of_produced_resources, cib, nodes)
        else:
            group_id = cib.get_group_by_primitive(id)
            if (group_id is None):
                return Primitive(id, resource_type, cib)
            else:
                if (self._groups.get(group_id) is None):
                    self._groups[group_id] = Group(group_id, cib)
                return self._groups[group_id].get_resource(id)


    def get_resources(self):
        resources_ids = self._cib.get_root_resources_ids()
        for resource_id in resources_ids:
            res = self._build_resource(resource_id, self._cib, self._nodes)
            if (res is not None):
                yield res

    def get_resource(self, id):
        return self._build_resource(id, self._cib, self._nodes)

    def get_primitives(self, primitive_type):
        primitives = []
        for res in self.get_resources():
            if (res.type == primitive_type):
                primitives.append(res)
            elif (res.is_group()):
                for child_res in res.get_children():
                    if (child_res.type == primitive_type):
                        primitives.append(child_res)
        return primitives


    def update(self):
        self._cib.update()
        nodes = {}
        for node_id in self._cib.get_nodes_ids():
            nodes[node_id] = Node(node_id, self._cib, self._devices_rep)
        self._nodes = nodes
        self._groups = {}


    def create_vm(self, id, conf_file_path):
        self._cib.create_vm(id, conf_file_path)

    def create_dummy(self, id, started=True):
        self._cib.create_dummy(id, started)

    def create_group(self, group_id, children_ids, started=True):
        self._cib.create_group(group_id, children_ids, started)
