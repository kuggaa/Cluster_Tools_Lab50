class DeviceError(Exception):
    def __init__(self, device_id):
        self.device_id = device_id
