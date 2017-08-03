import struct
import zlib


UPSTREAM = 0
DOWNSTREAM = 1
BOTH = 2


class Packet:
    PACKET_ID = None
    PACKET_DIRECTION = None
    EXPECTED_SIZE = None  # Expected size without variable-length strings.

    def __init__(self, buff):
        self.buff = buff
        self.size = 0

    def writePacket(self, *args):
        raise NotImplementedError

    def handlePacket(self):
        raise NotImplementedError

    def clear(self):
        self.buff = ''
        self.size = 0

    def unpack(self, fmt):
        size = struct.calcsize(fmt)
        self.size += size
        data = struct.unpack(fmt, self.buff[:size])
        self.buff = self.buff[size:]
        return data

    def pack(self, fmt, *args):
        size = struct.calcsize(fmt)
        self.size += size
        self.buff += struct.pack(fmt, *args)

    def unpackString(self):
        length = self.unpack('!h')[0]
        if length == 0:
            return ''
        fmt = '!' + ('c' * length)
        return ''.join(self.unpack(fmt))

    def packString(self, s):
        self.pack('!h', len(s))
        if len(s) == 0:
            return
        for c in s:
            self.pack('!c', c)


class KeepAlivePacket(Packet):
    PACKET_ID = 0x00
    PACKET_DIRECTION = BOTH
    PACKET_SIZE = 1

    def handlePacket(self):
        pass

    def writePacket(self):
        self.pack('!B', self.PACKET_ID)


class LoginRequestPacket(Packet):
    PACKET_ID = 0x01
    PACKET_DIRECTION = BOTH
    EXPECTED_SIZE = 18

    def handlePacket(self):
        protocolVersion = self.unpack('!i')[0]
        username = self.unpackString()

        # Used for password protected servers.
        password = self.unpackString()

        # Unused
        # seed, dimension = self.unpack('!qb')

        return protocolVersion, username

    def writePacket(self, entityId, seed, dimension):
        self.pack('!B', self.PACKET_ID)
        self.pack('!i', entityId)

        # Unused vars
        field2 = field3 = ''

        self.packString(field2)
        self.packString(field3)

        self.pack('!qb', seed, dimension)


class LoginHandshakePacket(Packet):
    PACKET_ID = 0x02
    PACKET_DIRECTION = BOTH
    EXPECTED_SIZE = 3

    def handlePacket(self):
        username = self.unpackString()
        return username

    def writePacket(self, connectionHash):
        self.pack('!B', self.PACKET_ID)
        self.packString(connectionHash)


class PreChunkPacket(Packet):
    PACKET_ID = 0x32
    PACKET_DIRECTION = DOWNSTREAM
    EXPECTED_SIZE = 10

    UNLOAD = 0
    LOAD = 1

    def handlePacket(self):
        pass

    def writePacket(self, chunkX, chunkZ, mode):
        self.pack('!B', self.PACKET_ID)
        self.pack('!iiB', chunkX, chunkZ, mode)


class MapChunkPacket(Packet):
    PACKET_ID = 0x33
    PACKET_DIRECTION = DOWNSTREAM
    EXPECTED_SIZE = 18

    def handlePacket(self):
        pass

    def writePacket(self, chunk, sizeX=15, sizeY=127, sizeZ=15):
        x = (chunk.x * 16)
        y = 0
        z = (chunk.z * 16)

        self.pack('!B', self.PACKET_ID)
        self.pack('!ihi', x, y, z)
        self.pack('!bbb', sizeX, sizeY, sizeZ)

        chunkData = chunk.blocks + chunk.blockMeta + chunk.blockLight + chunk.skyLight
        chunkData = "".join(map(chr, chunkData))
        compressedData = zlib.compress(chunkData)

        self.pack('!i', len(compressedData))
        self.buff += compressedData

        self.size += len(compressedData)


class SpawnPositionPacket(Packet):
    PACKET_ID = 0x06
    PACKET_DIRECTION = DOWNSTREAM
    EXPECTED_SIZE = 13

    def handlePacket(self):
        pass

    def writePacket(self, spawn):
        x, y, z = spawn
        self.pack('!B', self.PACKET_ID)
        self.pack('!iii', x, y, z)


