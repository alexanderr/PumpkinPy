import os

from nbt.nbt import NBTFile

from minecraft.world.Block import Block
from minecraft.world.Chunk import Chunk
from pumpkinpy.Util import base36
from pumpkinpy.networking import Packet


class World:
    def __init__(self, server, folder):
        self.server = server
        self.folder = folder

        if not os.path.exists(folder) or not os.path.isdir(folder):
            print('The world folder is missing!')
            return

        self.levelData = NBTFile(filename=os.path.join(self.folder, 'level.dat'), buffer='rb')
        self.seed = self.levelData['Data']['RandomSeed'].value
        self.spawn = [
            self.levelData['Data']['SpawnX'].value,
            self.levelData['Data']['SpawnY'].value,
            self.levelData['Data']['SpawnZ'].value
        ]

        self.chunks = {}

        self.test = False

        self.loadWorld()
        print 'Loaded %s chunks' % (len(self.chunks))

        self.clients = []

        self.time = 0

        reactor.callLater(1, self.sendTime)

    def loadWorld(self):
        for root, dirs, files in os.walk(self.folder):
            for name in files:
                self.handleChunkFile(root, name)

    def handleChunkFile(self, root, name):
        location = os.path.join(root, name)
        root = root.replace(self.folder, '')[1:]

        dirs = root.split(os.sep)
        if len(dirs) != 2:
            return

        a, b = dirs

        chunkFile = name.split('.')
        if len(chunkFile) != 4:
            print("Invalid chunk file: %s" % location)
            return

        if chunkFile[0] != 'c' or chunkFile[3] != 'dat':
            print("Invalid chunk file: %s" % location)
            return

        x, z = chunkFile[1], chunkFile[2]
        x, z = int(x, 36), int(z, 36)
        
        print("Loaded %s %s" % (x, z))

        if a != base36(x & 63):
            print("Invalid chunk file: %s" % location)
            return
        if b != base36(z & 63):
            print("Invalid chunk file: %s" % location)
            return

        nbt = NBTFile(filename=location, buffer='rb')

        if x != nbt['Level']['xPos'].value:
            print("Invalid chunk file: %s" % location)
            return

        if z != nbt['Level']['zPos'].value:
            print("Invalid chunk file: %s" % location)
            return

        chunk = Chunk(
            self.server,
            self,
            x, z,
            nbt['Level']['TerrainPopulated'].value,
            nbt['Level']['Blocks'].value,
            nbt['Level']['Data'].value,
            nbt['Level']['BlockLight'].value,
            nbt['Level']['SkyLight'].value
        )

        self.chunks[(chunkFile[1], chunkFile[2])] = chunk

    def getChunk(self, x, z):
        a, b = base36(x), base36(z)
        chunk = self.chunks.get((a, b))
        if not chunk:
            print('No chunk %d %d %s %s' % (x, z, a, b))
            print(self.chunks.keys())
        return chunk

    def getChunkCoord(self, x, z):
        return int(x) >> 4, int(z) >> 4

    def getAllChunksInRadius(self, centerX, centerZ, radius):
        chunks = []

        for x in xrange(centerX - radius, centerX + radius):
            for z in xrange(centerZ - radius, centerZ + radius):
                chunks.append((x, z))

        return chunks

    def sendTime(self):
        packet = Packet.TimeUpdatePacket('')
        packet.writePacket(self.time)

        for c in self.clients:
            c.send(packet)

        self.time += 20

        if self.time > 24000:
            self.time = 0

        reactor.callLater(1, self.sendTime)

    def getBlockAt(self, x, y, z):
        chunkX = x >> 4
        chunkZ = z >> 4

        relX = x & 15
        relZ = z & 15

        chunk = self.getChunk(chunkX, chunkZ)

        index = y + (relZ * 128 + (relX * 128 * 16))

        blockId = chunk.blocks[index]

        dataIndex = index / 2

        msb = index % 2

        if msb:
            blockLight = chunk.blockLight[dataIndex] >> 4
            blockMeta = chunk.blockMeta[dataIndex] >> 4
            skyLight = chunk.skyLight[dataIndex] >> 4
        else:
            blockLight = chunk.blockLight[dataIndex] & 15
            blockMeta = chunk.blockMeta[dataIndex] & 15
            skyLight = chunk.skyLight[dataIndex] & 15

        return Block(x, y, z, blockId, blockMeta, blockLight, skyLight)
