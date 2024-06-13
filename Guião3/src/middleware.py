"""Middleware to communicate with PubSub Message Broker."""
from collections.abc import Callable
from enum import Enum
from queue import LifoQueue, Empty
import selectors
import socket
import pickle
from typing import Any

from .protocol import CDProto, Serializer

class MiddlewareType(Enum):
    """Middleware Type."""

    CONSUMER = 1
    PRODUCER = 2


class Queue:
    """Representation of Queue interface for both Consumers and Producers."""

    def __init__(self, topic, _type=MiddlewareType.CONSUMER):
        """Create Queue."""
        self.topic = topic
        self.type = _type
        self.queue = LifoQueue()
        self.serializer = Serializer.JSON
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.port = 5000
        self.socket.connect(("localhost", self.port))
        # self.selector = selectors.DefaultSelector()
        # self.selector.register(self.socket, selectors.EVENT_READ, self.pull)

    def push(self, value):
        """Sends data to broker."""
        if self.type == MiddlewareType.PRODUCER:
            CDProto.send_msg(self.socket, CDProto.Pub(self.topic, value), self.serializer)

    def pull(self) -> (str, Any):
        """Receives (topic, data) from broker.

        Should BLOCK the consumer!"""
        msg = CDProto.recv_msg(self.socket)
        if msg is None or msg.value is None:
            return None
        if msg.com == "ListReply":
            return msg.topic_list
        else:
            return msg.topic, int(msg.value)


    def list_topics(self, callback: Callable):
        """Lists all topics available in the broker."""
        # print("List of topics:")
        msg = CDProto.ListReq()
        CDProto.send_msg(self.socket, msg, self.serializer)
        # self.selector.select()
        # callback(self.pull())

    def cancel(self):
        """Cancel subscription."""
        msg = CDProto.UnSub(self.topic)
        CDProto.send_msg(self.socket, msg, self.serializer)
        # self.socket.close()

    def subscribe(self, topic):
        """Subscribe to a topic."""
        msg = CDProto.Sub(topic)
        CDProto.send_msg(self.socket, msg, self.serializer)


class JSONQueue(Queue):
    """Queue implementation with JSON based serialization."""
    def __init__(self, topic, _type=MiddlewareType.CONSUMER):
        """Create Queue."""
        super().__init__(topic, _type)
        self.serializer = Serializer.JSON

        # CDProto.send_msg(self.socket, CDProto.ListReq(), Serializer.JSON)
        # CDProto.send_msg(self.socket, CDProto.Reg( self.type, self.topic), Serializer.JSON)
        if _type.value == MiddlewareType.CONSUMER.value:
            # print("serializer -> ", self.serializer)
            CDProto.send_msg(self.socket, CDProto.Ack(language=self.serializer), self.serializer)
            CDProto.send_msg(self.socket, CDProto.Sub(topic), self.serializer)

class XMLQueue(Queue):
    """Queue implementation with XML based serialization."""
    def __init__(self, topic, _type=MiddlewareType.CONSUMER):
        """Create Queue."""
        super().__init__(topic, _type)
        self.serializer = Serializer.XML

        if _type.value == MiddlewareType.CONSUMER.value:
            CDProto.send_msg(self.socket, CDProto.Ack(self.serializer), self.serializer)
            CDProto.send_msg(self.socket, CDProto.Sub(topic), self.serializer)

class PickleQueue(Queue):
    """Queue implementation with Pickle based serialization."""
    def __init__(self, topic, _type=MiddlewareType.CONSUMER):
        """Create Queue."""
        super().__init__(topic, _type)
        self.serializer = Serializer.PICKLE

        if _type.value == MiddlewareType.CONSUMER.value:
            CDProto.send_msg(self.socket, CDProto.Ack(self.serializer), self.serializer)
            CDProto.send_msg(self.socket, CDProto.Sub(topic), self.serializer)

