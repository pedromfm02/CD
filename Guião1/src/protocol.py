"""Protocol for chat server - Computação Distribuida Assignment 1."""
import json
from datetime import datetime
from socket import socket
import errno


class Message:
    """Message Type."""
    def __init__(self,com):
        self.com = com

    
class JoinMessage(Message):
    """Message to join a chat channel."""
    def __init__(self, com, channel):
        super().__init__(com)
        self.channel = channel

    def __repr__(self):
        return f'{{"command": "join", "channel": "{self.channel}"}}'


class RegisterMessage(Message):
    """Message to register username in the server."""
    def __init__(self, com, user:str):
        super().__init__(com)
        self.user = user
    
    def __repr__(self):
        return f'{{"command": "register", "user": "{self.user}"}}'
    
class TextMessage(Message):
    """Message to chat with other clients."""
    def __init__(self, com, message, ts, channel=None):
        super().__init__(com)
        self.message = message
        self.channel = channel
        self.ts = ts

    def __repr__(self):
        if self.channel == None:
            return f'{{"command": "message", "message": "{self.message}", "ts": {self.ts}}}'
        else:
            return f'{{"command": "message", "message": "{self.message}", "channel": "{self.channel}", "ts": {self.ts}}}'

class CDProto:
    """Computação Distribuida Protocol."""

    @classmethod
    def register(cls, username: str) -> RegisterMessage:
        """Creates a RegisterMessage object."""
        return RegisterMessage("Register",username)

    @classmethod
    def join(cls, channel: str) -> JoinMessage:
        """Creates a JoinMessage object."""
        return JoinMessage("Join",channel)
    @classmethod
    def message(cls, message: str, channel: str = None) -> TextMessage:
        """Creates a TextMessage object."""
        return TextMessage("Message",message,int(datetime.now().timestamp()),channel) # último parametro fornece o timestamp pedido.

    @classmethod
    def send_msg(cls, connection: socket, msg: Message):
        """Sends through a connection a Message object."""
        if type(msg) is RegisterMessage:
            msg_to_send = json.dumps({"command": "register", "user": msg.user}).encode("utf-8")
        elif type(msg) is JoinMessage:
            msg_to_send = json.dumps({"command": "join", "channel": msg.channel}).encode("utf-8")
        elif type(msg) is TextMessage:
            msg_to_send = json.dumps({"command": "message", "message": msg.message, "channel": msg.channel, "ts": msg.ts}).encode("utf-8")

        header = len(msg_to_send).to_bytes(2,"big")
        try:
            connection.sendall(header+msg_to_send)
        except IOError as err:
            if err.errno == errno.EPIPE:
                print(err)

    @classmethod
    def recv_msg(cls, connection: socket) -> Message:
        """Receives through a connection a Message object."""
        header = int.from_bytes(connection.recv(2),"big")
        
        if header == 0:
            return None
        message = connection.recv(header).decode("utf-8")
        try:
            dict_msg = json.loads(message)
        except json.JSONDecodeError as err:
            raise CDProtoBadFormat(message)
        
        if dict_msg["command"] == "register":
            return CDProto.register(dict_msg["user"])
        elif dict_msg["command"] == "join":
            return CDProto.join(dict_msg["channel"])
        else:
            if "channel" in dict_msg:
                return CDProto.message(dict_msg["message"],dict_msg["channel"])
            else: 
                return CDProto.message(dict_msg["message"],None)

class CDProtoBadFormat(Exception):
    """Exception when source message is not CDProto."""

    def __init__(self, original_msg: bytes=None) :
        """Store original message that triggered exception."""
        self._original = original_msg

    @property
    def original_msg(self) -> str:
        """Retrieve original message as a string."""
        return self._original.decode("utf-8")
