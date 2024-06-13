import socket
import threading
import pickle
from log import get_logger
import time 
import random

from Protocol import CDProto,CDProtoBadFormat
from sudoku import Sudoku

class P2PServer(threading.Thread):

    def __init__(self, address, join_addr, handicap,timeout=3):
        threading.Thread.__init__(self)
        #self.count = 0
        self.addr = address
        self.join_addr = join_addr
        self.handicap = handicap
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.settimeout(timeout)
        self.logger = get_logger("")
        self.logger.info(f"Initializing node")
        self.nodes_stats = {}
        self.connections = []
        self.num_nodes = 1
        self.validations = 0
        self.num_solved = 0
        self.lost_con = False
        self.last_sent_addr = address
        self.request_id = 0

        self.stats_events = {}
        self.network_events = {}
        self.solve_events = {}
        self.solve_api_events = {}

    # def divide_sudoku(self) -> List[List[List[int]]]:
    #     """Divide o Sudoku original em subgrids para distribuição entre os nós."""
    #     subgrids = []
    #     for row_start in range(0, self.grid_size, self.subgrid_size):
    #         for col_start in range(0, self.grid_size, self.subgrid_size):
    #             subgrid = []
    #             for i in range(self.subgrid_size):
    #                 for j in range(self.subgrid_size):
    #                     subgrid.append(self.original_sudoku[row_start + i][col_start + j])
    #             subgrids.append(subgrid)
    #     return subgrids


#------------------------------------- funções de envio e receção de mensagens-----------------------------------------
    def send(self, address, msg):
        """ Send msg to address. """           
        # if address not in self.connections:
        #     # Encaminha a mensagem para o próximo nó na lista de conexões se necessário
        #     next_node = self.connections[self.connections.index(address) + 1] if address in self.connections else None
        #     if next_node:
        #         self.send(next_node, msg)
        #         return
        send = True
        if self.lost_con:
            send = False
            com = msg["command"]
            if com == "node_req" or com == "node_ans" or com == "node_down" or com == "update" or com == "alive":
                send = True
        
        while self.lost_con and not send:
            pass
        
        payload = pickle.dumps(msg)
        self.last_sent_addr = address
        self.socket.sendto(payload, address)
        self.logger.info(f"[SENT TO]: {address}, [MSG]: {str(msg)}")
        
    def recv(self):
        """ Retrieve msg payload and from address."""
        try:
            payload, addr = self.socket.recvfrom(1024)
        except socket.timeout:
            return None, None
        except (ConnectionResetError, OSError) as e:
            self.lost_con = True
            self.logger.error(f"Connection Lost: {self.last_sent_addr}, Error: {e}")
            self.handle_disconnection(self.last_sent_addr)
            return None, None

        if len(payload) == 0:
            return None, addr
        try:
            dict_msg = pickle.loads(payload)
        except pickle.UnpicklingError as err:
            raise CDProtoBadFormat(payload)

        return dict_msg, addr
    
    def prop_messages(self, lst_addr:list):
        lst_sendto = []
        for con in self.connections:
            if con not in lst_addr:
                lst_sendto.append(con)
                lst_addr.append(con)
        return lst_addr, lst_sendto

    def handle_disconnection(self,address):
        if address in self.connections:
            self.connections.remove(address)
        self.logger.debug(f"[connections]: {self.connections}")
        self.num_nodes -= 1
        list_send = []
        list_send += self.connections
        list_send.append(self.addr)
        
        for con in self.connections:
            self.send(con,CDProto.node_down(address,list_send).pickle())
        
        for con in self.connections:
            self.send(con,CDProto.NumUpdate(self.num_nodes,list_send).pickle())

        self.lost_con = False
            
