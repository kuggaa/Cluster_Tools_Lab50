class DeviceError(Exception):
    def __init__(self, device_id, err_output=""):
        self.device_id = device_id
        self.err_output = err_output


class ProcessError(Exception):
    def __init__(self, args, err_output):
        self.cmd = " ".join(args)
        self.err_output = err_output
