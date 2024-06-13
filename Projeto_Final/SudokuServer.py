import threading
from http.server import HTTPServer
import argparse
from API import api
from P2PServer import P2PServer
from log import get_logger

HOST = "0.0.0.0"

class Node(threading.Thread):

    def __init__(self, host, httpPort, p2pPort, p2pJoin, handicap):
        threading.Thread.__init__(self)
        self.host = host
        self.httpPort = httpPort
        self.p2pPort = p2pPort
        self.p2pJoin = p2pJoin
        self.handicap = handicap
        self.logger = get_logger("Node start")

    def run(self):
        p2pNode = P2PServer((self.host, self.p2pPort), self.p2pJoin, self.handicap)
        http_server = HTTPServer((self.host, self.httpPort), lambda *args, **kwargs: api(p2pNode, *args, **kwargs))

        p2p_thread = threading.Thread(target=p2pNode.start)
        p2p_thread.start()
        self.logger.info(f"P2P Server running on port {self.p2pPort}")
        
        http_thread = threading.Thread(target=http_server.serve_forever)
        http_thread.start()
        self.logger.info(f"HTTP Server running on {self.host}:{self.httpPort}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--httpPort", help="Porto HTTP do nó", type=int, default=8007)
    parser.add_argument("-s", "--p2pPort", help="Porto do protocolo P2P do nó", type=int, default=5007)
    parser.add_argument("-a", "--ancoragem", help="Endereço e porto do nó da rede P2P a que se pretende juntar", nargs=2, default=None)
    parser.add_argument("-hd", "--handicap", help="Handicap/atraso para a função de validação em milisegundos", type=int, default=1)

    args = parser.parse_args()

    if args.ancoragem is not None:
        n = Node(HOST, args.httpPort, args.p2pPort, (args.ancoragem[0], int(args.ancoragem[1])), args.handicap)
    else:
        n = Node(HOST, args.httpPort, args.p2pPort, None, args.handicap)
    n.start()
