from minecraft.entity.Entity import Entity
from pumpkinpy.networking import Packet
from pumpkinpy.Util import absoluteInt


class Player(Entity):
    def __init__(self, client, eid):
        Entity.__init__(self, eid)

        self.client = client

        self.visibleChunks = []
        self.chunk = None

        self.health = 20
        self.stance = 0.0
        self.onGround = False

        self.name = self.client.username

        self.inventory = []

        for i in xrange(45):
            self.inventory.append(InventoryItem(slot=i))

    def spawn(self, world, x, y, z, onGround=False, broadcast=True):
        self.world = world

        self.x = x
        self.y = y
        self.z = z
        
        self.onGround = onGround

        self.chunk = self.world.getChunk(*self.world.getChunkCoord(self.x, self.z))
        self.chunk.enter(self)

        packet = Packet.SpawnPositionPacket('')
        packet.writePacket(self.world.spawn)
        self.client.send(packet)

        if broadcast:

            packet = Packet.NamedEntitySpawnPacket('')
            packet.writePacket(self)

            # TODO: broadcast in more than one chunk?

            for entity in self.chunk.entities:
                if isinstance(entity, Player) and entity != self:
                    entity.client.send(packet)

    def move(self, newX, newY, newZ, stance=None, yaw=None, pitch=None, onGround=None, broadcast=True):
        self.dX = newX - self.x
        self.dY = newY - self.y
        self.dZ = newZ - self.z

        if yaw is not None:
            self.dH = yaw - self.h
            self.h = yaw
        
        if pitch is not None:
            self.dP = pitch - self.p
            self.p = pitch

        if stance is not None:
            self.stance = stance

        if onGround is not None:
            self.onGround = onGround
        
        relative = self.dX < 4 and self.dY < 4 and self.dZ < 4

        self.x = newX
        self.y = newY
        self.z = newZ

        chunkX, chunkZ = self.world.getChunkCoord(self.x, self.z)
        chunk = self.world.getChunk(chunkX, chunkZ)
        if not chunk:
            print("Could not find chunk at: %s %s" % (chunkX, chunkZ))
            return

        if self.chunk != chunk and self.chunk is not None:
            chunkdX = chunk.x - self.chunk.x
            chunkdZ = chunk.z - self.chunk.z

            newVisibleChunks = self.visibleChunks[:]

            for i, coord in enumerate(newVisibleChunks):
                newVisibleChunks[i] = (coord[0] + chunkdX, coord[1] + chunkdZ)

            self.updateVisibility(self.visibleChunks, newVisibleChunks)

            if self.chunk is not None:
                self.chunk.exit(self)

            self.chunk = chunk

            self.chunk.enter(self)

        if broadcast:
            self.sendPosLook(relative=relative)

    def rotate(self, yaw, pitch):
        pass

    def updateVisibility(self, oldVisibility, newVisibility):
        for chunkCoord in oldVisibility:
            x, z = chunkCoord
            chunk = self.world.getChunk(x, z)
            if chunkCoord not in newVisibility:
                chunk.sendUnloadChunk(self.client)

        for chunkCoord in newVisibility:
            x, z = chunkCoord
            chunk = self.world.getChunk(x, z)
            if chunkCoord not in oldVisibility:
                chunk.sendPreChunk(self.client)
                chunk.sendLoadChunk(self.client)

        self.visibleChunks = newVisibility

    def sendPosLook(self, relative=False):
        packet = Packet.PlayerPosLookPacket('')
        packet.writePacket(self.x, self.y, self.stance, self.z, self.h, self.p, self.onGround)
        self.client.send(packet)

        if relative:
            x = absoluteInt(self.dX)
            y = absoluteInt(self.dY)
            z = absoluteInt(self.dZ)

            packet = Packet.EntityRelativePosLookPacket('')
            packet.writePacket(self.eid, x, y, z, int(self.h), int(self.p))

            for entity in self.chunk.entities:
                if isinstance(entity, Player) and entity != self:
                    entity.client.send(packet)
        else:
            x = absoluteInt(self.x)
            y = absoluteInt(self.y)
            z = absoluteInt(self.z)

            packet = Packet.EntityMovePacket('')
            packet.writePacket(self.eid, x, y, z, int(self.h), int(self.p))

            for entity in self.chunk.entities:
                if isinstance(entity, Player) and entity != self:
                    entity.client.send(packet)

    def sendInventory(self):
        packet = Packet.WindowItemsPacket('')
        packet.writePacket(windowId=0, inventory=self.inventory)
        self.client.send(packet)

    def destroy(self):
        del self.inventory[:]

        packet = Packet.EntityDestroyPacket('')
        packet.writePacket(self.eid)

        for entity in self.chunk.entities:
            if isinstance(entity, Player) and entity != self:
                entity.client.send(packet)


class InventoryItem:
    def __init__(self, slot, itemId=-1, count=0, uses=0):
        self.slot = slot
        self.itemId = itemId
        self.count = count
        self.uses = uses

    def pack(self):
        pass

    def unpack(self):
        pass
