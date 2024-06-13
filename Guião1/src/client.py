"""CD Chat client program"""
import logging
import sys
import fcntl
import os
import selectors
import socket

from .protocol import CDProto, CDProtoBadFormat

logging.basicConfig(filename=f"{sys.argv[0]}.log", level=logging.DEBUG)


class Client:
    """Chat Client process."""

    def __init__(self, name: str = "Foo"):
        """Initializes chat client."""
        self.name = name
        self.cltsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.selector = selectors.DefaultSelector()
        self.adress = ("localhost", 5005)
        logging.debug("[CLIENT] Initialized name ->", self.name)
        print("[CLIENT] Initialized name ->", self.name)
        self.channel = "None"
        

    def connect(self):
        """Connect to chat server and setup stdin flags."""
        self.cltsocket.connect(self.adress)
        logging.debug("[CONNECTED] to server")
        self.selector.register(self.cltsocket,selectors.EVENT_READ,self.receive)
        register_sms = CDProto.register(self.name)
        CDProto.send_msg(self.cltsocket,register_sms)
        logging.debug("[SENT] register message to server")

    def receive(self,mask):
        data = CDProto.recv_msg(self.cltsocket)
        if data:
            logging.debug("[RECIVIED] new message recieved: %s", data)
            if data.com == "Message":
                print(data.message)
        

    def got_keyboard_data(self,stdin):
        user_input = stdin.read().rstrip("\n")
        cmd = user_input.split(" ")
        
        if cmd[0].lower() == "/join": 
            if len(cmd) > 1:
                chnl = cmd[1:]
                self.channel = chnl[0]
                logging.debug("utilizador quer juntar-se ao canal: %s", self.channel)
                CDProto.send_msg(self.cltsocket,CDProto.join(self.channel))
            else:
                logging.debug("[ERRO] Por favor introduza este comando da seguinte maneira:\n /join <nome do canal>")
        elif cmd[0].lower() == "exit":
            logging.debug("[CLIENT] Terminated!")
            print("[CLIENT] Terminated!")
            self.selector.unregister(self.cltsocket)
            self.cltsocket.close()
        else:
            CDProto.send_msg(self.cltsocket,CDProto.message(user_input,self.channel))
            logging.debug("[SENT] new message: %s, sent to channel: %s",user_input,self.channel)


    def loop(self):
        """Loop indefinetely."""
        
        orig_fl = fcntl.fcntl(sys.stdin, fcntl.F_GETFL)
        fcntl.fcntl(sys.stdin, fcntl.F_SETFL, orig_fl | os.O_NONBLOCK)
        self.selector.register(sys.stdin, selectors.EVENT_READ, self.got_keyboard_data)
        logging.debug('Client initialzed, type commands: \n')
        sys.stdout.write('Client initialzed, type commands: \n')
        sys.stdout.flush()
        while True:
            
            for k, mask in self.selector.select():
                callback = k.data
                callback(k.fileobj)
