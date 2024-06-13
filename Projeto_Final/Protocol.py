"""Protocol for p2p sudoku solver - Computação Distribuida Project."""

class Message:
    """Message Type."""
    def __init__(self,com):
        self.com = com

    
class JoinRequest(Message):
    """Message to request connection with node."""
    def __init__(self, com):
        super().__init__(com)

    def pickle(self):
        return {"command": "join_req"}
    
class JoinAnswer(Message):
    """Message to confirm or not the join request."""
    def __init__(self, com, answer:str,num_nodes):
        super().__init__(com)
        self.answer = answer
        self.num_nodes = num_nodes

    def pickle(self):
        return {"command": "join_ans", "answer": self.answer, "NodesNum": self.num_nodes}

class NodeShutdown(Message):
    """Message to inform the network that this node is not working anymore."""
    def __init__(self, com,addr,lst_addr):
        super().__init__(com)
        self.addr = addr
        self.lst_addr = lst_addr
    
    def pickle(self):
        return {"command": "node_down","address": self.addr, "NodeSent": self.lst_addr}

class NodeRequest(Message):
    """Message to request connection with node."""
    def __init__(self, com):
        super().__init__(com)

    def pickle(self):
        return {"command": "node_req"}
    
class NodeAnswer(Message):
    """Message to confirm or not the node request."""
    def __init__(self, com,node_addr):
        super().__init__(com)
        self.node_addr = node_addr

    def pickle(self):
        return {"command": "node_ans","address": self.node_addr}
    
class NumNodesUpdate(Message):
    """Message to confirm or not the join request."""
    def __init__(self, com, num_nodes, lst_addr):
        super().__init__(com)
        self.lst_addr = lst_addr
        self.num_nodes = num_nodes

    def pickle(self):
        return {"command": "update", "NodesNum": self.num_nodes, "NodeSent": self.lst_addr}

class StatsRequest(Message):
    """Message to request number o validations."""
    def __init__(self, com, req_addr,lst_addr,req_id):
        super().__init__(com)
        self.req_addr = req_addr
        self.lst_addr = lst_addr
        self.req_id = req_id

    def pickle(self):
        return {"command": "stats_req","address": self.req_addr, "NodeSent": self.lst_addr, "req_id": self.req_id}
    
class StatsAnswer(Message):
    """Message to send the number of validations."""
    def __init__(self, com, validation:int,solved:int,req_id):
        super().__init__(com)
        self.val = validation
        self.solved = solved
        self.req_id = req_id

    def pickle(self):
        return {"command": "stats_ans", "validation": self.val, "solved": self.solved, "req_id": self.req_id}

class StatsHistory(Message):
    """Message to send the number of validations."""
    def __init__(self, com, nodes_stats,lst_addr):
        super().__init__(com)
        self.nodes_stats = nodes_stats
        self.lst_addr = lst_addr

    def pickle(self):
        return {"command": "stats_hist", "history": self.nodes_stats, "NodeSent": self.lst_addr}
    
class NetworkRequest(Message):
    """Message to request network connections."""
    def __init__(self, com, req_addr,lst_addr,req_id):
        super().__init__(com)
        self.req_addr = req_addr
        self.lst_addr = lst_addr
        self.req_id = req_id

    def pickle(self):
        return {"command": "network_req","address": self.req_addr, "NodeSent": self.lst_addr, "req_id": self.req_id}
    
class NetworkAnswer(Message):
    """Message to send the network connections."""
    def __init__(self, com, network:list,req_id):
        super().__init__(com)
        self.network = network
        self.req_id = req_id

    def pickle(self):
        return {"command": "network_ans", "network": self.network, "req_id": self.req_id}

class SolveRequest(Message):
    """Message to request the solving od sudoku."""
    def __init__(self, com, sudoku:list,req_addr,lst_addr,req_id, is_sub_request=False):
        super().__init__(com)
        self.sudoku = sudoku
        self.req_addr = req_addr
        self.lst_addr = lst_addr
        self.req_id = req_id
        self.is_sub_request = is_sub_request

    def pickle(self):
        return {"command": "solve_req", "sudoku": self.sudoku,"address": self.req_addr, "NodeSent": self.lst_addr, "req_id": self.req_id, "is_sub_request": self.is_sub_request}
    
class SolveAnswer(Message):
    """Message to send solution of sudoku."""
    def __init__(self, com, sudoku:list,req_id):
        super().__init__(com)
        self.sudoku = sudoku
        self.req_id = req_id

    def pickle(self):
        return {"command": "solve_ans", "sudoku": self.sudoku, "req_id": self.req_id}
    
