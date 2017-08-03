import struct
from twisted.internet import protocol

from pumpkinpy.networking import Packet
from minecraft.entity.Player import Player


ANONYMOUS = 0
HANDSHAKE = 1
LOGGING_IN = 2
PLAY_GAME = 3


class MinecraftProtocol(protocol.Protocol):
    PROTOCOL_VERSION = 8

    def __init__(self):
        self.factory = None
        self.server = None
        self.username = None
        self.state = None
        self.player = None

        self.dataBuffer = ''

    def connectionMade(self):
        print('A new connection was made!')
        self.factory.clients.append(self)
        self.server = self.factory.server
        self.state = ANONYMOUS

    def dataReceived(self, data):
        self.dataBuffer += data

        packetId = struct.unpack_from('!b', self.dataBuffer)[0]

        for p in Packet.VALID_PACKETS:
            if p.PACKET_ID == packetId:
                if p.PACKET_DIRECTION not in (Packet.UPSTREAM, Packet.BOTH):
                    self.sendKick('A nonsendable packet was sent!')
                    return
                if p.EXPECTED_SIZE > len(self.dataBuffer):
                    return
                break
        else:
            print("Unhandled Packet ID: %s" % hex(packetId))
            self.sendKick('Invalid packet was sent!')
            return

        self.handlePacket(packetId)

    def handlePacket(self, packetId):
        self.dataBuffer = self.dataBuffer[1:]

        if self.state == ANONYMOUS:
            if packetId == 0x02:
                packet = Packet.LoginHandshakePacket(self.dataBuffer)
                self.username = packet.handlePacket()

                self.dataBuffer = self.dataBuffer[packet.size:]
                packet.clear()

                self.state = HANDSHAKE

                packet.writePacket(connectionHash='-')
                self.send(packet)
            else:
                self.sendKick('Invalid packet sent!')
                return
        elif self.state == HANDSHAKE:
            if packetId == 0x01:
                packet = Packet.LoginRequestPacket(self.dataBuffer)
                protocolVersion, username = packet.handlePacket()

                if protocolVersion != self.PROTOCOL_VERSION:
                    self.sendKick('Invalid protocol version!')
                    return
                if username != self.username:
                    self.sendKick('The server rejected your login request.')
                    return

                self.dataBuffer = self.dataBuffer[packet.size:]
                packet.clear()

                self.state = LOGGING_IN

                self.handleLogin()
            else:
                self.sendKick('Invalid packet sent!')
                return

        elif self.state == LOGGING_IN:
            if packetId == 0x00:
                packet = Packet.KeepAlivePacket('')
                packet.writePacket()
                self.send(packet)
            else:
                self.sendKick('Invalid packet sent!')
                return

        elif self.state == PLAY_GAME:
            if packetId == 0x00:
                packet = Packet.KeepAlivePacket('')
                packet.writePacket()
                self.send(packet)

            elif packetId == 0x0D:
                packet = Packet.PlayerPosLookPacket(self.dataBuffer)
                x, stance, y, z, yaw, pitch, onGround = packet.handlePacket()
                self.player.move(x, y, z, stance=stance, yaw=yaw, pitch=pitch, broadcast=False)
                self.dataBuffer = self.dataBuffer[packet.size:]
                packet.clear()

            elif packetId == 0x0B:
                packet = Packet.PlayerPositionPacket(self.dataBuffer)
                x, y, stance, z, onGround = packet.handlePacket()
                self.player.move(x, y, z, stance=stance, onGround=onGround, broadcast=False)
                self.dataBuffer = self.dataBuffer[packet.size:]
                packet.clear()

            elif packetId == 0x0C:
                packet = Packet.PlayerLookPacket(self.dataBuffer)
                yaw, pitch, onGround = packet.handlePacket()
                self.player.rotate(yaw, pitch)
                self.dataBuffer = self.dataBuffer[packet.size:]
                packet.clear()

            elif packetId == 0x0A:
                packet = Packet.PlayerOnGroundPacket(self.dataBuffer)
                onGround = packet.handlePacket()
                self.player.onGround = onGround
                self.dataBuffer = self.dataBuffer[packet.size:]
                packet.clear()

            elif packetId == 0x12:
                packet = Packet.EntityAnimationPacket(self.dataBuffer)
                packet.handlePacket()
                self.dataBuffer = self.dataBuffer[packet.size:]
                packet.clear()

            elif packetId == 0x0E:
                packet = Packet.PlayerDiggingPacket(self.dataBuffer)
                packet.handlePacket()
                self.dataBuffer = self.dataBuffer[packet.size:]
                packet.clear()

            elif packetId == 0x03:
                packet = Packet.ChatMessagePacket(self.dataBuffer)
                message = packet.handlePacket()

                self.dataBuffer = self.dataBuffer[packet.size:]
                packet.clear()

                self.server.chatManager.handleChatMessage(self, message)
            else:
                print('Unhandled packet ID: %s' % hex(packetId))

        if len(self.dataBuffer):
            self.dataReceived('')

    def send(self, data):
        if isinstance(data, Packet.Packet):
            data = data.buff
        self.transport.write(data)

    def connectionLost(self, reason=protocol.connectionDone):
        protocol.Protocol.connectionLost(self, reason)
        if self in self.server.world.clients:
            self.server.world.clients.remove(self)
        self.factory.clients.remove(self)
        print("Lost connection!")

    def handleLogin(self):
        self.player = Player(self, self.server.allocateEntityId())

        packet = Packet.LoginRequestPacket('')
        packet.writePacket(entityId=self.player.eid, seed=self.server.world.seed, dimension=0)
        self.send(packet)

        self.sendInitialChunks()

        self.player.sendInventory()

        self.state = PLAY_GAME

        self.server.world.clients.append(self)

        x, y, z = self.server.world.spawn
        y += 2

        self.player.spawn(self.server.world, x, y, z)
        self.player.sendPosLook()

    def sendInitialChunks(self):
        spawnX, spawnY, spawnZ = self.server.world.spawn

        chunkX, chunkZ = self.server.world.getChunkCoord(spawnX, spawnZ)

        chunkCoords = self.server.world.getAllChunksInRadius(chunkX, chunkZ, 5)

        for c in chunkCoords:
            x, z = c
            self.player.visibleChunks.append((x, z))
            chunk = self.server.world.getChunk(x, z)
            if not chunk:
                print("No chunk at: %s" % chunk)
                return

            chunk.sendPreChunk(self)
            chunk.sendLoadChunk(self)

    def sendKick(self, reason):
        packet = Packet.ClientKickPacket('')
        packet.writePacket(reason)
        self.send(packet)
        self.transport.loseConnection()


class MinecraftFactory(protocol.ServerFactory):
    protocol = MinecraftProtocol
    server = None
    clients = []
