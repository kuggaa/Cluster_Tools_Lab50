import const
from communicator import Communicator
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import SubElement as SubEl
import process


class LocConstarint(object):
    def __init__(self, node_id, score):
        self.node_id = node_id
        self.score = score

    def isTabu(self):
        return ("-" == self.score[0])


# Cluster Information Base.
class CIB(object):
    VM_TMPL_ID = "vm_template"
    DUMMY_TMPL_ID = "dummy_template"
    # Xpaths wrt cib element.
    NODES_XPATH = "./configuration/nodes"
    RESOURCES_XPATH = "./configuration/resources"
    CONSTRAINTS_XPATH = "./configuration/constraints"
    ALL_RESOURCE_ONGOING_OPS_XPATH = "./status/node_state/lrm/lrm_resources/lrm_resource[@id='%s']/lrm_rsc_op[@op-status='-1']"
    # Tags.
    NODE_TAG = "node"
    PRIMITIVE_RESOURCE_TAG = "primitive"
    GROUP_TAG = "group"
    CLONE_TAG = "clone"
    META_ATTRS_TAG = "meta_attributes"
    INSTANCE_ATTRS_TAG = "instance_attributes"
    ATTR_TAG = "nvpair"
    OPERATIONS_TAG = "operations"
    OPERATION_TAG = "op"
    LOC_CONSTRAINT_TAG = "rsc_location"
    # Target role values.
    STARTED_ROLE = "Started"
    STOPPED_ROLE = "Stopped"

    RAW_TYPES = {"VirtualDomain": const.resource_type.VM,
                 "IPaddr": const.resource_type.IP,
                 "IPaddr2": const.resource_type.IP,
                 "Dummy": const.resource_type.DUMMY,
                 "Filesystem": const.resource_type.FILESYSTEM,
                 "volume": const.resource_type.VOLUME,
                 "glusterd": const.resource_type.GLUSTERD,
                 "external/ipmi": const.resource_type.IPMI,
                 "fence_apc_snmp": const.resource_type.PDU,
                 "apache2": const.resource_type.APACHE,
                 "nslcd": const.resource_type.LDAP_DAEMON,
                 "aldcd": const.resource_type.ALD_CACHE_DAEMON,
                 "krb5-kdc": const.resource_type.KERBEROS_KEY_SERVER,
                 "krb5-prop": const.resource_type.KERBEROS_DB_PROPAGATION,
                 "krb5-admin-server": const.resource_type.KERBEROS_MASTER_SERVER,
                 "aldd": const.resource_type.ALD_DAEMON,
                 "nscd": const.resource_type.NAME_SERVICE_CACHE_DAEMON,
                 "slapd": const.resource_type.OPENLDAP_SERVER}


    # TODO: get rid of cmd.
    @staticmethod
    def get_real_time_state():
        xml_str = process.call(["sudo", "crm_mon", "--as-xml", "--one-shot", "--inactive"])
        return ET.fromstring(xml_str)


    @staticmethod
    def _create_attrs_el(resource_el, tag, attrs):
        id = resource_el.get("id") + "-" + tag
        attrs_el = SubEl(resource_el, tag, {"id": id})
        for attr_name, attr_val in attrs.iteritems():
            SubEl(attrs_el, CIB.ATTR_TAG, {"id": id + "-" + attr_name,
                                           "name": attr_name,
                                           "value": attr_val})
        return attrs_el


    @staticmethod
    def _create_meta_attrs_el(resource_el, attrs):
        return CIB._create_attrs_el(resource_el, tag=CIB.META_ATTRS_TAG, attrs=attrs)


    @staticmethod
    def _create_instance_attrs_el(resource_el, attrs):
        return CIB._create_attrs_el(resource_el, tag=CIB.INSTANCE_ATTRS_TAG, attrs=attrs)


    @staticmethod
    def _create_primitive_resource_el(parent_el, id, tmpl_id, instance_attrs=None):
        """
        Creates a primitive resource element in `parent_el`.
        Param `instance_attrs` is dict.
        """
        resource_el = SubEl(parent_el, "primitive", {"id": id, "template": tmpl_id})
        #CIB._add_meta_attrs_el(resource_el,
        #                       started=started,
        #                       migration_allowed=migration_allowed)
        if (instance_attrs is not None):
            CIB._create_instance_attrs_el(resource_el, attrs=instance_attrs)


    def _get_primitive_resource_el(self, id):
        """ Returns None in case of fail. """
        return self._resources_el.find(".//primitive[@id='%s']" % (id))

    def _get_tmpl_el(self, id):
        """ Returns None in case of fail. """
        return self._resources_el.find("./template[@id='%s']" % (id))

    def _get_group_el(self, id):
        """ Returns None in case of fail. """
        return self._resources_el.find("./group[@id='%s']" % (id))

    def _get_clone_el(self, id):
        """ Returns None in case of fail. """
        return self._resources_el.find("./clone[@id='%s']" % (id))

    def _get_group_el_by_primitive(self, id):
        """ Returns None for a root primitive. """
        return self._resources_el.find("./group/primitive[@id='%s']/.." % (id))

    def _get_loc_contraints_els_by_resource(self, id):
        return self._constraints_el.findall("./rsc_location[@rsc='%s']" % (id))

    def get_attr_val(self, resource_id, attr_name):
        XPATH = "./configuration/resources//*[@id='%s']/instance_attributes/nvpair[@name='%s']"
        return self._cib_el.find(XPATH % (resource_id, attr_name)).get("value")


    @staticmethod
    def _is_last_child(group_el, resource_el):
        if (resource_el not in group_el):
            return False
        return (1 == len(group_el.findall(CIB.PRIMITIVE_RESOURCE_TAG)))


    def __init__(self, host, login, password):
        self._communicator = Communicator()
        self._communicator.connect(host, login, password)
        self._cib_el = None
        self._nodes_el = None
        self._resources_el = None
        self._constraints_el = None


    def update(self):
        self._cib_el = self._communicator.get_cib()
        self._nodes_el = self._cib_el.find(CIB.NODES_XPATH)
        self._resources_el = self._cib_el.find(CIB.RESOURCES_XPATH)
        self._constraints_el = self._cib_el.find(CIB.CONSTRAINTS_XPATH)

        self._state_el = CIB.get_real_time_state()


    def get_nodes_ids(self):
        return [el.get("id") for el in self._nodes_el.findall(CIB.NODE_TAG)]


    def get_state_of_node(self, id):
        node_el = self._state_el.find("./nodes/node[@id='%s']" % (id))
        if ("false" == node_el.get("online")):
            return const.node_state.OFF
        if ("true" == node_el.get("standby")):
            return const.node_state.STANDBY
        return const.node_state.ON

    def is_unclean(self, id):
        node_el = self._state_el.find("./nodes/node[@id='%s']" % (id))
        return ("true" == node_el.get("unclean"))


    def enable_standby_mode(self, node_id):
        self._communicator.enable_standby_mode(node_id)
    def cancel_standby_mode(self, node_id):
        self._communicator.cancel_standby_mode(node_id)


    # Returns list of names.
    def get_root_resources_ids(self):
        groups_els = self._resources_el.findall(CIB.GROUP_TAG)
        primitives_els = self._resources_el.findall(CIB.PRIMITIVE_RESOURCE_TAG)
        clones_els = self._resources_el.findall(CIB.CLONE_TAG)
        return [el.get("id") for el in primitives_els + groups_els + clones_els]


    def get_group_children(self, group_id):
        """ Returns list of ids. """
        group_el = self._get_group_el(group_id)
        return [el.get("id") for el in group_el.findall(CIB.PRIMITIVE_RESOURCE_TAG)]

    def get_group_by_primitive(self, primitive_id):
        """ Returns id of a group (or None for a root primitive). """
        group_el = self._get_group_el_by_primitive(primitive_id)
        return None if (group_el is None) else group_el.get("id")

    def get_children_of_cloned_group(self, clone_id):
        """ Returns list of ids. """
        clone_el = self._get_clone_el(clone_id)
        group_el = clone_el.find(CIB.GROUP_TAG)
        return [el.get("id") for el in group_el.findall(CIB.PRIMITIVE_RESOURCE_TAG)]


    def get_produced_resources(self, clone_id):
        """ Returns list of ids. """
        clone_el = self._state_el.find("./resources/clone[@id='%s']" % (clone_id))
        ids = []
        for produced_resource_el in clone_el:
            ids.append(produced_resource_el.get("id"))
        return ids


    def create_vm(self, id, conf_file_path):
        CIB._create_primitive_resource_el(parent_el=self._resources_el,
                                          id=id,
                                          tmpl_id=CIB.VM_TMPL_ID,
                                          instance_attrs={"config": conf_file_path})
        self._communicator.modify(self._resources_el)


    def create_dummy(self, id, started=True):
        CIB._create_primitive_resource_el(parent_el=self._resources_el,
                                          id=id,
                                          tmpl_id=CIB.DUMMY_TMPL_ID)
        self._communicator.modify(self._resources_el)


    def create_group(self, id, children_ids, started):
        group_el = SubEl(self._resources_el, CIB.GROUP_TAG, {"id": id})
        CIB._create_meta_attrs_el(group_el, attrs={"target-role": CIB.STARTED_ROLE,
                                                    "ordered": "false",
                                                    "collocated": "false"})

        for child_id in children_ids:
            resource_el = self._get_primitive_resource_el(child_id)
            current_group_el = self._get_group_el_by_primitive(child_id)
            if (current_group_el is None):
                self._resources_el.remove(resource_el)
            else:
                if (CIB._is_last_child(current_group_el, resource_el)):
                    self.remove_loc_constraints_by_resource(current_group_el.get("id"))
                    self._resources_el.remove(current_group_el)
                else:
                    current_group_el.remove(resource_el)
            group_el.append(resource_el)

        self._communicator.modify(self._resources_el)


    def is_resource_exists(self, id):
        if (self._get_group_el(id) is not None):
            return True
        if (self._get_clone_el(id) is not None):
            return True
        return (self._get_primitive_resource_el(id) is not None)


    def get_resource_type(self, id):
        """ Returns None in case of fail. """
        if (self._get_group_el(id) is not None):
            return const.resource_type.GROUP
        elif (self._get_clone_el(id) is not None):
            return const.resource_type.CLONE
        
        primitive_resource_el = self._get_primitive_resource_el(id)
        if (primitive_resource_el is None):
            return None
        primitive_type = primitive_resource_el.get("type")
        if (primitive_type is None):
            tmpl_id = primitive_resource_el.get("template")
            if (tmpl_id is None):
                return None
            primitive_type = self._get_tmpl_el(tmpl_id).get("type")

        return CIB.RAW_TYPES.get(primitive_type)


    def get_clone_type(self, id):
        clone_el = self._get_clone_el(id)
        cloned_primitive_el = clone_el.find(CIB.PRIMITIVE_RESOURCE_TAG)
        if (cloned_primitive_el is None):
            return const.resource_type.GROUP
        else:
            return CIB.RAW_TYPES.get(cloned_primitive_el.get("type"))


    def get_state_of_primitive(self, id):
        primitive_el = self._state_el.find("./resources//resource[@id='%s']" % (id))
        if ("false" == primitive_el.get("managed")):
            return const.resource_state.UNMANAGED
        if ("false" == primitive_el.get("active")):
            return const.resource_state.OFF
        if ("true" == primitive_el.get("failed")):
            return const.resource_state.FAILED
        return const.resource_state.ON


    def get_location_of_primitive(self, id):
        """
        Do not use for groups.
        """
        node_el = self._state_el.find("./resources//resource[@id='%s']/node" % (id))
        if (node_el is not None):
            return node_el.get("id")
        else:
            return None


    def _modify_target_role(self, id, target_role):
        resource_type = self.get_resource_type(id)
        # Update group's children.
        if (const.resource_type.GROUP == resource_type):
            for child_id in self.get_group_children(id):
                self._communicator.modify_attr(child_id, "target-role", target_role)
        self._communicator.modify_attr(id, "target-role", target_role)

    def start(self, id):
        self._modify_target_role(id, CIB.STARTED_ROLE)

    def stop(self, id):
        self._modify_target_role(id, CIB.STOPPED_ROLE)

    def manage(self, id):
        self._communicator.modify_attr(id, "is-managed", "true")

    def unmanage(self, id):
        self._communicator.modify_attr(id, "is-managed", "false")

    def migrate_resource(self, resource_id, node_id):
        self._communicator.migrate_resource(resource_id, node_id)


    def get_loc_constraints(self, id):
        """ Returns list of LocConstarint instances. """
        loc_constraints = []
        for constr_el in self._get_loc_contraints_els_by_resource(id):
            node_id = constr_el.get("node")
            if (node_id is None):
                rule_el = constr_el.find("./rule")
                if (rule_el is None):
                    continue
                expr_el = rule_el.find("./expression")
                if (expr_el is None):
                    continue

                node_id = expr_el.get("node")
                score = rule_el.get("score")
                loc_constraints.append(LocConstarint(node_id, score))
            else:
                score = constr_el.get("score")
                loc_constraints.append(LocConstarint(node_id, score))
        return loc_constraints


    def create_loc_constraint(self, resource_id, node_id):
        self.remove_loc_constraints_by_resource(resource_id)
        attrs = {"rsc": resource_id,
                 "node": node_id,
                 "score": "+INFINITY",
                 "id": "%s-location" % (resource_id)}
        SubEl(self._constraints_el, CIB.LOC_CONSTRAINT_TAG, attrs)
        self._communicator.modify(self._constraints_el)


    def remove_loc_constraints_by_resource(self, id):
        """ Remove all location constraints of the resource. """
        for constr_el in self._get_loc_contraints_els_by_resource(id):
            self._constraints_el.remove(constr_el)
            self._communicator.remove_constraint(constr_el)


    def cleanup(self, resource_id):
        for node_id in self.get_nodes_ids():
            self._communicator.cleanup(resource_id, node_id)


    def set_group(self, resource_id, group_id):
        resource_el = self._get_primitive_resource_el(resource_id)
        target_group_el = self._get_group_el(group_id)

        current_group_el = self._get_group_el_by_primitive(resource_id)
        if (current_group_el is None):
            self._resources_el.remove(resource_el)
        else:
            # Remove the group if necessary.
            if (CIB._is_last_child(current_group_el, resource_el)):
                self.remove_loc_constraints_by_resource(current_group_el.get("id"))
                self._resources_el.remove(current_group_el)
            else:
                current_group_el.remove(resource_el)

        target_group_el.append(resource_el)
        self._communicator.modify(self._resources_el)


    def move_to_root(self, id):
        """ Moves the child resource to root. """
        resource_el = self._get_primitive_resource_el(id)
        group_el = self._get_group_el_by_primitive(id)
        if (group_el is None):
            return
        
        if (CIB._is_last_child(group_el, resource_el)):
            self.remove_loc_constraints_by_resource(group_el.get("id"))
            self._resources_el.remove(group_el)
        else:
            group_el.remove(resource_el)

        self._resources_el.append(resource_el)
        self._communicator.modify(self._resources_el)


    def remove_primitive_resource(self, id):
        resource_el = self._get_primitive_resource_el(id)
        if (resource_el is None):
            return
        self.remove_loc_constraints_by_resource(id)

        group_el = self._get_group_el_by_primitive(id)
        # Process root primitive resource.
        if (group_el is None):
            self._communicator.remove_resource(resource_el)
            self._resources_el.remove(resource_el)
        # Process child primitive resource.
        else:
            if (CIB._is_last_child(group_el, resource_el)):
                self.remove_loc_constraints_by_resource(group_el.get("id"))
                self._communicator.remove_resource(group_el)
                self._resources_el.remove(group_el)
            else:
                self._communicator.remove_resource(resource_el)
                group_el.remove(resource_el)