class SolveStop(Message):
    """Message to warn that the sudoku puzzle has been solved."""
    def __init__(self, com,lst_addr,req_id):
        super().__init__(com)
        self.lst_addr = lst_addr
        self.req_id = req_id

    def pickle(self):
        return {"command": "solved","NodeSent": self.lst_addr, "req_id": self.req_id}

class KeepAlive(Message):
    """Message to warn that the sudoku puzzle has been solved."""
    def __init__(self, com):
        super().__init__(com)

    def pickle(self):
        return {"command": "alive"}

# class List(Message):
#     """Message to warn that the sudoku puzzle has been solved."""
#     def __init__(self, com,grid):
#         super().__init__(com)
#         self.grid = grid

#     def pickle(self):
#         return {"command": "sudoku_part", "grid": self.grid}

class CDProto:
    """Computação Distribuida Protocol."""

    @classmethod
    def join_req(cls) -> JoinRequest:
        """Creates a JoinRequest object."""
        return JoinRequest("join_req")
    
    @classmethod
    def join_ans(cls,answer,num_nodes) -> JoinAnswer:
        """Creates a JoinAnswer object."""
        return JoinAnswer("join_ans",answer,num_nodes)
    
    @classmethod
    def NumUpdate(cls,num_nodes,lst_addr) -> NumNodesUpdate:
        """Creates a NumNodesUpdate object."""
        return NumNodesUpdate("update",num_nodes,lst_addr)

    @classmethod
    def node_down(cls,addr,lst_addr) -> NodeShutdown:
        """Creates a NodeShutdown object."""
        return NodeShutdown("node_down",addr,lst_addr)

    @classmethod
    def node_req(cls) -> NodeRequest:
        """Creates a NodeRequest object."""
        return NodeRequest("node_req")
    
    @classmethod
    def node_ans(cls,node_addr) -> NodeAnswer:
        """Creates a NodeAnswer object."""
        return NodeAnswer("node_ans",node_addr)  
    
    @classmethod
    def stats_req(cls,req_addr,lst_addr,req_id) -> StatsRequest:
        """Creates a StatsRequest object."""
        return StatsRequest("stats_req",req_addr,lst_addr,req_id)
    
    @classmethod
    def stats_ans(cls,validation,solved,req_id) -> StatsAnswer:
        """Creates a StatsAnswer object."""
        return StatsAnswer("stats_ans",validation,solved,req_id)
    
    @classmethod
    def stats_hist(cls,nodes_stats,lst_addr) -> StatsHistory:
        """Creates a StatsHistory object."""
        return StatsHistory("stats_hist",nodes_stats,lst_addr)
    
    @classmethod
    def net_req(cls,req_addr,lst_addr,req_id) -> NetworkRequest:
        """Creates a NetworkRequest object."""
        return NetworkRequest("network_req",req_addr,lst_addr,req_id)
    
    @classmethod
    def net_ans(cls,network,req_id) -> NetworkAnswer:
        """Creates a NetworkAnswer object."""
        return NetworkAnswer("network_ans",network,req_id)
    
    @classmethod
    def solve_req(cls,sudoku,addr,lst_addr,req_id, is_sub_request=False) -> SolveRequest:
        """Creates a SolveRequest object."""
        return SolveRequest("solve_req",sudoku,addr,lst_addr,req_id, is_sub_request)
    
    @classmethod
    def solve_ans(cls,sudoku,req_id) -> SolveAnswer:
        """Creates a SolveAnswer object."""
        return SolveAnswer("solve_ans",sudoku,req_id)
    
    @classmethod
    def solve_stop(cls,lst_addr,req_id) -> SolveStop:
        """Creates a SolveStop object."""
        return SolveStop("solved",lst_addr,req_id)
    
    @classmethod
    def alive(cls) -> KeepAlive:
        """Creates a KeepAlive object."""
        return KeepAlive("alive")
    
    #@classmethod
    #def sudoku_part(cls,grid):
    #    """Creates a list of sudoku parts."""
    #    return List("sudoku_part",grid)
    
class CDProtoBadFormat(Exception):
    """Exception when source message is not CDProto."""

    def __init__(self, original_msg: bytes=None) :
        """Store original message that triggered exception."""
        self._original = original_msg

    @property
    def original_msg(self) -> str:
        """Retrieve original message as a string."""
        return self._original.decode("utf-8")
