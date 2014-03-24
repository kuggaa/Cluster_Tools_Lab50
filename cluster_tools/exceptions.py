class DeviceError(Exception):
    def __init__(self, device_id):
        self.device_id = device_id


class ProcessError(Exception):
    def __init__(self, args, err_output):
        self.cmd = " ".join(args)
        self.err_output = err_output
