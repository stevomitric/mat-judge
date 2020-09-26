''' Limiting requests to release stress from the workers '''
import time

class Limits:
    def __init__(self, a=100, b=5000):
        self.dataset = {}

        self.limits = {
            'ip_status_timeout': a,
            'ip_submit_timeout': b,
        }

    def setLimits(self, a = None, b = None):
        if a != None:
            self.limits['ip_status_timeout'] = a
        if b != None:
            self.limits['ip_submit_timeout'] = b

    def validateRequest(self, req, ip):
        ''' Returns 0/1 indicating an invalid/valid request '''

        # First time
        if ip not in self.dataset or req not in self.dataset[ip]:
            self.dataset[ip] = {req:time.time()}
            return 1

        if time.time() - self.dataset[ip][req] < self.limits[req]/1000.0:
            return 0
        else:
            self.dataset[ip][req] = time.time()
            return 1