class PlayerPosLookPacket(Packet):
    PACKET_ID = 0x0D
    PACKET_DIRECTION = BOTH
    EXPECTED_SIZE = 42

    def handlePacket(self):
        return self.unpack('!ddddffb')

    def writePacket(self, x, y, stance, z, yaw, pitch, onGround):
        self.pack('!B', self.PACKET_ID)
        self.pack('!ddddffb', x, y, stance, z, yaw, pitch, onGround)


class PlayerPositionPacket(Packet):
    PACKET_ID = 0x0B
    PACKET_DIRECTION = UPSTREAM
    EXPECTED_SIZE = 34

    def handlePacket(self):
        return self.unpack('!ddddb')

    def writePacket(self, *args):
        pass


class PlayerLookPacket(Packet):
    PACKET_ID = 0x0C
    PACKET_DIRECTION = UPSTREAM
    EXPECTED_SIZE = 10

    def handlePacket(self):
        yaw, pitch, onGround = self.unpack('!ffb')
        return yaw, pitch, onGround

    def writePacket(self, *args):
        pass


class PlayerOnGroundPacket(Packet):
    PACKET_ID = 0x0A
    PACKET_DIRECTION = UPSTREAM
    EXPECTED_SIZE = 2

    def handlePacket(self):
        onGround = self.unpack('!b')[0]
        return onGround

    def writePacket(self, *args):
        pass


class EntityAnimationPacket(Packet):
    PACKET_ID = 0x12
    PACKET_DIRECTION = BOTH
    EXPECTED_SIZE = 6

    def handlePacket(self):
        entityId = self.unpack('!i')
        animation = self.unpack('!b')
        print("Entity Animation: %s %s" % (entityId, animation))
        return entityId, animation

    def writePacket(self, *args):
        pass


class TimeUpdatePacket(Packet):
    PACKET_ID = 0x04
    PACKET_DIRECTION = DOWNSTREAM
    EXPECTED_SIZE = 9

    def handlePacket(self):
        pass

    def writePacket(self, time):
        self.pack('!B', self.PACKET_ID)
        self.pack('!q', time)


class SetSlotPacket(Packet):
    PACKET_ID = 0x67
    PACKET_DIRECTION = DOWNSTREAM
    EXPECTED_SIZE = 6

    def handlePacket(self):
        pass

    def writePacket(self, windowId, item):
        self.pack('!B', self.PACKET_ID)
        self.pack('!b', windowId)

        self.pack('!h', item.slot)
        self.pack('!h', item.itemId)

        if item.itemId != -1:
            self.pack('!bh', item.count, item.uses)


class WindowItemsPacket(Packet):
    PACKET_ID = 0x68
    PACKET_DIRECTION = DOWNSTREAM
    EXPECTED_SIZE = 4

    def handlePacket(self):
        pass

    def writePacket(self, windowId, inventory):
        self.pack('!B', self.PACKET_ID)
        self.pack('!b', windowId)
        self.pack('!h', len(inventory))

        for item in inventory:
            self.pack('!h', item.itemId)

            if item.itemId != -1:
                self.pack('!bh', item.count, item.uses)


class PlayerDiggingPacket(Packet):
    PACKET_ID = 0x0E
    PACKET_DIRECTION = BOTH
    EXPECTED_SIZE = 12

    START_DIGGING = 0
    DIGGING = 1
    STOPPED_DIGGING = 2
    BLOCK_BROKEN = 3
    DROP_ITEM = 4

    def handlePacket(self):
        status = self.unpack('!b')[0]
        x, y, z = self.unpack('!ibi')
        face = self.unpack('!b')[0]

        return status, x, y, z, face

    def writePacket(self):
        pass


class HoldItemPacket(Packet):
    PACKET_ID = 0x10
    PACKET_DIRECTION = BOTH
    EXPECTED_SIZE = 3

    def writePacket(self, *args):
        pass

    def handlePacket(self):
        slot = self.unpack('!h')[0]
        return slot


class BlockChangePacket(Packet):
    PACKET_ID = 0x35
    PACKET_DIRECTION = BOTH
    EXPECTED_SIZE = 12

    def handlePacket(self):
        pass

    def writePacket(self, x, y, z, blockId, blockMeta):
        self.pack('!B', self.PACKET_ID)
        self.pack('ibibb', x, y, z, blockId, blockMeta)


