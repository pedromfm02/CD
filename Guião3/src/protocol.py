import json
from datetime import datetime
from socket import socket
import pickle
import xml.etree.ElementTree as et
import enum


class MiddlewareType(enum.Enum):
    """Middleware Type."""

    CONSUMER = 1
    PRODUCER = 2

class Serializer(enum.Enum):
    """Possible message serializers."""

    JSON = 0
    XML = 1
    PICKLE = 2

class Message:
    """Message Type."""
    def __init__(self,com):
        self.com = com

    
class Subscribe(Message):
    """Message to subscribe a topic."""
    def __init__(self, com, topic):
        super().__init__(com)
        self.topic = topic

    def __repr__(self):
        return f'{{"command": "Subscribe", "topic": "{self.topic}"}}'
    
    def XML(self):
        return "<?xml version=\"1.0\"?><data command=\"{}\" topic=\"{}\"></data>".format("Subscribe", self.topic)

    def Pickle(self):
        return {"command": "Subscribe", "topic": self.topic}


class Publish(Message):
    """Message to publish, value in topic."""
    def __init__(self, com, topic, value):
        super().__init__(com)
        self.topic = topic
        self.value = value
    
    def __repr__(self):
        return f'{{"command": "Publish", "topic": "{self.topic}", "value": "{self.value}"}}'
    
    def XML(self):
        return "<?xml version=\"1.0\"?><data command=\"{}\" topic=\"{}\" value=\"{}\"></data>".format("Publish", self.topic, self.value)

    def Pickle(self):
        return {"command": "Publish", "topic": self.topic, "value": self.value}

    
class ListRequest(Message):
    """Message to request a list of all the topics."""
    def __init__(self, com):
        super().__init__(com)

    def __repr__(self):
         return f'{{"command": "ListRequest"}}'
    
    def XML(self):
        return "<?xml version=\"1.0\"?><data command=\"{}\"></data>".format("ListRequest")

    def Pickle(self):
        return {"command": "ListRequest"}
    
class ListReply(Message):
    """Message to return a list of all the topics."""
    def __init__(self, com, topic_list):
        super().__init__(com)
        self.topic_list = topic_list

    def __repr__(self):
        return f'{{"command": "ListReply", "topic_list": "{self.topic_list}"}}'
    
    def XML(self):
        return "<?xml version=\"1.0\"?><data command=\"{}\" topic_list=\"{}\"></data>".format("ListReply",self.topic_list)

    def Pickle(self):
        return {"command": "ListReply", "topic_list": self.topic_list}

    
class UnSubscribe(Message):
    """Message to cancel subscription of a topic."""
    def __init__(self, com,topic):
        super().__init__(com)
        self.topic = topic

    def __repr__(self):
         return f'{{"command": "UnSubscribe", "topic": "{self.topic}"}}'
    
    def XML(self):
        return "<?xml version=\"1.0\"?><data command=\"{}\" topic=\"{}\"></data>".format("UnSubscribe", self.topic)

    def Pickle(self):
        return {"command": "UnSubscribe", "topic": self.topic}


    
class Ack(Message):
    """Message to acknowledge a message."""
    def __init__(self, language):
        super().__init__("Ack")
        self.language = language

    def __repr__(self):
        return f'{{"command": "Ack", "language": "{self.language}"}}'
    
    def XML(self):
        return "<?xml version=\"1.0\"?><data command=\"{}\" language=\"{}\"></data>".format("Ack", self.language)
    
    def Pickle(self):
        return {"command": "Ack", "language": self.language}


