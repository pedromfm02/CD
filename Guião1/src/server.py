"""CD Chat server program."""
import logging
import socket
import selectors

from collections import defaultdict

logging.basicConfig(filename="server.log", level=logging.DEBUG)
from .protocol import CDProto, CDProtoBadFormat

class Server:
    """Chat Server process."""

    def __init__(self):
        self.selector = selectors.DefaultSelector()
        self.serversocket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.serversocket.bind(("localhost",5005))
        self.serversocket.listen()
        logging.debug("[SERVER]: initialized on [PORT] -> 5005")
        print("[SERVER]: initialized on [PORT] -> 5005")
        self.selector.register(self.serversocket, selectors.EVENT_READ, self.accept) 
        self.conn_list = {}
        self.Channel = defaultdict(list)
        


    def accept(self, conn, mask):
        conn, addr = self.serversocket.accept()
        logging.debug("[CONNECTED] new client -> %s from %s", conn, addr)
        conn.setblocking(False)
        self.selector.register(conn, selectors.EVENT_READ, self.read)

    def read(self, conn, mask):
        
        data = CDProto.recv_msg(conn)
        logging.debug("[RECIVED] new message recieved: %s", data)
        
        if data:
            
            if data.com == "Register":
                
                self.conn_list[conn] = data.user
                self.Channel[conn].append('None')
            elif data.com == "Join":
                
                chnl = data.channel
                if chnl in self.Channel:
                    
                    self.Channel[chnl].append(conn)
                else:    
                    self.Channel[chnl] = [conn]
            else:
                
                if data.channel == "None":
                    
                    for connections in self.conn_list:
                        
                        CDProto.send_msg(connections, CDProto.message(data.message))
                        logging.debug("[SENT] new message: %s sent to: %s",data.message, self.conn_list[connections])
                        
                else:
                    channel_list = self.Channel[data.channel]
                    for connections in channel_list:
                        CDProto.send_msg(connections, CDProto.message(data.message))
                        logging.debug("[SENT] new message: %s sent to: %s",data.message, self.conn_list[connections])
        
        else:
            print("closing: ", conn)
            logging.debug("[CLOSE] client Socket closed: %s", self.conn_list[conn])
            self.conn_list.pop(conn)
            self.selector.unregister(conn)
            conn.close()     
        
    def loop(self):
        """Loop indefinetely."""
        while True:
            events = self.selector.select()
            for key, mask in events:
                callback = key.data
                callback(key.fileobj, mask)