class ChatMessagePacket(Packet):
    PACKET_ID = 0x03
    PACKET_DIRECTION = BOTH
    EXPECTED_SIZE = 3

    def handlePacket(self):
        message = self.unpackString()
        return message

    def writePacket(self, message):
        self.pack('!B', self.PACKET_ID)
        self.packString(message)


class NamedEntitySpawnPacket(Packet):
    PACKET_ID = 0x14
    PACKET_DIRECTION = DOWNSTREAM
    EXPECTED_SIZE = 23

    def handlePacket(self):
        pass

    def writePacket(self, player):
        self.pack('!B', self.PACKET_ID)
        self.pack('!i', player.eid)
        self.pack('!iii', int(player.x), int(player.y), int(player.z))
        self.pack('!bb', int(player.h), int(player.p))

        # TODO: current hold item
        self.pack('!h', 0)


class EntityDestroyPacket(Packet):
    PACKET_ID = 0x1D
    PACKET_DIRECTION = DOWNSTREAM
    EXPECTED_SIZE = 5

    def handlePacket(self):
        pass

    def writePacket(self, eid):
        self.pack('!Bi', self.PACKET_ID, eid)


class EntityStillPacket(Packet):
    PACKET_ID = 0x1E
    PACKET_DIRECTION = DOWNSTREAM
    EXPECTED_SIZE = 5

    def handlePacket(self):
        pass

    def writePacket(self, eid):
        self.pack('!Bi', self.PACKET_ID, eid)


class EntityRelativePosPacket(Packet):
    PACKET_ID = 0x1F
    PACKET_DIRECTION = DOWNSTREAM
    EXPECTED_SIZE = 8

    def handlePacket(self):
        pass

    def writePacket(self, eid, dX, dY, dZ):
        self.pack('!Bibbb', self.PACKET_ID, eid, dX, dY, dZ)


class EntityLookPacket(Packet):
    PACKET_ID = 0x20
    PACKET_DIRECTION = DOWNSTREAM
    EXPECTED_SIZE = 7

    def handlePacket(self):
        pass

    def writePacket(self, eid, h, p):
        self.pack('!Bibb', self.PACKET_ID, eid, h, p)


class EntityRelativePosLookPacket(Packet):
    PACKET_ID = 0x21
    PACKET_DIRECTION = DOWNSTREAM
    EXPECTED_SIZE = 10

    def handlePacket(self):
        pass

    def writePacket(self, eid, dX, dY, dZ, h, p):
        self.pack('!Bibbbbb', self.PACKET_ID, eid, dX, dY, dZ, h, p)


class EntityMovePacket(Packet):
    PACKET_ID = 0x22
    PACKET_DIRECTION = DOWNSTREAM
    EXPECTED_SIZE = 19

    def handlePacket(self):
        pass

    def writePacket(self, eid, x, y, z, h, p):
        self.pack('!Biiiibb', self.PACKET_ID, eid, x, y, z, h, p)


class ClientKickPacket(Packet):
    PACKET_ID = 0xFF
    PACKET_DIRECTION = DOWNSTREAM
    EXPECTED_SIZE = 3

    def handlePacket(self):
        pass

    def writePacket(self, reason):
        self.pack('!B', self.PACKET_ID)
        self.packString(reason)

VALID_PACKETS = {
    KeepAlivePacket,
    LoginRequestPacket,
    LoginHandshakePacket,
    ChatMessagePacket,
    TimeUpdatePacket,

    SpawnPositionPacket,



    PlayerOnGroundPacket,
    PlayerPositionPacket,
    PlayerLookPacket,
    PlayerPosLookPacket,
    PlayerDiggingPacket,


    HoldItemPacket,

    NamedEntitySpawnPacket,
    EntityDestroyPacket,
    EntityStillPacket,
    EntityRelativePosPacket,
    EntityLookPacket,
    EntityRelativePosLookPacket,
    EntityMovePacket,

    EntityAnimationPacket,



    PreChunkPacket,
    MapChunkPacket,

    BlockChangePacket,


    SetSlotPacket,
    WindowItemsPacket,
    ClientKickPacket,
}
