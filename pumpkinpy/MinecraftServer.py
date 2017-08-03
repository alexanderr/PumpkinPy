import __builtin__

from twisted.internet import reactor

__builtin__.reactor = reactor

from pumpkinpy.networking.MinecraftProtocol import MinecraftFactory
from pumpkinpy.chat.ChatManager import ChatManager
from minecraft.world.World import World


class MinecraftServer:

    def __init__(self, worldDirectory):
        self.factory = MinecraftFactory()
        self.factory.server = self

        self.world = World(self, worldDirectory)
        self.chatManager = ChatManager(self)

        self.nextEID = 100
        self.id2entity = {}

    def start(self, port):
        print('Listening on port %d...' % port)
        reactor.listenTCP(port, self.factory)
        reactor.run()

    def allocateEntityId(self):
        eid = self.nextEID
        self.nextEID += 1
        return eid


if __name__ == '__main__':        
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--port', default=25565, type=int, help='The port for the server to listen on.')
    parser.add_argument('--world-directory', default='World1', help='The directory name of the main world.')
    args = parser.parse_args()

    server = MinecraftServer(args.world_directory)
    server.start(args.port)


