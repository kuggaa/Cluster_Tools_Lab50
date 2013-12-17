import const
from communicator import Communicator
from xml.etree.ElementTree import SubElement as SubEl


# Cluster Information Base.
class CIB(object):
    # Xpaths wrt cib element.
    ALL_NODES_XPATH = "./configuration/nodes/node"
    ALL_ROOT_RESOURCES_XPATH = "./configuration/resources/*"
    RESOURCES_XPATH = "./configuration/resources"
    RESOURCE_XPATH = "./configuration/resources//*[@id='%s']"
    ALL_RESOURCE_ONGOING_OPS_XPATH = "./status/node_state/lrm/lrm_resources/lrm_resource[@id='%s']/lrm_rsc_op[@op-status='-1']"
    CONSTRAINTS_XPATH = "./configuration/constraints"
    LOC_CONSTRAINT_XPATH = "./configuration/constraints/rsc_location[@rsc='%s']"
    # Xpaths wrt resource element.
    ATTRS_XPATH = "./meta_attributes"
    TARGET_ROLE_ATTR_XPATH = "./meta_attributes/nvpair[@name='target-role']"
    IS_MANAGED_ATTR_XPATH = "./meta_attributes/nvpair[@name='is-managed']"
    # Tags.
    RESOURCE_TAG = "primitive"
    GROUP_TAG = "group"
    ATTRS_TAG = "meta_attributes"
    ATTR_TAG = "nvpair"
    OPERATIONS_TAG = "operations"
    LOC_CONSTRAINT_TAG = "rsc_location"
    # Target role values.
    STARTED_ROLE = "Started"
    STOPPED_ROLE = "Stopped"


    @staticmethod
    def _set_target_role_attr(resource_xml, val):
        attr_xml = resource_xml.find(CIB.TARGET_ROLE_ATTR_XPATH)
        if (attr_xml is None):
            attrs_xml = resource_xml.find(CIB.ATTRS_XPATH)
            assert(attrs_xml is not None, "WTF? Where is meta_attributes element?")
            attr_xml = SubEl(attrs_xml, CIB.ATTR_TAG, {"name": "target-role"})
            attr_xml.set("id", attrs_xml.get("id") + "-target-role")
        attr_xml.set("value", val)


    @staticmethod
    def _remove_target_role_attr(resource_xml):
        attr_xml = resource_xml.find(CIB.TARGET_ROLE_ATTR_XPATH)
        if (attr_xml is not None):
            attrs_xml = resource_xml.find(CIB.ATTRS_XPATH)
            attrs_xml.remove(attr_xml)


    # Creates new child in "cib/configuration/resources" el (param `resources_xml`).
    # Returns created element.
    # It will have 1 child: attributes container.
    # Attributes container will have 1 child: target role,
    # which value depends on param `started`.
    @staticmethod
    def _create_resource(resources_xml, id, tag, started):
        resource_xml = SubEl(resources_xml, tag, {"id": id})
        # Create attributes container.
        attrs_xml = SubEl(resource_xml, CIB.ATTRS_TAG)
        attrs_xml.set("id", "%s-%s" % (id, CIB.ATTRS_TAG))
        # Set target role.
        role_xml = SubEl(attrs_xml, CIB.ATTR_TAG, {"name": "target-role"})
        role_xml.set("id", attrs_xml.get("id") + "-target-role")
        role_xml.set("value", CIB.STARTED_ROLE if (started) else CIB.STOPPED_ROLE)
        return resource_xml


    def __init__(self):
        self._communicator = Communicator()
        self._communicator.connect()
        self._cib_xml = None


    def update(self):
        self._cib_xml = self._communicator.get_cib()


    # Returns list of names.
    def get_nodes(self):
        return [n.get("id") for n in self._cib_xml.findall(CIB.ALL_NODES_XPATH)]


    def get_node_state(self, node_id):
        return self._communicator.get_node_state(node_id)


    def set_standby_mode(self, node_name, standby_mode_enabled):
        self._communicator.set_standby_mode(node_name, standby_mode_enabled)


    # Returns list of names.
    def get_root_resources(self):
        return [r.get("id") for r in self._cib_xml.findall(CIB.ALL_ROOT_RESOURCES_XPATH)]


    # Returns list of ids.
    def get_subresources(self, group_id):
        xpath = "./configuration/resources/group[@id='%s']/primitive" % (group_id)
        resources_xml = self._cib_xml.findall(xpath)
        return [res.get("id") for res in resources_xml]


    def create_dummy(self, id, started):
        resources_xml = self._cib_xml.find(CIB.RESOURCES_XPATH)
        assert(resources_xml is not None)
        resource_xml = CIB._create_resource(resources_xml, id, CIB.RESOURCE_TAG, started)
        resource_xml.set("class", "ocf")
        resource_xml.set("provider", "pacemaker")
        resource_xml.set("type", "Dummy")
        self._communicator.modify(resources_xml)


    def create_group(self, id, children_ids, started):
        resources_xml = self._cib_xml.find(CIB.RESOURCES_XPATH)
        assert(resources_xml is not None)
        group_xml = CIB._create_resource(resources_xml, id, CIB.GROUP_TAG, started)

        # TODO: do something with remove stuff.
        for child_id in children_ids:
            child_xml = self._cib_xml.find(CIB.RESOURCE_XPATH % (child_id))
            if (child_xml is None):
                continue
            resources_xml.remove(child_xml)
            group_xml.append(child_xml)

        self._communicator.modify(resources_xml)


    # Returns None in case of fail.
    def get_resource_type(self, resource_id):
        resource_xml = self._cib_xml.find(CIB.RESOURCE_XPATH % (resource_id))
        if (resource_xml is None):
            return None

        if ("group" == resource_xml.tag):
            return const.resource_type.GROUP
        elif ("primitive" == resource_xml.tag):
            return const.resource_type.DUMMY
        else:
            return None


    # Do not use for groups!
    def get_resource_states(self, resource_id):
        state = self._communicator.get_resource_state(resource_id)
        # Check ongoing operations.
        for op_xml in self._cib_xml.findall(CIB.ALL_RESOURCE_ONGOING_OPS_XPATH % (resource_id)):
            if ("start" == op_xml.get("operation")):
                state = const.resource_state.STARTING
                break
            elif ("stop" == op_xml.get("operation")):
                state = const.resource_state.STOPPING
                break
        return state


    def _modify_target_role(self, resource_id, target_role):
        resource_xml = self._cib_xml.find(CIB.RESOURCE_XPATH % (resource_id))
        if (resource_xml is None):
            return
        if ("group" == resource_xml.tag):
            for child_resource_xml in resource_xml.findall("./" + CIB.RESOURCE_TAG):
                CIB._remove_target_role_attr(child_resource_xml)
        CIB._set_target_role_attr(resource_xml, target_role)
        self._communicator.modify(resource_xml)


    def start(self, resource_id):
        self._modify_target_role(resource_id, "Started")
    def stop(self, resource_id):
        self._modify_target_role(resource_id, "Stopped")


    def manage(self, resource_id):
        self._communicator.modify_managed_attr(resource_id, True)
    def unmanage(self, resource_id):
        self._communicator.modify_managed_attr(resource_id, False)


    def migrate_resource(self, resource_id, node_id):
        self._communicator.migrate_resource(resource_id, node_id)


    # Returns name of node or None.
    def get_priority_node(self, resource_name):
        constraint_xml = self._cib_xml.find(CIB.LOC_CONSTRAINT_XPATH % (resource_name))
        return None if (constraint_xml is None) else constraint_xml.get("node")


    def set_priority_node(self, resource_name, node_name):
        constraint_xml = self._cib_xml.find(CIB.LOC_CONSTRAINT_XPATH % (resource_name))
        if (constraint_xml is not None) and (node_name == constraint_xml.get("node")):
            return

        constraints_xml = self._cib_xml.find(CIB.CONSTRAINTS_XPATH)
        if (constraint_xml is None):
            id = resource_name + "-location"
            attrs = {"rsc": resource_name, "node": node_name, "score": "+INFINITY", "id": id}
            constraint_xml = SubEl(constraints_xml, CIB.LOC_CONSTRAINT_TAG, attrs)
        else:
            constraint_xml.set("node", node_name)
        self._communicator.update_constraints(constraints_xml)


    def unset_priority_node(self, resource_name):
        constraint_xml = self._cib_xml.find(CIB.LOC_CONSTRAINT_XPATH % (resource_name))
        if (constraint_xml is None):
            return

        constraints_xml = self._cib_xml.find(CIB.CONSTRAINTS_XPATH)
        constraints_xml.remove(constraint_xml)
        self._communicator.update_constraints(constraints_xml)


    def cleanup(self, resource_id):
        nodes_ids = self.get_nodes()
        for node_id in nodes_ids:
            self._communicator.cleanup(resource_id, node_id)


    def remove_resource(self, resource_id):
        resource_xml = self._cib_xml.find(CIB.RESOURCE_XPATH % (resource_id))
        if (resource_xml is None):
            return
        self._communicator.remove_resource(resource_xml)
