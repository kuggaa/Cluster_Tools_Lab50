class node_state(object):
    OFF = 0
    ON = 1
    STANDBY = 2

    @staticmethod
    def to_str(state):
        if (node_state.OFF == state):
            return "OFF"
        elif (node_state.ON == state):
            return "ON"
        elif (node_state.STANDBY == state):
            return "STANDBY"
        else:
            assert(False and "bad state")


class resource_type(object):
    GROUP = 1
    CLONE = 2
    VM = 3
    DUMMY = 4
    IP = 5
    FILESYSTEM = 6
    VOLUME = 7
    GLUSTERD = 8
    IPMI = 9
    PDU = 10

    @staticmethod
    def to_str(res_type):
        if (resource_type.GROUP == res_type):
            return "Group"
        elif (resource_type.VM == res_type):
            return "VM"
        elif (resource_type.GLUSTER_FS == res_type):
            return "GlusterFS"
        elif (resource_type.DUMMY == res_type):
            return "Dummy"
        elif (resource_type.IP == res_type):
            return "IP"
        else:
            assert(False and "bad type")


class resource_state(object):
    OFF = 0
    ON = 1
    UNMANAGED = 2
    FAILED = 3
    STOPPING = 4
    STARTING = 5


    @staticmethod
    def to_str(state):
        if (resource_state.OFF == state):
            return "OFF"
        elif (resource_state.ON == state):
            return "ON"
        elif (resource_state.STARTING == state):
            return "STARTING"
        elif (resource_state.STOPPING == state):
            return "STOPPING"
        elif (resource_state.FAIL == state):
            return "FAIL"
        else:
            assert(False and "bad state")


class action(object):
    SEE_NODES = "can_see_nodes"
    CONTROL_NODES = "can_control_nodes"

    SEE_RESOURCES = "can_see_resources"
    SEE_RESOURCES_TIMEOUTS = "can_see_resources_timeouts"
    CREATE_RESOURCE = "can_create_resource"
    CONTROL_RESOURCES = "can_control_resources"
    OPEN_VM_CONSOLE = "can_open_vm_console"