#------------------------------------- função que responde ao endpoint /stats -----------------------------------------
    def stats(self):
        self.logger.info("Handling stats request")
        stat_event = threading.Event()
        stats_ans = {}
        self.request_id += 1
        reqId = self.request_id 
        self.stats_events[(reqId,self.addr)] = (stat_event, stats_ans)
        total_solved = 0
        total_val = 0
        list_send = []
        list_send += self.connections
        list_send.append(self.addr)

        response = {"all": {"solved": 0, "validations": 0}, "nodes": []}
        if self.validations != 0:
            self.nodes_stats[f"{self.addr[0]}:{self.addr[1]}"] = [self.validations, self.num_solved]

        for con in self.connections:
            self.send(con, CDProto.stats_req(self.addr, list_send, (reqId,self.addr)).pickle())
        
        self.logger.info("Waiting for stats response")
        stat_event.wait()
        self.logger.info("Received stats response")

        for addr in stats_ans:
            msg = stats_ans[addr]
            if msg["validation"] != 0:
                self.nodes_stats[f"{addr[0]}:{addr[1]}"] = [msg["validation"], msg["solved"]]

        for con in self.connections:
            self.send(con, CDProto.stats_hist(self.nodes_stats, list_send).pickle())
        
        for addr in self.nodes_stats:
            response["nodes"].append({"address": addr, "validations": self.nodes_stats[addr][0]})
            total_solved += self.nodes_stats[addr][1]
            total_val += self.nodes_stats[addr][0]
        
        del self.stats_events[(reqId,self.addr)]
        response["all"]["solved"] = total_solved
        response["all"]["validations"] = total_val

        self.logger.info(f"Stats response: {response}")
        return response

    #------------------------------------- função que responde ao endpoint /network -----------------------------------------
    def network(self):
        if not self.connections:
            self.logger.warning("No connections available")
            return {"error": "No connections available"}

        net_event = threading.Event()
        net_ans = {}
        self.request_id += 1
        reqId = self.request_id 
        self.network_events[(reqId,self.addr)] = (net_event, net_ans)
        list_send = []
        list_send += self.connections
        list_send.append(self.addr)

        for con in self.connections:
            self.send(con, CDProto.net_req(self.addr, list_send, (reqId,self.addr)).pickle())
        
        # Adição de log e tempo limite
        self.logger.info(f"Waiting for network response for request ID {(reqId,self.addr)}")
        net_event.wait(timeout=5)  # Adding a timeout to avoid indefinite wait
        
        if net_event.is_set():
            self.logger.info("Received network response")
            response = self.do_network_dict()
            for addr in net_ans:
                answer = net_ans[addr]["network"]
                for key in answer:
                    response[key] = answer[key]
            
            del self.network_events[(reqId,self.addr)]
            return response
        else:
            self.logger.error("Network request timed out")
            del self.network_events[(reqId,self.addr)]
            return {"error": "Network request timed out"}
    #----------------------- funções auxiliam o processo de resposta ao endpoint /network -------------------------------------    
    def do_network_dict(self):
        my_addr = f"{self.addr[0]}:{self.addr[1]}"
        net_dict = {my_addr: [f"{con[0]}:{con[1]}" for con in self.connections]}
        return net_dict
    
    #----------------------- resolução do sudoku e funções auxiliares -------------------------------------
    def solve_api(self, sudoku: dict):
        start=time.time()
        stop_event = threading.Event()
        solve_ans = {}
        ans = []
        self.request_id += 1
        reqId = self.request_id
        self.solve_api_events[(reqId,self.addr)] = [stop_event,solve_ans]
        list_send = [self.addr] + self.connections

        for con in self.connections:
            self.send(con,CDProto.solve_req(sudoku["sudoku"],self.addr,list_send,(reqId,self.addr)).pickle())

        #Encontra todas as celulas que precisam de numero.
        puzzle = Sudoku(sudoku["sudoku"])
        coords = puzzle.empty_coords()
        numbers = puzzle.possible_values_by_row()
        self.logger.debug(f"[Empty cells]: {coords}")
        self.logger.debug(f"[Puzzle]: {puzzle.grid}")
        self.logger.debug(f"[VALUES]: {numbers}")

        print("Solving the Sudoku puzzle...", puzzle.grid)
        
        while not self.solve_api_events[(reqId,self.addr)][0].is_set():
            self.logger.debug(f"[STOP]: {self.solve_api_events[(reqId,self.addr)][0].is_set()}")
            for coord in coords:
                nums = numbers[coord[0]]
                
                puzzle.grid[coord[0]][coord[1]] = random.choice(nums)
            self.validations += 1
            if puzzle.check() and not self.solve_api_events[(reqId,self.addr)][0].is_set():
                self.logger.info("[SUDOKU]: Finished")
                ans = puzzle.grid
                self.solve_api_events[(reqId,self.addr)][0].set()
        self.logger.debug(f"sai do loop")
        if ans == []:
            ans = self.solve_api_events[(reqId,self.addr)][1]
        
        for con in self.connections:
            self.send(con,CDProto.solve_stop(list_send,(reqId,self.addr)).pickle())
        
        
        end = time.time()
        duration = end-start
        self.logger.debug(f"[ANS2]: {self.solve_api_events[(reqId,self.addr)][1]}")
        self.logger.debug(f"[ANS3]: {ans}")
        del self.solve_api_events[(reqId,self.addr)]
        return ans,duration
    
    def num_solve_counter(self):
        self.num_solved += 1

    def solve(self,sudoku,addr,req_id):
        stop_event = threading.Event()
        self.solve_events[req_id] = stop_event
        
        puzzle = Sudoku(sudoku)
        coords = puzzle.empty_coords()
        numbers = puzzle.possible_values_by_row()
        self.logger.debug(f"[Empty cells]: {coords}")
        self.logger.debug(f"[Puzzle]: {puzzle.grid}")
        self.logger.debug(f"[VALUES]: {numbers}")

        print("Solving the Sudoku puzzle...", puzzle.grid)
        
        while not self.solve_events[req_id].is_set():
            self.logger.debug(f"[STOP]: {self.solve_events[req_id].is_set()}")
            for coord in coords:
                nums = numbers[coord[0]]
                
                puzzle.grid[coord[0]][coord[1]] = random.choice(nums)
            self.validations += 1
            if puzzle.check() and not self.solve_events[req_id].is_set():
                self.logger.info("[SUDOKU]: Finished")
                self.solve_events[req_id].set()
                self.logger.debug(f"[STOP]: {self.solve_events[req_id].is_set()}")
                self.send(addr,CDProto.solve_ans(puzzle.grid,req_id).pickle())
        self.logger.debug(f"sai do loop")
        del self.solve_events[req_id]
        return
      
    #----------------------- função run  -------------------------------------
    def keepAlive(self):
        for con in self.connections:
            self.send(con,CDProto.alive().pickle())
        alive_method = threading.Timer(interval=5,function=self.keepAlive)
        alive_method.start()
    
    def run(self):
        self.socket.bind(self.addr)
        port = self.addr[1]
        self.addr = (socket.gethostbyname_ex(socket.gethostname())[2][1], port)
        self.logger.info(f"[Node Address]: {self.addr}")

        if self.join_addr is not None:
            self.send(self.join_addr, CDProto.join_req().pickle())

        self.keepAlive()


        while True:
            if self.num_nodes <= len(self.connections):
                self.num_nodes = len(self.connections) + 1
                list_send = []
                list_send += self.connections
                list_send.append(self.addr)
                for con in self.connections:
                    print("list_send: ",list_send)
                    self.send(con, CDProto.NumUpdate(self.num_nodes, list_send).pickle())

            msg, addr = self.recv()
            if msg is not None:
                self.logger.info(f"[FROM]: {addr}, [RECEIVED]: {str(msg)}")

    #-------------------- handles the JoinRequest message ---------------------------(DONE) 
                if msg["command"] == "join_req":
                    self.num_nodes += 1
                    for con in self.connections:
                        self.send(con,CDProto.NumUpdate(self.num_nodes,self.connections).pickle())
                    self.connections.append(addr)
                    self.send(addr,CDProto.join_ans("ACK",self.num_nodes).pickle())

    #-------------------- handles the JoinAnswer message ---------------------------(DONE) 
                elif msg["command"] == "join_ans":
                    if msg["answer"] == "ACK":
                        self.connections.append(addr)
                        self.num_nodes = msg["NodesNum"]
                        if self.num_nodes > 2:
                            self.send(addr,CDProto.node_req().pickle())

    #-------------------- handles the NumNodesUpdate message ---------------------------(DONE)     
                elif msg["command"] == "update":
                        self.num_nodes = msg["NodesNum"]
                        if self.num_nodes > 2 and len(self.connections) == 1:
                            self.send(addr,CDProto.node_req().pickle())
                        else:
                            lst_addr, lst_send = self.prop_messages(msg["NodeSent"])
                            if lst_send != []:
                                for con in lst_send:
                                    self.send(con,CDProto.NumUpdate(self.num_nodes,lst_addr).pickle())

    #-------------------- handles the NodeShutdown message ---------------------------(DONE) 
                elif msg["command"] == "node_down":
                    if msg["address"] in self.connections:
                        self.connections.remove(msg["address"])
                    lst_addr, lst_send = self.prop_messages(msg["NodeSent"])
                    if lst_send != []:
                        for con in lst_send:
                            self.send(con,CDProto.node_down(msg["address"],lst_addr).pickle())

    #-------------------- handles the NodeRequest message ---------------------------(DONE)         
                elif msg["command"] == "node_req":
                    possible_nodes = []
                    for con in self.connections:
                        if con != addr:
                            possible_nodes.append(con)
                    if possible_nodes != []:
                        self.send(addr,CDProto.node_ans(possible_nodes[0]).pickle())
                        #self.send(possible_nodes[0],CDProto.node_ans(addr).pickle())
                    else:
                        self.send(addr,CDProto.node_ans(None).pickle())

    #-------------------- handles the NodeAnswer message ---------------------------(DONE) 
                elif msg["command"] == "node_ans":
                    if msg["address"] != None:
                        if msg["address"] not in self.connections:
                            self.connections.append(msg["address"])
                    else:
                        self.logger.info("There are no more nodes to connect to")#se que mudar esta mensagem

    #-------------------- handles the StatsRequest message ---------------------------(DONE) 
                elif msg["command"] == "stats_req":
                    print("stats_req: ",msg)
                    lst_addr, lst_send = self.prop_messages(msg["NodeSent"])
                    if lst_send != []:
                        for con in lst_send:
                            self.send(con,CDProto.stats_req(msg["address"],lst_addr,msg["req_id"]).pickle())
                    self.send(msg["address"],CDProto.stats_ans(self.validations,self.num_solved,msg["req_id"]).pickle())

    #-------------------- handles the StatsAnswer message ---------------------------(DONE) 
                elif msg["command"] == "stats_ans":
                    key = msg["req_id"]
                    self.stats_events[key][1][addr] = msg
                    if len(self.stats_events[key][1]) == self.num_nodes-1:
                        self.stats_events[key][0].set()

    #-------------------- handles the StatsHistory message ---------------------------(DONE) 
                elif msg["command"] == "stats_hist":
                    self.nodes_stats = msg["history"]
                    lst_addr, lst_send = self.prop_messages(msg["NodeSent"])
                    if lst_send != []:
                        for con in lst_send:
                            self.send(con,CDProto.stats_hist(self.nodes_stats,lst_addr).pickle())

    #-------------------- handles the NetworkRequest message ---------------------------(DONE) 
                elif msg["command"] == "network_req":
                    self.logger.info("Processing network request")
                    lst_addr, lst_send = self.prop_messages(msg["NodeSent"])
                    if lst_send != []:
                        for con in lst_send:
                            self.send(con,CDProto.net_req(msg["address"],lst_addr,msg["req_id"]).pickle())
                    self.send(msg["address"],CDProto.net_ans(self.do_network_dict(),msg["req_id"]).pickle())

    #-------------------- handles the NetworkAnswer message ---------------------------(DONE) 
                elif msg["command"] == "network_ans":
                    key = msg["req_id"]
                    
                    if key in self.network_events:
                        self.network_events[key][1][addr] = msg
                        if len(self.network_events[key][1]) == self.num_nodes-1:
                            self.network_events[key][0].set()
                    else:
                        self.logger.warning(f"Received network answer for unknown request ID {key}")

    #-------------------- handles the SolveRequest message ---------------------------
                elif msg["command"] == "solve_req":
                    lst_addr, lst_send = self.prop_messages(msg["NodeSent"])
                    if lst_send != []:
                        for con in lst_send:
                            self.send(con,CDProto.solve_req(msg["sudoku"],addr,lst_addr,msg["req_id"]).pickle())
                    solve_thread = threading.Thread(target=self.solve, args=(msg["sudoku"], addr, msg["req_id"]))
                    solve_thread.start()
    #-------------------- handles the SolveAnswer message ---------------------------
                elif msg["command"] == "solve_ans":
                    key = msg["req_id"]
                    if key in self.solve_api_events:
                        self.solve_api_events[key][0].set()
                        self.solve_api_events[key][1] = msg["sudoku"]
                        self.logger.debug(f"[stop]: {self.solve_api_events[key][0].is_set()}")
                        self.logger.debug(f"[ANS1]: {self.solve_api_events[key][1]}")

    #-------------------- handles the SolveStop message ---------------------------
                elif msg["command"] == "solved":
                    
                    lst_addr, lst_send = self.prop_messages(msg["NodeSent"])
                    if lst_send != []:
                        for con in lst_send:
                            self.send(con,CDProto.solve_stop(lst_addr,msg["req_id"]).pickle())
                    if msg["req_id"] in self.solve_events:
                        self.solve_events[msg["req_id"]].set()

    #-------------------- handles the Alive message ---------------------------
                elif msg["command"] == "alive":
                    if addr not in self.connections:
                        self.connections.append(addr)

    #         if self.num_nodes != 1:
    #             for i, con in enumerate(self.connections):
    #                 start_idx = i * (self.grid_size // len(self.connections))
    #                 end_idx = (i + 1) * (self.grid_size // len(self.connections))
    #                 part_of_sudoku = self.subgrids[start_idx:end_idx]
    #                 self.send(con, CDProto.sudoku_part(part_of_sudoku).pickle())
    #                 self.logger.info(f"Distribuída parte do Sudoku para {con}")

    #                 self.handle_sudoku_part(part_of_sudoku, con, self.request_id)
    # def partition_sudoku(self, sudoku, num_parts):
    #     """ Divide o Sudoku em partes para os diferentes nós. """
    #     print("sudoku: ", sudoku)
    #     sudokus = []
    #     sud_size = len(sudoku['sudoku']) // num_parts
    #     remaining = len(sudoku['sudoku']) % num_parts

    #     start = 0
    #     for i in range(num_parts):
    #         end = start + sud_size + (1 if remaining > 0 else 0)
    #         part = {'sudoku': sudoku['sudoku'][start:end]}

    #         # Calcula o nó correspondente para esta parte do Sudoku
    #         node_address = self.addr if i == 0 else self.connections[i - 1]

    #         sudokus.append((node_address, part))
    #         start = end
    #         if remaining > 0:
    #             remaining -= 1

    #     # print the partitioned sudokus
    #     print("sudokus: ", sudokus)
    #     return sudokus


    # def combine_sudoku_parts(self, solved_parts):
    #     """ Combina as partes do Sudoku resolvidas pelos diferentes nós. """
    #     print("solved_parts: ",solved_parts)
    #     combined_solution = []
    #     for part in solved_parts:
    #         if isinstance(part, dict) and 'sudoku' in part:
    #             sudoku_part = part['sudoku']
    #             if isinstance(sudoku_part, list):
    #                 combined_solution.extend(sudoku_part)
    #             elif isinstance(sudoku_part, dict) and 'sudoku' in sudoku_part:
    #                 combined_solution.extend(sudoku_part['sudoku'])

    #     print("combined_solution: ",combined_solution)
    #     return {'sudoku': combined_solution}


    # def solve_distributed(self, sudoku, address, req_id):
    #     num_nodes = len(self.connections) + 1
    #     partitioned_sudokus = self.partition_sudoku(sudoku, num_nodes)
    #     solved_parts = []
    #     for sud_part in partitioned_sudokus:
    #         solved_part = self.solveSudoku(sud_part, address, req_id)
    #         solved_parts.append(solved_part)
    #     return solved_parts 

    # def solveSudoku(self, sudokuSent, address, req_id):
    #     self.logger.info(f"Solving sudoku {sudokuSent}")
    #     sud = Sudoku(sudokuSent["sudoku"])
    #     solved,num = sud.solve_sudoku(sudokuSent["sudoku"])
    #     self.validations += num
    #     self.logger.info(f"Sudoku solved: {solved}")
    #     return {"sudoku": solved}