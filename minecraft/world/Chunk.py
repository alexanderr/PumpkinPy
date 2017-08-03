from pumpkinpy.networking import Packet


class Chunk:
    def __init__(self, server, world, x, z, terrainPopulated, blocks, blockMeta, blockLight, skyLight,
                 persistent=False):
        self.server = server
        self.world = world
        self.x = x
        self.z = z
        self.terrainPopulated = terrainPopulated
        self.blocks = blocks
        self.blockMeta = blockMeta
        self.blockLight = blockLight
        self.skyLight = skyLight

        self.persistent = persistent

        self.entities = []

    def sendPreChunk(self, client):
        packet = Packet.PreChunkPacket('')
        packet.writePacket(self.x, self.z, mode=Packet.PreChunkPacket.LOAD)
        client.send(packet)

    def sendLoadChunk(self, client):
        packet = Packet.MapChunkPacket('')
        packet.writePacket(self)
        client.send(packet)

    def sendUnloadChunk(self, client):
        if self.persistent:
            return

        packet = Packet.PreChunkPacket('')
        packet.writePacket(self.x, self.z, mode=Packet.PreChunkPacket.UNLOAD)
        client.send(packet)

    def enter(self, entity):
        self.entities.append(entity)

    def exit(self, entity):
        self.entities.remove(entity)
