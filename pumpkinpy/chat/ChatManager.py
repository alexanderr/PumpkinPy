from pumpkinpy.networking import Packet

CHAT_FORMATTING = '<%s> %s'
COLOR_ESCAPE_CHARACTER = unichr(0x00A7)


class ChatManager:
    def __init__(self, server):
        self.server = server

    def handleChatMessage(self, client, message):
        packet = Packet.ChatMessagePacket('')
        packet.writePacket(CHAT_FORMATTING % (client.username, message))

        client.send(packet)

    def sendPlayerJoined(self, username):
        pass

