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
    GROUP_XPATH = "./configuration/resources/group[@id='%s']"
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
    META_ATTRS_TAG = "meta_attributes"
    INSTANCE_ATTRS_TAG = "instance_attributes"
    ATTR_TAG = "nvpair"
    OPERATIONS_TAG = "operations"
    LOC_CONSTRAINT_TAG = "rsc_location"
    # Target role values.
    STARTED_ROLE = "Started"
    STOPPED_ROLE = "Stopped"


    # Accessory method for _add_meta_attrs_el() and _add_instance_attrs_el().
    @staticmethod
    def _add_attrs_el(parent_el, tag, attrs):
        id = parent_el.get("id") + "-" + tag
        attrs_el = SubEl(parent_el, tag, {"id": id})
        for attr_name, attr_val in attrs.iteritems():
            SubEl(attrs_el, CIB.ATTR_TAG, {"id": id + "-" + attr_name,
                                           "name": attr_name,
                                           "value": attr_val})
        return attrs_el


    @staticmethod
    def _add_meta_attrs_el(parent_el, started):
        role = CIB.STARTED_ROLE if (started) else CIB.STOPPED_ROLE
        return CIB._add_attrs_el(parent_el, CIB.META_ATTRS_TAG, {"target-role": role})


    @staticmethod
    def _add_instance_attrs_el(parent_el, attrs):
        return CIB._add_attrs_el(parent_el, CIB.INSTANCE_ATTRS_TAG, attrs)


    @staticmethod
    def _add_resource_el(parent_el, id, cls, provider, type, started, attrs=None):
        resource_el = SubEl(parent_el, "primitive", {"id": id,
                                                     "class": cls,
                                                     "provider": provider,
                                                     "type": type})
        CIB._add_meta_attrs_el(parent_el=resource_el, started=started)
        if (attrs is not None):
            CIB._add_instance_attrs_el(parent_el=resource_el, attrs=attrs)


    @staticmethod
    def _get_group_children_qty(group_xml):
        children_qty = 0
        for sub_xml in group_xml:
            if (CIB.RESOURCE_TAG == sub_xml.tag):
                children_qty += 1
        return children_qty


    # Returns group element or None if this is root resource.
    @staticmethod
    def _get_group_of_resource(resources_xml, resource_xml):
        if (resource_xml in resources_xml):
            return None
        return resources_xml.find("./group/primitive[@id='%s']/.." % (resource_xml.get("id")))



    def _get_resources_el(self):
        return self._cib_xml.find(CIB.RESOURCES_XPATH)


    def get_attr_val(self, resource_id, attr_name):
        XPATH = "./configuration/resources//*[@id='%s']/instance_attributes/nvpair[@name='%s']"
        return self._cib_xml.find(XPATH % (resource_id, attr_name)).get("value")


    def __init__(self, host):
        self._communicator = Communicator()
        self._communicator.connect(host=host)
        self._cib_xml = None


    def update(self):
        self._cib_xml = self._communicator.get_cib()


    # Returns list of names.
    def get_nodes(self):
        return [n.get("id") for n in self._cib_xml.findall(CIB.ALL_NODES_XPATH)]


    def get_node_state(self, node_id):
        return self._communicator.get_node_state(node_id)


    def enable_standby_mode(self, node_id):
        self._communicator.enable_standby_mode(node_id)

    def cancel_standby_mode(self, node_id):
        self._communicator.cancel_standby_mode(node_id)


    # Returns list of names.
    def get_root_resources(self):
        return [r.get("id") for r in self._cib_xml.findall(CIB.ALL_ROOT_RESOURCES_XPATH)]


    # Returns list of ids.
    def get_children(self, group_id):
        xpath = "./configuration/resources/group[@id='%s']/primitive" % (group_id)
        resources_xml = self._cib_xml.findall(xpath)
        return [res.get("id") for res in resources_xml]


    def create_vm(self, id, conf_file_path):
        resources_el = self._get_resources_el()
        CIB._add_resource_el(parent_el=resources_el,
                             id=id,
                             cls="ocf",
                             provider="pacemaker",
                             type="VirtualDomain",
                             started=True,
                             attrs={
                                 "config": conf_file_path,
                                 "hypervisor": "qemu:///system"})
        self._communicator.modify(resources_el)


    def create_dummy(self, id, started):
        resources_el = self._get_resources_el()
        CIB._add_resource_el(parent_el=resources_el,
                             id=id,
                             cls="ocf",
                             provider="pacemaker",
                             type="Dummy",
                             started=started)
        self._communicator.modify(resources_xml)


    def create_group(self, id, children_ids, started):
        resources_el = self._get_resources_el()
        group_el = SubEl(parent_el, CIB.GROUP_TAG, {"id": id})
        CIB._add_meta_attrs_el(group_el, started)

        # TODO: do something with remove stuff.
        for child_id in children_ids:
            child_el = self._cib_xml.find(CIB.RESOURCE_XPATH % (child_id))
            if (child_xml is None):
                continue
            resources_el.remove(child_el)
            group_el.append(child_el)

        self._communicator.modify(resources_el)


    # Returns None in case of fail.
    def get_resource_type(self, resource_id):
        resource_xml = self._cib_xml.find(CIB.RESOURCE_XPATH % (resource_id))
        if (resource_xml is None):
            return None

        if ("group" == resource_xml.tag):
            return const.resource_type.GROUP
        elif ("primitive" == resource_xml.tag):
            # TODO: govnocode.
            primitive_type = resource_xml.get("type")
            if ("IPaddr" == primitive_type):
                return const.resource_type.IP
            elif ("VirtualDomain" == primitive_type):
                return const.resource_type.VM
            elif ("Dummy" == primitive_type):
                return const.resource_type.DUMMY
        else:
            return None


    # Do not use for groups!
    def get_resource_state(self, resource_id):
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


    # Do not use for groups.
    def get_resource_nodes(self, resource_id):
        return self._communicator.get_resource_nodes(resource_id)


    def _modify_target_role(self, resource_id, target_role):
        resource_type = self.get_resource_type(resource_id)
        # Update group's children.
        if (const.resource_type.GROUP == resource_type):
            for child_id in self.get_children(resource_id):
                self._communicator.modify_attr(child_id, "target-role", target_role)
        self._communicator.modify_attr(resource_id, "target-role", target_role)

    def start(self, resource_id):
        self._modify_target_role(resource_id, CIB.STARTED_ROLE)

    def stop(self, resource_id):
        self._modify_target_role(resource_id, CIB.STOPPED_ROLE)


    def manage(self, resource_id):
        self._communicator.modify_attr(resource_id, "is-managed", "true")

    def unmanage(self, resource_id):
        self._communicator.modify_attr(resource_id, "is-managed", "false")

    def migrate_resource(self, resource_id, node_id):
        self.remove_loc_constraints(resource_id)
        self._communicator.migrate_resource(resource_id, node_id)

    def get_loc_constraints(self, id):
        """ Returns nodes list. """
        nodes_ids = []
        for constr_xml in self._cib_xml.findall(CIB.LOC_CONSTRAINT_XPATH % (id)):
            node_id = constr_xml.get("node")
            if (node_id is None):
                expr_xml = constr_xml.find("./rule/expression")
                if (expr_xml is None) or (expr_xml.get("value") is None):
                    continue
                nodes_ids.append(expr_xml.get("value"))
            else:
                nodes_ids.append(node_id)
        return nodes_ids

    def create_loc_constraint(self, resource_id, node_id):
        self.remove_loc_constraints(resource_id)
        constraints_xml = self._cib_xml.find(CIB.CONSTRAINTS_XPATH)
        attrs = {"rsc": resource_id,
                 "node": node_id,
                 "score": "+INFINITY",
                 "id": "%s-location" % (resource_id)}
        SubEl(constraints_xml, CIB.LOC_CONSTRAINT_TAG, attrs)
        self._communicator.modify(constraints_xml)

    def remove_loc_constraints(self, id):
        """ Remove all location constraints of the resource. """
        constraints_xml = self._cib_xml.find(CIB.CONSTRAINTS_XPATH)
        for constr_xml in self._cib_xml.findall(CIB.LOC_CONSTRAINT_XPATH % (id)):
            self._communicator.remove_constraint(constr_xml)
            constraints_xml.remove(constr_xml)

    def cleanup(self, resource_id):
        nodes_ids = self.get_nodes()
        for node_id in nodes_ids:
            self._communicator.cleanup(resource_id, node_id)


    def set_group(self, resource_id, group_id):
        resources_xml = self._cib_xml.find(CIB.RESOURCES_XPATH)
        resource_xml = self._cib_xml.find(CIB.RESOURCE_XPATH % (resource_id))
        target_group_xml = self._cib_xml.find(CIB.GROUP_XPATH % (group_id))

        current_group_xml = CIB._get_group_of_resource(resources_xml, resource_xml)
        if (current_group_xml is None):
            resources_xml.remove(resource_xml)
        else:
            current_group_xml.remove(resource_xml)
            # Remove the group if necessary.
            if (0 == CIB._get_group_children_qty(current_group_xml)):
                resources_xml.remove(current_group_xml)

        target_group_xml.append(resource_xml)
        self._communicator.modify(resources_xml)


    def move_to_root(self, resource_id):
        resources_xml = self._cib_xml.find(CIB.RESOURCES_XPATH)
        resource_xml = self._cib_xml.find(CIB.RESOURCE_XPATH % (resource_id))
        group_xml = CIB._get_group_of_resource(resources_xml, resource_xml)
        if (group_xml is None):
            return

        # Move the resource to the root.
        group_xml.remove(resource_xml)
        resources_xml.append(resource_xml)
        # Remove the group if necessary.
        if (0 == CIB._get_group_children_qty(group_xml)):
            resources_xml.remove(group_xml)
        # Save.
        self._communicator.modify(resources_xml)


    # Send remove command via self._communicator and delete element from CIB.
    def remove_resource(self, resource_id):
        resources_xml = self._cib_xml.find(CIB.RESOURCES_XPATH)
        resource_xml = self._cib_xml.find(CIB.RESOURCE_XPATH % (resource_id))
        if (resource_xml is None):
            return

        # Process group.
        if (CIB.GROUP_TAG == resource_xml.tag):
            self._communicator.remove_resource(resource_xml)
            resources_xml.remove(resource_xml)
        # Process primitive resource.
        else:
            group_xml = CIB._get_group_of_resource(resources_xml, resource_xml)
            # Process root primitive resource.
            if (group_xml is None):
                self._communicator.remove_resource(resource_xml)
                resources_xml.remove(resource_xml)
            # Process child primitive resource.
            else:
                if (1 == CIB._get_group_children_qty(group_xml)):
                    self._communicator.remove_resource(group_xml)
                    resources_xml.remove(group_xml)
                else:
                    self._communicator.remove_resource(resource_xml)
                    group_xml.remove(resource_xml)
