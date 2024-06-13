"""Message Broker"""
import enum
import socket
from typing import Dict, List, Any, Tuple
from .protocol import CDProto, CDProtoBadFormat
import selectors
from src.log import get_logger


class Serializer(enum.Enum):
    """Possible message serializers."""

    JSON = 0
    XML = 1
    PICKLE = 2


class Broker:
    """Implementation of a PubSub Message Broker."""

    def __init__(self):
        """Initialize broker."""
        self.canceled = False
        self._host = "localhost"
        self._port = 5000
        # self.logger = get_logger(f"Broker ({self._host},{self._port})")
        # self.logger.info("[SERVER]: initialized on [PORT] -> 5002")

        self.broker = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.broker.bind((self._host,self._port))
        self.selector = selectors.DefaultSelector()
        self.broker.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.broker.listen()
        
        self.topics = [] #contains all topics available -> [topic1, topic2, ...]
        self.messages = {} #contains all topics available and their last message -> {topic1: lastmsg, topic2: lastmsg, ...}
        self.clients = {} # contains relevant information of all clients -> {conn1: (serializer1,middlewareType1), ....}
        self.subscriptions = {} #contains all CONSUMER subscriptions of all the topics-> {topic1: [(conn1,topic2),(conn3,topic1)], .....}

        self.selector.register(self.broker, selectors.EVENT_READ, self.accept)

    def accept(self, broker, mask):
        conn, addr = broker.accept()
        # self.logger.info("[CONNECTED] new client -> %s from %s", conn, addr)
        # conn.setblocking(False)
        self.selector.register(conn, selectors.EVENT_READ, self.read)

    def read(self, conn, mask):      
        try:
            data = CDProto.recv_msg(conn)
            # self.logger.info("[RECEIVED] new message received: %s", data)
            
            if data:
                if data.com == "Subscribe":
                    self.subscribe(data.topic,conn,self.getSerial(conn))
                elif data.com == "Publish":
                    self.put_topic(data.topic,data.value)
                    if data.topic in self.subscriptions:
                        for consumer in self.list_subscriptions(data.topic):
                            CDProto.send_msg(consumer[0], data, self.getSerial(consumer[0]))
                    else:
                        self.subscriptions[data.com] = []
                elif data.com == "ListRequest":
                    CDProto.send_msg(conn,CDProto.ListRep(self.list_topics()),self.getSerial(conn))
                elif data.com == "UnSubscribe":
                    self.unsubscribe(data.topic,conn)
                elif data.com == "Ack":
                    self.ack(data.language,conn)
                else:
                    #se a msg que for recebida n for do tipo válido ??? se que isto não é preciso.
                    pass
            else:
                self.unsubscribe("", conn)
                self.selector.unregister(conn)
                conn.close()

        except ConnectionError:
            self.unsubscribe("", conn)
            self.selector.unregister(conn)
            conn.close()

    def list_topics(self) -> List[str]: # Em pricipio Feito
        """Returns a list of strings containing all topics containing values."""
        return [topic for topic, value in self.messages.items() if value is not None]

    def get_topic(self, topic):# Em pricipio Feito
        """Returns the currently stored value in topic."""
        return self.messages.get(topic, None)


    def put_topic(self, topic, value):# Em pricipio Feito
        """Store in topic the value."""

        if topic not in self.topics:
            self.topics.append(topic)
            self.subscriptions[topic] = []

            for topic2 in self.topics:
                if topic.startswith(topic2):
                    for consumer in self.subscriptions[topic2]:
                        if consumer not in self.subscriptions[topic]:
                            self.subscriptions[topic].append(consumer)
        
        self.messages[topic] = value

    def list_subscriptions(self, topic: str) -> List[Tuple[socket.socket, Serializer]]:# Em principio feito
        """Provide list of subscribers to a given topic."""
        lst = []
        for conn in self.subscriptions[topic]:
            lst.append((conn, self.getSerial(conn)))

        return lst
    
    
    def subscribe(self, topic: str, address: socket.socket, _format: Serializer = None):
        """Subscribe to topic by client in address."""
        if address not in self.clients:
            self.ack(_format, address)

        if topic in self.topics:
            if topic not in self.subscriptions:
                self.topics.append(topic)
                self.subscriptions[topic] = []
                for topic2 in self.topics:
                    if(topic.startswith(topic2)):
                        for consumer in self.subscriptions[topic2]:
                            if consumer not in self.subscriptions[topic]:
                                self.subscriptions[topic].append(consumer)
            if address not in self.subscriptions[topic]:
                self.subscriptions[topic].append(address)

            if topic in self.messages and self.messages[topic] is not None:
                CDProto.send_msg(address, CDProto.Pub(topic, self.messages[topic]), self.getSerial(address))
            return
        else:
            self.put_topic(topic, None)
            self.subscribe(topic, address, _format)
    
    def unsubscribe(self, topic, address): # Em principio feito
        """Unsubscribe to topic by client in address."""
        if topic != "":
            for t in self.topics:
                if(t.startswith(topic)):
                    self.subscriptions[t].remove(address)
        else:
            for t in self.topics:
                if(address in self.subscriptions[t]):
                    self.subscriptions[t].remove(address)

    
                

    def getSerial(self,conn):
        """Get the serializer associated with a given client connection."""
        return self.clients.get(conn, None)


    def ack(self, language, conn):
        """Send Acknowledgement to client."""
        if language == 0 or language == Serializer.JSON:
            self.clients[conn] = Serializer.JSON
        elif language == 1 or language == Serializer.XML:
            self.clients[conn] = Serializer.XML
        elif language == 2 or language == Serializer.PICKLE:
            self.clients[conn] = Serializer.PICKLE

        
    def run(self):
        """Run until canceled."""
        while not self.canceled:
            events = self.selector.select()
            for key, mask in events:
                callback = key.data
                callback(key.fileobj, mask)
