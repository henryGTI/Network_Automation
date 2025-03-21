class Device:
    def __init__(self, name, vendor, ip, id=None):
        self.id = id
        self.name = name
        self.vendor = vendor
        self.ip = ip

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'vendor': self.vendor,
            'ip': self.ip
        } 