

class Entity:
    def __init__(self, eid):
        self.eid = eid

        self.world = None
        self.x = self.y = self.z = self.h = self.p = self.r = 0.0
        self.dX = self.dY = self.dZ = self.dH = self.dP = self.dR = 0.0
