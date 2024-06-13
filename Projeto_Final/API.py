import json
from http.server import BaseHTTPRequestHandler

class api(BaseHTTPRequestHandler):

    def __init__(self, p2p, *args, **kwargs):
        self.p2p = p2p
        super().__init__(*args, **kwargs)

    def do_GET(self):
        print("Handling GET request")
        if self.path.startswith('/stats'):
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(self.p2p.stats()).encode('utf-8'))
        elif self.path.startswith('/network'):
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(self.p2p.network()).encode('utf-8'))
        else:
            self.send_error(404, 'Not Found')

    def do_POST(self):
        if self.path.startswith('/solve'):
            content_length = int(self.headers['Content-Length'])
            post_data = json.loads(self.rfile.read(content_length))
            sudoku,duration = self.p2p.solve_api(post_data)
            self.p2p.num_solve_counter()
            # Handle post_data as needed
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response_data = {'sudoku': sudoku, 'time': duration}
            self.wfile.write(json.dumps(response_data).encode('utf-8'))

        else:
            self.send_error(404, 'Not Found')
        