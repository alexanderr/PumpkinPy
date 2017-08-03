

class Block:
    def __init__(self, x, y, z, blockId, blockData, blockLight, skyLight):
        self.x = x
        self.y = y
        self.z = z
        self.blockId = blockId
        self.blockData = blockData
        self.skyLight = skyLight
        self.blockLight = blockLight