class CDProto:
    """Computação Distribuida Protocol."""

    @classmethod
    def Sub(cls, topic) -> Subscribe:
        """Creates a Subscribe object."""
        return Subscribe("Subscribe",topic)

    @classmethod
    def Pub(cls, topic, value) -> Publish:
        """Creates a Publish object."""
        return Publish("Publish",topic,value)
    
    @classmethod
    def ListReq(cls) -> ListRequest:
        """Creates a ListRequest object."""
        return ListRequest("ListRequest")
    
    @classmethod
    def ListRep(cls, topic_list) -> ListReply:
        """Creates a ListReply object."""
        return ListReply("ListReply",topic_list)
    
    @classmethod
    def UnSub(cls,topic) -> UnSubscribe:
        """Creates an UnSubscribe object."""
        return UnSubscribe("UnSubscribe",topic)

    # @classmethod
    # def Reg(cls,client_type:MiddlewareType,serializer:Serializer) -> Register:
    #     """Creates a Register object."""
    #     return Register("Register",client_type,serializer)
    
    # @classmethod
    # def Msg(cls,msg) -> TextMessage:
    #     """Creates a Register object."""
    #     return TextMessage("TextMessage",msg)

    @classmethod
    def Ack(cls,language) -> Ack:
        """Creates an Ack object."""
        return Ack(language)
    
    @classmethod
    def send_msg(cls, connection: socket, msg: Message, serializer:Serializer):#possivelmete tenho de fzr isto doutra forma
        """Sends through a connection a Message object."""
        if serializer == None:
            serializer = 0
        if type(serializer) == str:
            serializer = int(serializer)
        if isinstance(serializer, enum.Enum):
            serializer = serializer.value

        connection.send(serializer.to_bytes(1, 'big'))            # first we send the serializer
        if serializer == 0 or serializer == Serializer.JSON:
            temp = json.loads(msg.__repr__())
            jsonMsg = json.dumps(temp).encode('utf-8')          # get message in JSON
            connection.send(len(jsonMsg).to_bytes(2, 'big'))          # send header
            connection.send(jsonMsg)                                  # send message
        elif serializer == 1 or serializer == Serializer.XML:
            xmlMsg = msg.XML().encode('utf-8')                # get message in XML
            connection.send(len(xmlMsg).to_bytes(2, 'big'))           # send header
            connection.send(xmlMsg)                                   # send message
        elif serializer == 2 or serializer == Serializer.PICKLE:
            pickleMsg = pickle.dumps(msg.Pickle())            # get message in Pickle
            connection.send(len(pickleMsg).to_bytes(2, 'big'))        # send header
            connection.send(pickleMsg)                                # send message

    @classmethod
    def recv_msg(cls, connection: socket) -> Message:
            """Receives through a connection a Message object."""
        # try:
            code = int.from_bytes(connection.recv(1), 'big')  # first we receive the serializer
            header = int.from_bytes(connection.recv(2), 'big')  # then we receive the header
            
            if header == 0:
                return None

            if code == 0:
                try:
                    # print("header:",header)
                    message = connection.recv(header).decode("utf-8")
                    dict_msg = json.loads(message)
                except json.JSONDecodeError as err:
                    print("JSON decoding error:", err)
                    raise CDProtoBadFormat(message)
            
            elif code == 1:
                try:
                    message = connection.recv(header).decode("utf-8")
                    dict_msg = {}                                      
                    root = et.fromstring(message)
                    for element in root.keys():
                        dict_msg[element] = root.get(element)
                except et.ParseError as err:
                    raise CDProtoBadFormat(message)
            
            elif code == 2:
                try:
                    message = connection.recv(header)
                    dict_msg = pickle.loads(message)
                except pickle.UnpicklingError as err:
                    raise CDProtoBadFormat(message)
            
            if dict_msg["command"] == "Subscribe":
                return CDProto.Sub(dict_msg["topic"])
            elif dict_msg["command"] == "Publish":
                return CDProto.Pub(dict_msg["topic"],dict_msg["value"])
            elif dict_msg["command"] == "ListRequest":
                return CDProto.ListReq()
            elif dict_msg["command"] == "UnSubscribe":
                return CDProto.UnSub(dict_msg["topic"])
            elif dict_msg["command"] == "ListReply":
                return CDProto.ListRep(dict_msg["topic_list"])
            elif dict_msg["command"] == "Ack":
                return CDProto.Ack(dict_msg["language"])
        # except ConnectionError as err:
        #     print("Connection error:", err)
        #     return None
    

class CDProtoBadFormat(Exception):
    """Exception when source message is not CDProto."""

    def __init__(self, original_msg: bytes=None) :
        """Store original message that triggered exception."""
        self._original = original_msg

    @property
    def original_msg(self) -> str:
        """Retrieve original message as a string."""
        return self._original.decode("utf-8")